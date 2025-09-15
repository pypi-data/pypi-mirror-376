use std::collections::{BTreeMap, HashSet};
use std::sync::{Arc, Mutex};

use polars::prelude::*;
use rand::seq::SliceRandom;
use rayon::prelude::*;

use crate::config::WorkflowConfig;
use crate::matching::shared::{build_result_dataframe, process_vital_events};
use crate::matching::utils::{are_parent_birth_dates_compatible, is_at_risk_at_time};
use crate::types::RiskSetRecord;

/// Risk-set sampling with spatial indexing for faster control lookup
/// Maintains statistical integrity while significantly improving performance
pub fn match_cases_spatial_index(
    mfr_lpr_df: &DataFrame,
    vital_events_df: Option<&DataFrame>,
    config: &WorkflowConfig,
) -> PolarsResult<DataFrame> {
    println!("Starting OPTIMIZED risk-set sampling with parallel processing...");

    // Step 1: Process vital events data
    let vital_events_map = process_vital_events(vital_events_df)?;

    // Step 2: Build risk set records
    let risk_set = build_risk_set(mfr_lpr_df, &vital_events_map)?;
    println!("Risk set size: {} individuals", risk_set.len());

    // Step 3: Extract cases with temporal validity checks and sort chronologically
    let mut cases: Vec<&RiskSetRecord> = risk_set
        .iter()
        .filter(|r| {
            // Basic case criteria
            if r.scd_status != "SCD" || r.scd_date.is_none() {
                return false;
            }

            let diagnosis_date = r.scd_date.unwrap();

            // Check if case child is alive and present at diagnosis time
            if !is_at_risk_at_time(diagnosis_date, r.death_date, r.emigration_date) {
                return false;
            }

            // Check if case parents are alive and present at diagnosis time (if parent matching enabled)
            if config.matching.match_parent_birth_dates {
                let mother_at_risk = r.mother_birth_day.is_none()
                    || is_at_risk_at_time(
                        diagnosis_date,
                        r.mother_death_date,
                        r.mother_emigration_date,
                    );

                let father_at_risk = r.father_birth_day.is_none()
                    || is_at_risk_at_time(
                        diagnosis_date,
                        r.father_death_date,
                        r.father_emigration_date,
                    );

                if config.matching.require_both_parents && (!mother_at_risk || !father_at_risk) {
                    return false;
                }

                // If not requiring both parents but one is available, at least one must be at risk
                if (r.mother_birth_day.is_some() || r.father_birth_day.is_some())
                    && !mother_at_risk
                    && !father_at_risk
                {
                    return false;
                }
            }

            true
        })
        .collect();

    if cases.is_empty() {
        polars_bail!(ComputeError: "No SCD cases with diagnosis dates found");
    }

    cases.sort_by_key(|c| c.scd_date.unwrap());
    println!(
        "Processing {} cases with optimized parallel algorithm",
        cases.len()
    );

    // Step 4: Create spatial index for faster control lookup
    let control_index = build_spatial_index(&risk_set);

    // Step 5: Perform optimized parallel matching
    let matched_results = perform_optimized_matching(&risk_set, &cases, &control_index, config)?;

    // Step 6: Build result DataFrame
    build_result_dataframe(mfr_lpr_df, matched_results)
}

/// Spatial index for faster control lookups based on birth dates
#[derive(Debug)]
struct SpatialIndex {
    /// `BTreeMap`: `birth_day` -> list of indices in `risk_set`
    birth_day_index: BTreeMap<i32, Vec<usize>>,
}

impl SpatialIndex {
    const fn new() -> Self {
        Self {
            birth_day_index: BTreeMap::new(),
        }
    }

    /// Find control indices within birth date window using O(log n) lookup
    fn find_controls_in_birth_window(
        &self,
        case_birth_day: i32,
        birth_date_window_days: i32,
    ) -> Vec<usize> {
        let min_birth_day = case_birth_day - birth_date_window_days;
        let max_birth_day = case_birth_day + birth_date_window_days;

        let mut candidates = Vec::new();

        // Use BTreeMap range query for O(log n) lookup
        for (_, indices) in self.birth_day_index.range(min_birth_day..=max_birth_day) {
            candidates.extend(indices);
        }

        candidates
    }
}

