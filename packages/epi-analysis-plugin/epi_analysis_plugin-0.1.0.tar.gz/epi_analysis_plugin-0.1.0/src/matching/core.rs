use std::collections::HashSet;

use polars::prelude::*;
use rand::seq::SliceRandom;

use crate::config::MatchingConfig;
use crate::matching::utils::are_parent_birth_dates_compatible;
use crate::types::ControlRecord;

/// Find controls eligible for matching with a case
pub fn find_eligible_controls(
    controls: &[ControlRecord],
    case_birth_day: i32,
    case_mother_birth_day: Option<i32>,
    case_father_birth_day: Option<i32>,
    used_indices: &HashSet<usize>,
    config: &MatchingConfig,
) -> Vec<usize> {
    let mut eligible = Vec::new();

    // Find birth day range using binary search
    let min_birth_day = case_birth_day - config.birth_date_window_days;
    let max_birth_day = case_birth_day + config.birth_date_window_days;

    // Binary search for start of range
    let start_idx = controls.partition_point(|c| c.birth_day < min_birth_day);

    // Check controls in the birth day window
    for (idx, control) in controls[start_idx..].iter().enumerate() {
        let actual_idx = start_idx + idx;

        // Stop if we're past the window
        if control.birth_day > max_birth_day {
            break;
        }

        // Skip if already used
        if used_indices.contains(&actual_idx) {
            continue;
        }

        // Check parent birth date compatibility if enabled
        if config.match_parent_birth_dates
            && !are_parent_birth_dates_compatible(
                case_mother_birth_day,
                case_father_birth_day,
                control.mother_birth_day,
                control.father_birth_day,
                config,
            )
        {
            continue;
        }

        eligible.push(actual_idx);
    }

    eligible
}

/// Build control pool from input series with optimized structure
pub fn build_control_pool(
    control_pnrs: &StringChunked,
    control_birth_dates: &DateChunked,
    control_mother_birth_dates: Option<&DateChunked>,
    control_father_birth_dates: Option<&DateChunked>,
) -> Vec<ControlRecord> {
    let mut controls = Vec::new();

    for i in 0..control_pnrs.len() {
        // Use get() which returns None for null values
        if let (Some(pnr), Some(birth_date)) =
            (control_pnrs.get(i), control_birth_dates.phys.get(i))
        {
            let birth_day = birth_date;
            let mother_birth_day = control_mother_birth_dates.and_then(|ca| ca.phys.get(i));
            let father_birth_day = control_father_birth_dates.and_then(|ca| ca.phys.get(i));

            controls.push(ControlRecord {
                pnr: pnr.to_string(),
                birth_day,
                mother_birth_day,
                father_birth_day,
            });
        }
    }

    // Sort controls by birth day for efficient searching
    controls.sort_by_key(|c| c.birth_day);
    controls
}

/// Select random controls from eligible pool
pub fn select_random_controls(
    controls: &[ControlRecord],
    eligible_controls: &[usize],
    matching_ratio: usize,
    used_control_indices: &mut HashSet<usize>,
) -> Vec<String> {
    let num_to_select = std::cmp::min(matching_ratio, eligible_controls.len());
    let mut selected_controls = Vec::with_capacity(num_to_select);

    if num_to_select > 0 {
        let mut rng = rand::thread_rng();
        let mut indices: Vec<usize> = (0..eligible_controls.len()).collect();
        indices.shuffle(&mut rng);

        for i in 0..num_to_select {
            let control_idx = eligible_controls[indices[i]];
            selected_controls.push(controls[control_idx].pnr.clone());
            used_control_indices.insert(control_idx);
        }
    }

    selected_controls
}
