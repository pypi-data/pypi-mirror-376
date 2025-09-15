use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use std::sync::Arc;

use polars::prelude::*;
use rayon::prelude::*;

use crate::config::WorkflowConfig;
use crate::matching::shared::{build_result_dataframe, process_vital_events};
use crate::matching::utils::{are_parent_birth_dates_compatible, is_at_risk_at_time};

/// Risk-set sampling with deterministic k-round algorithm for reproducible, conflict-free parallel processing
/// Implements OPTIMIZATION.md recommendations: bitset, sorted arrays, deterministic claiming
pub fn match_cases_partitioned_parallel(
    mfr_lpr_df: &DataFrame,
    vital_events_df: Option<&DataFrame>,
    config: &WorkflowConfig,
) -> PolarsResult<DataFrame> {
    println!("Starting DETERMINISTIC k-round risk-set sampling with advanced optimizations...");

    // Step 1: Process vital events data
    let vital_events_map = process_vital_events(vital_events_df)?;

    // Step 2: Build optimized risk set with struct-of-arrays layout
    let risk_set = build_optimized_risk_set(mfr_lpr_df, &vital_events_map)?;
    println!("Risk set size: {} individuals", risk_set.len());

    // Step 3: Extract and sort cases chronologically with temporal validity checks (CRITICAL: maintains temporal integrity)
    let cases = extract_and_sort_cases(&risk_set, config);
    if cases.is_empty() {
        polars_bail!(ComputeError: "No SCD cases with diagnosis dates found");
    }

    println!(
        "Processing {} cases with ultra-optimized algorithm",
        cases.len()
    );

    // Step 4: Create optimized birth date index with sorted arrays
    let birth_index = BirthDateIndex::new(&risk_set);

    // Step 5: Perform deterministic k-round parallel matching
    let matched_results =
        perform_deterministic_k_round_matching(&risk_set, &cases, &birth_index, config);

    // Step 6: Build result DataFrame
    build_result_dataframe(mfr_lpr_df, matched_results)
}

/// Optimized struct-of-arrays data structure for risk set
/// Improves cache locality by storing each attribute in contiguous arrays
#[derive(Debug)]
struct OptimizedRiskSet {
    /// PNR strings
    pnrs: Vec<String>,

    /// Birth days as i32 for fast comparison
    birth_days: Vec<i32>,

    /// Parent birth days (separate arrays for better cache locality)
    mother_birth_days: Vec<Option<i32>>,
    father_birth_days: Vec<Option<i32>>,

    /// Parity values
    parities: Vec<Option<i64>>,

    /// Birth type values
    birth_types: Vec<Option<String>>,

    /// SCD status strings
    scd_statuses: Vec<String>,

    /// SCD diagnosis dates
    scd_dates: Vec<Option<i32>>,

    /// Vital event dates (death/emigration for children and parents)
    child_death_dates: Vec<Option<i32>>,
    child_emigration_dates: Vec<Option<i32>>,
    mother_death_dates: Vec<Option<i32>>,
    mother_emigration_dates: Vec<Option<i32>>,
    father_death_dates: Vec<Option<i32>>,
    father_emigration_dates: Vec<Option<i32>>,
}

impl OptimizedRiskSet {
    const fn len(&self) -> usize {
        self.pnrs.len()
    }
}

/// High-performance bitset for tracking used controls with chunked atomic operations
/// Memory efficient: ~175KB for 1.4M controls vs 11MB for Vec<AtomicBool>
#[derive(Debug)]
struct UsedBitset {
    /// Chunked storage: each `AtomicU64` handles 64 control flags
    words: Box<[AtomicU64]>,
}

impl UsedBitset {
    fn new(num_controls: usize) -> Self {
        let num_words = num_controls.div_ceil(64);
        let words: Box<[AtomicU64]> = (0..num_words).map(|_| AtomicU64::new(0)).collect();

        Self { words }
    }

    /// Atomically try to mark a control as used (returns true if successful)
    #[inline]
    fn try_mark_used(&self, idx: usize) -> bool {
        let word_idx = idx / 64;
        let mask = 1u64 << (idx & 63);
        let word = &self.words[word_idx];

        loop {
            let current = word.load(Ordering::Relaxed);
            if current & mask != 0 {
                return false; // Already used
            }
            if word
                .compare_exchange_weak(current, current | mask, Ordering::AcqRel, Ordering::Relaxed)
                .is_ok()
            {
                return true; // Successfully marked as used
            }
            // Retry if CAS failed due to concurrent modification
        }
    }