fn build_spatial_index(risk_set: &[RiskSetRecord]) -> SpatialIndex {
    let mut index = SpatialIndex::new();

    // Build birth day index
    for (idx, record) in risk_set.iter().enumerate() {
        index
            .birth_day_index
            .entry(record.birth_day)
            .or_default()
            .push(idx);
    }

    println!(
        "Built spatial index with {} birth day buckets",
        index.birth_day_index.len()
    );

    index
}

/// Batch cases by time windows for parallel processing while maintaining chronological integrity
fn create_case_batches(cases: &[&RiskSetRecord], batch_window_days: i32) -> Vec<Vec<usize>> {
    let mut batches = Vec::new();
    let mut current_batch = Vec::new();
    let mut batch_start_date = None;

    for (idx, case) in cases.iter().enumerate() {
        let case_date = case.scd_date.unwrap();

        match batch_start_date {
            None => {
                // First case in batch
                batch_start_date = Some(case_date);
            },
            Some(start_date) => {
                if case_date - start_date > batch_window_days {
                    // Start new batch
                    batches.push(std::mem::take(&mut current_batch));
                    batch_start_date = Some(case_date);
                }
            },
        }
        current_batch.push(idx);
    }

    // Add final batch
    if !current_batch.is_empty() {
        batches.push(current_batch);
    }

    println!(
        "Created {} case batches for parallel processing",
        batches.len()
    );
    batches
}

fn perform_optimized_matching(
    risk_set: &[RiskSetRecord],
    cases: &[&RiskSetRecord],
    spatial_index: &SpatialIndex,
    config: &WorkflowConfig,
) -> PolarsResult<Vec<(String, Vec<String>)>> {
    // Create case batches for parallel processing (30-day windows)
    let case_batches = create_case_batches(cases, 30);

    // Shared state for used controls (needs thread-safe access)
    let used_controls = Arc::new(Mutex::new(HashSet::<String>::new()));
    let matched_results = Arc::new(Mutex::new(Vec::new()));

    // Process batches in parallel
    case_batches.into_par_iter().for_each(|batch_indices| {
        let batch_results = process_case_batch(
            risk_set,
            cases,
            &batch_indices,
            spatial_index,
            config,
            &used_controls,
        );

        // Add batch results to global results
        if let Ok(batch_matches) = batch_results {
            let mut results_lock = matched_results.lock().unwrap();
            results_lock.extend(batch_matches);
        }
    });

    // Extract final results
    let final_results = Arc::try_unwrap(matched_results)
        .map_err(|_| polars_err!(ComputeError: "Failed to extract matching results"))?
        .into_inner()
        .map_err(|_| polars_err!(ComputeError: "Failed to unlock matching results"))?;

    // Sort results by case order to maintain deterministic output
    let mut sorted_results = final_results;
    sorted_results.sort_by_key(|(case_pnr, _)| {
        cases
            .iter()
            .position(|c| &c.pnr == case_pnr)
            .unwrap_or(usize::MAX)
    });

    println!(
        "Completed parallel matching for {} cases",
        sorted_results.len()
    );
    Ok(sorted_results)
}

fn process_case_batch(
    risk_set: &[RiskSetRecord],
    cases: &[&RiskSetRecord],
    batch_indices: &[usize],
    spatial_index: &SpatialIndex,
    config: &WorkflowConfig,
    global_used_controls: &Arc<Mutex<HashSet<String>>>,
) -> PolarsResult<Vec<(String, Vec<String>)>> {
    let mut batch_results = Vec::new();

    // Process cases in this batch sequentially (to maintain chronological order within batch)
    for &case_idx in batch_indices {
        let case = cases[case_idx];
        let case_diagnosis_date = case.scd_date.unwrap();

        // Find eligible controls using spatial index
        let candidate_indices = spatial_index
            .find_controls_in_birth_window(case.birth_day, config.matching.birth_date_window_days);

        // Filter candidates for eligibility at this time point
        let eligible_controls = filter_eligible_controls_optimized(
            risk_set,
            case,
            case_diagnosis_date,
            &candidate_indices,
            config,
            global_used_controls,
        )?;

        // Select controls from eligible pool
        let selected_controls = select_controls_thread_safe(
            &eligible_controls,
            config.matching.matching_ratio,
            global_used_controls,
        )?;

        batch_results.push((case.pnr.clone(), selected_controls));
    }

    Ok(batch_results)
}