    /// Check if a control is already used (non-atomic read for filtering)
    #[inline]
    fn is_used(&self, idx: usize) -> bool {
        let word_idx = idx / 64;
        let mask = 1u64 << (idx & 63);
        (self.words[word_idx].load(Ordering::Relaxed) & mask) != 0
    }
}

/// Round-based claiming system for deterministic conflict resolution
/// Each control can be claimed by exactly one case per round, with earliest case winning
#[derive(Debug)]
struct RoundClaims {
    /// One atomic claim slot per control; `NO_CLAIM` means unclaimed
    claimant: Box<[AtomicU32]>,
}

const NO_CLAIM: u32 = u32::MAX;

impl RoundClaims {
    fn new(num_controls: usize) -> Self {
        let claimant: Box<[AtomicU32]> = (0..num_controls)
            .map(|_| AtomicU32::new(NO_CLAIM))
            .collect();

        Self { claimant }
    }

    /// Propose a claim for a control (deterministic: lower `case_id` wins)
    #[inline]
    fn propose_claim(&self, control_idx: usize, case_id: u32) {
        let cell = &self.claimant[control_idx];
        // fetch_min ensures deterministic resolution: earliest case_id wins
        let _ = cell.fetch_min(case_id, Ordering::AcqRel);
    }

    /// Get the winning claimant for a control (`NO_CLAIM` if unclaimed)
    #[inline]
    fn get_claimant(&self, control_idx: usize) -> u32 {
        self.claimant[control_idx].load(Ordering::Acquire)
    }

    /// Reset all claims for next round (parallel clear)
    fn reset_for_next_round(&self) {
        self.claimant.par_iter().for_each(|cell| {
            cell.store(NO_CLAIM, Ordering::Release);
        });
    }
}

/// Birth date sorted index for O(log n) window lookups
/// Replaces `BTreeMap` with cache-friendly sorted arrays + binary search
#[derive(Debug)]
struct BirthDateIndex {
    /// Control indices sorted by `birth_date`
    sorted_indices: Box<[u32]>,
    /// Birth dates in same order as `sorted_indices` (for binary search)
    sorted_birth_dates: Box<[i32]>,
}

impl BirthDateIndex {
    fn new(risk_set: &OptimizedRiskSet) -> Self {
        // Create (birth_date, index) pairs for all potential controls
        let mut birth_index_pairs: Vec<(i32, u32)> = Vec::new();

        for i in 0..risk_set.len() {
            if risk_set.scd_statuses[i] != "SCD" {
                birth_index_pairs.push((risk_set.birth_days[i], i as u32));
            }
        }

        // Sort by birth date for binary search
        birth_index_pairs.sort_unstable_by_key(|&(birth_date, _)| birth_date);

        let sorted_indices: Box<[u32]> = birth_index_pairs.iter().map(|&(_, idx)| idx).collect();
        let sorted_birth_dates: Box<[i32]> = birth_index_pairs
            .iter()
            .map(|&(birth_date, _)| birth_date)
            .collect();

        println!(
            "Built birth date index with {} potential controls",
            sorted_indices.len()
        );

        Self {
            sorted_indices,
            sorted_birth_dates,
        }
    }

    /// Find controls within birth date window using binary search O(log n)
    fn find_controls_in_window(&self, case_birth_date: i32, window_days: i32) -> &[u32] {
        let min_birth = case_birth_date - window_days;
        let max_birth = case_birth_date + window_days;

        // Binary search for start and end of window
        let start_idx = self
            .sorted_birth_dates
            .partition_point(|&date| date < min_birth);
        let end_idx = self
            .sorted_birth_dates
            .partition_point(|&date| date <= max_birth);

        &self.sorted_indices[start_idx..end_idx]
    }
}

/// Case information with stable ordering for deterministic results
#[derive(Debug, Clone)]
struct CaseInfo {
    risk_set_idx: usize,
    stable_case_id: u32, // For deterministic conflict resolution
    diagnosis_date: i32,
}

#[allow(clippy::too_many_lines)]
fn build_optimized_risk_set(
    all_individuals: &DataFrame,
    vital_events_map: &rustc_hash::FxHashMap<String, i32>,
) -> PolarsResult<OptimizedRiskSet> {
    let num_rows = all_individuals.height();

    // Pre-allocate all vectors with known capacity
    let mut pnrs = Vec::with_capacity(num_rows);
    let mut birth_days = Vec::with_capacity(num_rows);
    let mut mother_birth_days = Vec::with_capacity(num_rows);
    let mut father_birth_days = Vec::with_capacity(num_rows);
    let mut parities = Vec::with_capacity(num_rows);
    let mut birth_types = Vec::with_capacity(num_rows);
    let mut scd_statuses = Vec::with_capacity(num_rows);
    let mut scd_dates = Vec::with_capacity(num_rows);
    let mut child_death_dates = Vec::with_capacity(num_rows);
    let mut child_emigration_dates = Vec::with_capacity(num_rows);
    let mut mother_death_dates = Vec::with_capacity(num_rows);
    let mut mother_emigration_dates = Vec::with_capacity(num_rows);
    let mut father_death_dates = Vec::with_capacity(num_rows);
    let mut father_emigration_dates = Vec::with_capacity(num_rows);

    // Extract columns once
    let pnrs_col = all_individuals.column("PNR")?.str()?;
    let birth_dates_col = all_individuals.column("FOEDSELSDATO")?.date()?;
    let scd_statuses_col = all_individuals.column("SCD_STATUS")?.str()?;
    let scd_dates_col = all_individuals.column("SCD_DATE")?.date()?;

    // Optional parent columns
    let mother_dates_col = all_individuals
        .column("MODER_FOEDSELSDATO")
        .ok()
        .map(|s| s.date())
        .transpose()?;
    let father_dates_col = all_individuals
        .column("FADER_FOEDSELSDATO")
        .ok()
        .map(|s| s.date())
        .transpose()?;
    let mother_pnrs_col = all_individuals
        .column("CPR_MODER")
        .ok()
        .map(|s| s.str())
        .transpose()?;
    let father_pnrs_col = all_individuals
        .column("CPR_FADER")
        .ok()
        .map(|s| s.str())
        .transpose()?;
    let parity_col = all_individuals
        .column("PARITET")
        .ok()
        .map(|s| s.i64())
        .transpose()?;
    let birth_type_col = all_individuals
        .column("birth_type")
        .ok()
        .map(|s| s.str())
        .transpose()?;

    // Process all rows in a single loop
    for i in 0..num_rows {
        if let (Some(pnr), Some(birth_date), Some(scd_status)) = (
            pnrs_col.get(i),
            birth_dates_col.phys.get(i),
            scd_statuses_col.get(i),
        ) {
            let scd_date_days = scd_dates_col.phys.get(i);
            let mother_birth_day = mother_dates_col.as_ref().and_then(|ca| ca.phys.get(i));
            let father_birth_day = father_dates_col.as_ref().and_then(|ca| ca.phys.get(i));
            let parity = parity_col.as_ref().and_then(|ca| ca.get(i));
            let birth_type = birth_type_col
                .as_ref()
                .and_then(|ca| ca.get(i))
                .map(|s| s.to_string());

            // Look up vital events
            let death_date = vital_events_map.get(&format!("{pnr}:DEATH:CHILD")).copied();
            let emigration_date = vital_events_map
                .get(&format!("{pnr}:EMIGRATION:CHILD"))
                .copied();

            // Get parent PNRs for vital event lookup
            let mother_pnr = mother_pnrs_col.as_ref().and_then(|ca| ca.get(i));
            let father_pnr = father_pnrs_col.as_ref().and_then(|ca| ca.get(i));

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

            // Push to all arrays (struct-of-arrays layout)
            pnrs.push(pnr.to_string());
            birth_days.push(birth_date);
            mother_birth_days.push(mother_birth_day);
            father_birth_days.push(father_birth_day);
            parities.push(parity);
            birth_types.push(birth_type);
            scd_statuses.push(scd_status.to_string());
            scd_dates.push(scd_date_days);
            child_death_dates.push(death_date);
            child_emigration_dates.push(emigration_date);
            mother_death_dates.push(mother_death_date);
            mother_emigration_dates.push(mother_emigration_date);
            father_death_dates.push(father_death_date);
            father_emigration_dates.push(father_emigration_date);
        }
    }

    Ok(OptimizedRiskSet {
        pnrs,
        birth_days,
        mother_birth_days,
        father_birth_days,
        parities,
        birth_types,
        scd_statuses,
        scd_dates,
        child_death_dates,
        child_emigration_dates,
        mother_death_dates,
        mother_emigration_dates,
        father_death_dates,
        father_emigration_dates,
    })
}