fn filter_eligible_controls_optimized<'a>(
    risk_set: &'a [RiskSetRecord],
    case: &RiskSetRecord,
    case_diagnosis_date: i32,
    candidate_indices: &[usize],
    config: &WorkflowConfig,
    used_controls: &Arc<Mutex<HashSet<String>>>,
) -> PolarsResult<Vec<&'a RiskSetRecord>> {
    let mut eligible_controls = Vec::new();
    let used_controls_snapshot = {
        let lock = used_controls
            .lock()
            .map_err(|_| polars_err!(ComputeError: "Failed to lock used controls"))?;
        lock.clone()
    };

    for &idx in candidate_indices {
        let potential_control = &risk_set[idx];

        // Quick eligibility checks first (most likely to fail)
        if potential_control.pnr == case.pnr
            || used_controls_snapshot.contains(&potential_control.pnr)
        {
            continue;
        }

        // Check SCD status eligibility
        let is_eligible_at_time = match potential_control.scd_status.as_str() {
            "NO_SCD" => true,
            "SCD" | "SCD_LATE" => potential_control
                .scd_date
                .is_some_and(|control_diag_date| control_diag_date > case_diagnosis_date),
            _ => false,
        };

        if !is_eligible_at_time {
            continue;
        }

        // Check temporal validity
        if !is_at_risk_at_time(
            case_diagnosis_date,
            potential_control.death_date,
            potential_control.emigration_date,
        ) {
            continue;
        }

        // Birth date window already checked by spatial index

        // Check parent compatibility (most expensive check)
        if config.matching.match_parent_birth_dates {
            // Parent temporal validity
            let mother_at_risk = potential_control.mother_birth_day.is_none()
                || is_at_risk_at_time(
                    case_diagnosis_date,
                    potential_control.mother_death_date,
                    potential_control.mother_emigration_date,
                );

            let father_at_risk = potential_control.father_birth_day.is_none()
                || is_at_risk_at_time(
                    case_diagnosis_date,
                    potential_control.father_death_date,
                    potential_control.father_emigration_date,
                );

            if config.matching.require_both_parents && (!mother_at_risk || !father_at_risk) {
                continue;
            }

            // Parent birth date compatibility
            if !are_parent_birth_dates_compatible(
                case.mother_birth_day,
                case.father_birth_day,
                potential_control.mother_birth_day,
                potential_control.father_birth_day,
                &config.matching,
            ) {
                continue;
            }
        }

        // Check parity matching
        if config.matching.match_parity && case.parity != potential_control.parity {
            continue;
        }

        // Check birth type matching
        if config.matching.match_birth_type && case.birth_type != potential_control.birth_type {
            continue;
        }

        eligible_controls.push(potential_control);
    }

    Ok(eligible_controls)
}

fn select_controls_thread_safe(
    eligible_controls: &[&RiskSetRecord],
    matching_ratio: usize,
    used_controls: &Arc<Mutex<HashSet<String>>>,
) -> PolarsResult<Vec<String>> {
    let num_to_select = std::cmp::min(matching_ratio, eligible_controls.len());
    let mut selected_controls = Vec::with_capacity(num_to_select);

    if num_to_select > 0 {
        let mut rng = rand::thread_rng();
        let mut indices: Vec<usize> = (0..eligible_controls.len()).collect();
        indices.shuffle(&mut rng);

        // Lock once and update used controls atomically
        let mut used_lock = used_controls
            .lock()
            .map_err(|_| polars_err!(ComputeError: "Failed to lock used controls for selection"))?;

        for i in 0..num_to_select {
            let control = eligible_controls[indices[i]];
            if !used_lock.contains(&control.pnr) {
                selected_controls.push(control.pnr.clone());
                used_lock.insert(control.pnr.clone());
            }
        }
    }

    Ok(selected_controls)
}