/// Extract and sort cases with stable case IDs for deterministic results
fn extract_and_sort_cases(risk_set: &OptimizedRiskSet, config: &WorkflowConfig) -> Vec<CaseInfo> {
    let mut cases = Vec::new();

    // Find all SCD cases with diagnosis dates and temporal validity
    for i in 0..risk_set.len() {
        // Basic case criteria
        if risk_set.scd_statuses[i] != "SCD" || risk_set.scd_dates[i].is_none() {
            continue;
        }

        let diagnosis_date = risk_set.scd_dates[i].unwrap();

        // Check if case child is alive and present at diagnosis time
        if !is_at_risk_at_time(
            diagnosis_date,
            risk_set.child_death_dates[i],
            risk_set.child_emigration_dates[i],
        ) {
            continue;
        }

        // Check if case parents are alive and present at diagnosis time (if parent matching enabled)
        if config.matching.match_parent_birth_dates {
            let mother_at_risk = risk_set.mother_birth_days[i].is_none()
                || is_at_risk_at_time(
                    diagnosis_date,
                    risk_set.mother_death_dates[i],
                    risk_set.mother_emigration_dates[i],
                );

            let father_at_risk = risk_set.father_birth_days[i].is_none()
                || is_at_risk_at_time(
                    diagnosis_date,
                    risk_set.father_death_dates[i],
                    risk_set.father_emigration_dates[i],
                );

            if config.matching.require_both_parents && (!mother_at_risk || !father_at_risk) {
                continue;
            }

            // If not requiring both parents but one is available, at least one must be at risk
            if (risk_set.mother_birth_days[i].is_some() || risk_set.father_birth_days[i].is_some())
                && !mother_at_risk
                && !father_at_risk
            {
                continue;
            }
        }

        cases.push(CaseInfo {
            risk_set_idx: i,
            stable_case_id: i as u32, // Use index as stable ID for now
            diagnosis_date,
        });
    }

    // CRITICAL: Sort by diagnosis date, then by stable ID for deterministic order
    cases.sort_by_key(|c| (c.diagnosis_date, c.stable_case_id));

    cases
}

/// Main deterministic k-round matching algorithm
/// Implements 2-phase approach: parallel candidate discovery + deterministic claiming
fn perform_deterministic_k_round_matching(
    risk_set: &OptimizedRiskSet,
    cases: &[CaseInfo],
    birth_index: &BirthDateIndex,
    config: &WorkflowConfig,
) -> Vec<(String, Vec<String>)> {
    if cases.is_empty() {
        return Vec::new();
    }

    println!(
        "Starting deterministic k-round matching for {} cases...",
        cases.len()
    );

    // Initialize shared data structures
    let used_bitset = Arc::new(UsedBitset::new(risk_set.len()));
    let round_claims = Arc::new(RoundClaims::new(risk_set.len()));

    // Target: 4 controls per case (matching spatial_index results)
    let k_target = config.matching.matching_ratio as u8;

    // Create chronological case batches for parallel processing
    let case_batches = create_case_batches(cases, 30); // 30-day batches
    println!(
        "Created {} case batches for parallel processing",
        case_batches.len()
    );

    // Track assignments per case
    let mut case_assignments: Vec<Vec<u32>> = vec![Vec::new(); cases.len()];
    let mut assigned_counts: Vec<u8> = vec![0; cases.len()];

    // Process batches sequentially to maintain chronological integrity
    for batch in case_batches {
        println!("Processing batch with {} cases...", batch.len());

        // Phase A: Parallel candidate discovery
        let per_case_candidates =
            discover_candidates_parallel(risk_set, cases, &batch, birth_index, config);

        // Phase B: k rounds of deterministic claiming
        for round in 0..k_target {
            // Propose phase (parallel)
            propose_claims_parallel(
                cases,
                &batch,
                &per_case_candidates,
                &assigned_counts,
                &used_bitset,
                &round_claims,
                round,
                k_target,
            );

            // Commit phase (deterministic resolution)
            commit_winners_parallel(
                risk_set,
                cases,
                &batch,
                &used_bitset,
                &round_claims,
                &mut case_assignments,
                &mut assigned_counts,
            );

            // Reset claims for next round
            round_claims.reset_for_next_round();

            // Early termination if all cases in batch are satisfied
            let all_satisfied = batch
                .iter()
                .all(|&case_idx| assigned_counts[case_idx] >= k_target);
            if all_satisfied {
                println!("All cases in batch satisfied after round {}", round + 1);
                break;
            }
        }
    }

    // Build final results
    build_final_results(risk_set, cases, &case_assignments)
}

/// Create chronological case batches
fn create_case_batches(cases: &[CaseInfo], batch_window_days: i32) -> Vec<Vec<usize>> {
    if cases.is_empty() {
        return Vec::new();
    }

    let mut batches = Vec::new();
    let mut current_batch = Vec::new();
    let mut batch_start_date = cases[0].diagnosis_date;

    for (idx, case) in cases.iter().enumerate() {
        if case.diagnosis_date - batch_start_date > batch_window_days {
            // Start new batch
            batches.push(std::mem::take(&mut current_batch));
            batch_start_date = case.diagnosis_date;
        }
        current_batch.push(idx);
    }

    // Add final batch
    if !current_batch.is_empty() {
        batches.push(current_batch);
    }

    batches
}

/// Phase A: Parallel candidate discovery with deterministic ordering
fn discover_candidates_parallel(
    risk_set: &OptimizedRiskSet,
    cases: &[CaseInfo],
    batch: &[usize],
    birth_index: &BirthDateIndex,
    config: &WorkflowConfig,
) -> Vec<Vec<u32>> {
    // Parallel discovery per case
    batch
        .par_iter()
        .map(|&case_idx| {
            let case = &cases[case_idx];
            let case_info = &risk_set;

            // Step 1: Birth date window lookup (O(log n))
            let birth_window_candidates = birth_index.find_controls_in_window(
                case_info.birth_days[case.risk_set_idx],
                config.matching.birth_date_window_days,
            );

            // Step 2: Filter for eligibility
            let mut eligible_candidates = Vec::new();
            for &control_idx in birth_window_candidates {
                if is_control_eligible_for_case(
                    risk_set,
                    case.risk_set_idx,
                    control_idx as usize,
                    case.diagnosis_date,
                    config,
                ) {
                    eligible_candidates.push(control_idx);
                }
            }

            // Step 3: Deterministic stable ordering
            eligible_candidates.sort_by_key(|&control_idx| {
                let birth_distance = (case_info.birth_days[case.risk_set_idx]
                    - case_info.birth_days[control_idx as usize])
                    .abs();
                (birth_distance, control_idx) // Stable tie-breaking by control_idx
            });

            eligible_candidates
        })
        .collect()
}

/// Phase B.1: Propose claims in parallel
fn propose_claims_parallel(
    cases: &[CaseInfo],
    batch: &[usize],
    per_case_candidates: &[Vec<u32>],
    assigned_counts: &[u8],
    used_bitset: &Arc<UsedBitset>,
    round_claims: &Arc<RoundClaims>,
    round: u8,
    k_target: u8,
) {
    batch
        .par_iter()
        .enumerate()
        .for_each(|(batch_idx, &case_idx)| {
            if assigned_counts[case_idx] >= k_target {
                return; // Case already satisfied
            }

            let case = &cases[case_idx];
            let candidates = &per_case_candidates[batch_idx];

            // Find next unused candidate for this round
            if let Some(&control_idx) = candidates
                .iter()
                .skip(round as usize) // Skip candidates used in previous rounds
                .find(|&&idx| !used_bitset.is_used(idx as usize))
            {
                // Propose claim for this control
                round_claims.propose_claim(control_idx as usize, case.stable_case_id);
            }
        });
}