fn build_risk_set(
    all_individuals: &DataFrame,
    vital_events_map: &rustc_hash::FxHashMap<String, i32>,
) -> PolarsResult<Vec<RiskSetRecord>> {
    let mut risk_set = Vec::new();

    let pnrs = all_individuals.column("PNR")?.str()?;
    let birth_dates = all_individuals.column("FOEDSELSDATO")?.date()?;
    let scd_statuses = all_individuals.column("SCD_STATUS")?.str()?;
    let scd_dates = all_individuals.column("SCD_DATE")?.date()?;

    // Parent columns
    let mother_dates = all_individuals
        .column("MODER_FOEDSELSDATO")
        .ok()
        .map(|s| s.date())
        .transpose()?;
    let father_dates = all_individuals
        .column("FADER_FOEDSELSDATO")
        .ok()
        .map(|s| s.date())
        .transpose()?;
    let mother_pnrs = all_individuals
        .column("CPR_MODER")
        .ok()
        .map(|s| s.str())
        .transpose()?;
    let father_pnrs = all_individuals
        .column("CPR_FADER")
        .ok()
        .map(|s| s.str())
        .transpose()?;
    let parity_values = all_individuals
        .column("PARITET")
        .ok()
        .map(|s| s.i64())
        .transpose()?;
    let birth_type_values = all_individuals
        .column("birth_type")
        .ok()
        .map(|s| s.str())
        .transpose()?;

    for i in 0..pnrs.len() {
        if let (Some(pnr), Some(birth_date), Some(scd_status)) =
            (pnrs.get(i), birth_dates.phys.get(i), scd_statuses.get(i))
        {
            let scd_date_days = scd_dates.phys.get(i);
            let mother_birth_day = mother_dates.as_ref().and_then(|ca| ca.phys.get(i));
            let father_birth_day = father_dates.as_ref().and_then(|ca| ca.phys.get(i));
            let parity = parity_values.as_ref().and_then(|ca| ca.get(i));
            let birth_type = birth_type_values
                .as_ref()
                .and_then(|ca| ca.get(i))
                .map(|s| s.to_string());

            // Look up vital events for this individual and parents
            let death_date = vital_events_map.get(&format!("{pnr}:DEATH:CHILD")).copied();
            let emigration_date = vital_events_map
                .get(&format!("{pnr}:EMIGRATION:CHILD"))
                .copied();

            // Get parent PNRs for vital event lookup
            let mother_pnr = mother_pnrs.as_ref().and_then(|ca| ca.get(i));
            let father_pnr = father_pnrs.as_ref().and_then(|ca| ca.get(i));

            let mother_death_date = mother_pnr.and_then(|mpnr| {
                vital_events_map
                    .get(&format!("{mpnr}:DEATH:PARENT"))
                    .copied()
            });
            let mother_emigration_date = mother_pnr.and_then(|mpnr| {
                vital_events_map
                    .get(&format!("{mpnr}:EMIGRATION:PARENT"))
                    .copied()
            });
            let father_death_date = father_pnr.and_then(|fpnr| {
                vital_events_map
                    .get(&format!("{fpnr}:DEATH:PARENT"))
                    .copied()
            });
            let father_emigration_date = father_pnr.and_then(|fpnr| {
                vital_events_map
                    .get(&format!("{fpnr}:EMIGRATION:PARENT"))
                    .copied()
            });

            risk_set.push(RiskSetRecord {
                pnr: pnr.to_string(),
                birth_day: birth_date,
                mother_birth_day,
                father_birth_day,
                parity,
                birth_type,
                scd_status: scd_status.to_string(),
                scd_date: scd_date_days,
                death_date,
                emigration_date,
                mother_death_date,
                mother_emigration_date,
                father_death_date,
                father_emigration_date,
            });
        }
    }

    Ok(risk_set)
}