/// Phase B.2: Commit winners with deterministic resolution
fn commit_winners_parallel(
    risk_set: &OptimizedRiskSet,
    cases: &[CaseInfo],
    batch: &[usize],
    used_bitset: &Arc<UsedBitset>,
    round_claims: &Arc<RoundClaims>,
    case_assignments: &mut [Vec<u32>],
    assigned_counts: &mut [u8],
) {
    // Parallel commit for all controls
    (0..risk_set.len()).into_par_iter().for_each(|control_idx| {
        let winning_case_id = round_claims.get_claimant(control_idx);
        if winning_case_id != NO_CLAIM {
            // Try to atomically mark as used
            if used_bitset.try_mark_used(control_idx) {
                // Find the winning case index
                if let Some(&_case_idx) = batch
                    .iter()
                    .find(|&&idx| cases[idx].stable_case_id == winning_case_id)
                {
                    // This is unsafe in parallel context - need synchronization
                    // For now, we'll handle this in a sequential phase
                }
            }
        }
    });

    // Sequential phase to update assignments (to avoid data races)
    for control_idx in 0..risk_set.len() {
        let winning_case_id = round_claims.get_claimant(control_idx);
        if winning_case_id != NO_CLAIM && used_bitset.is_used(control_idx) {
            if let Some(&case_idx) = batch
                .iter()
                .find(|&&idx| cases[idx].stable_case_id == winning_case_id)
            {
                case_assignments[case_idx].push(control_idx as u32);
                assigned_counts[case_idx] += 1;
            }
        }
    }
}

/// Check if a control is eligible for a specific case
fn is_control_eligible_for_case(
    risk_set: &OptimizedRiskSet,
    case_idx: usize,
    control_idx: usize,
    case_diagnosis_date: i32,
    config: &WorkflowConfig,
) -> bool {
    // Skip the case itself
    if case_idx == control_idx {
        return false;
    }

    // Check SCD status eligibility
    let is_eligible_at_time = match risk_set.scd_statuses[control_idx].as_str() {
        "NO_SCD" => true,
        "SCD" | "SCD_LATE" => risk_set.scd_dates[control_idx]
            .is_some_and(|control_diag_date| control_diag_date > case_diagnosis_date),
        _ => false,
    };

    if !is_eligible_at_time {
        return false;
    }

    // Check temporal validity (child)
    if !is_at_risk_at_time(
        case_diagnosis_date,
        risk_set.child_death_dates[control_idx],
        risk_set.child_emigration_dates[control_idx],
    ) {
        return false;
    }

    // Check parent compatibility if enabled
    if config.matching.match_parent_birth_dates {
        // Parent temporal validity
        let mother_at_risk = risk_set.mother_birth_days[control_idx].is_none()
            || is_at_risk_at_time(
                case_diagnosis_date,
                risk_set.mother_death_dates[control_idx],
                risk_set.mother_emigration_dates[control_idx],
            );

        let father_at_risk = risk_set.father_birth_days[control_idx].is_none()
            || is_at_risk_at_time(
                case_diagnosis_date,
                risk_set.father_death_dates[control_idx],
                risk_set.father_emigration_dates[control_idx],
            );

        if config.matching.require_both_parents && (!mother_at_risk || !father_at_risk) {
            return false;
        }

        // Parent birth date compatibility
        if !are_parent_birth_dates_compatible(
            risk_set.mother_birth_days[case_idx],
            risk_set.father_birth_days[case_idx],
            risk_set.mother_birth_days[control_idx],
            risk_set.father_birth_days[control_idx],
            &config.matching,
        ) {
            return false;
        }
    }

    // Check parity matching
    if config.matching.match_parity && risk_set.parities[case_idx] != risk_set.parities[control_idx]
    {
        return false;
    }

    // Check birth type matching
    if config.matching.match_birth_type
        && risk_set.birth_types[case_idx] != risk_set.birth_types[control_idx]
    {
        return false;
    }

    true
}

/// Build final results from assignments
fn build_final_results(
    risk_set: &OptimizedRiskSet,
    cases: &[CaseInfo],
    case_assignments: &[Vec<u32>],
) -> Vec<(String, Vec<String>)> {
    let mut results = Vec::new();
    let mut total_controls = 0;

    for (case_idx, case) in cases.iter().enumerate() {
        let case_pnr = risk_set.pnrs[case.risk_set_idx].clone();
        let control_pnrs: Vec<String> = case_assignments[case_idx]
            .iter()
            .map(|&control_idx| risk_set.pnrs[control_idx as usize].clone())
            .collect();

        total_controls += control_pnrs.len();
        results.push((case_pnr, control_pnrs));
    }

    let avg_controls = if cases.is_empty() {
        0.0
    } else {
        total_controls as f64 / cases.len() as f64
    };
    println!(
        "Deterministic matching complete: {} cases, {} controls, {:.1} controls/case",
        cases.len(),
        total_controls,
        avg_controls
    );

    results
}
