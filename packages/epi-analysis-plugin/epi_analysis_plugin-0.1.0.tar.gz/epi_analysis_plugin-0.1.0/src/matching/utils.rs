use crate::config::MatchingConfig;

/// Check if parent birth dates are compatible between case and control
pub const fn are_parent_birth_dates_compatible(
    case_mother_birth_day: Option<i32>,
    case_father_birth_day: Option<i32>,
    control_mother_birth_day: Option<i32>,
    control_father_birth_day: Option<i32>,
    config: &MatchingConfig,
) -> bool {
    let window = config.parent_birth_date_window_days;

    // Check mother birth date compatibility
    let mother_compatible = match (case_mother_birth_day, control_mother_birth_day) {
        (Some(case_mother), Some(control_mother)) => (case_mother - control_mother).abs() <= window,
        (None, None) => true,                      // Both missing is compatible
        _ if config.require_both_parents => false, // One missing when both required
        _ => !config.match_mother_birth_date_only, // One missing is ok unless mother-only matching
    };

    if !mother_compatible {
        return false;
    }

    // If only matching mother birth dates, we're done
    if config.match_mother_birth_date_only {
        return mother_compatible;
    }

    // Check father birth date compatibility
    match (case_father_birth_day, control_father_birth_day) {
        (Some(case_father), Some(control_father)) => (case_father - control_father).abs() <= window,
        (None, None) => true,                      // Both missing is compatible
        _ if config.require_both_parents => false, // One missing when both required
        _ => true, // One missing is ok for fathers unless both parents required
    }
}

/// Check if an individual is "at risk" (alive and not emigrated) at a given time point
/// Returns true if the person is available for matching at the specified date
pub const fn is_at_risk_at_time(
    time_point: i32,
    death_date: Option<i32>,
    emigration_date: Option<i32>,
) -> bool {
    // Check if person died before this time point
    if let Some(death) = death_date {
        if death <= time_point {
            return false;
        }
    }

    // Check if person emigrated before this time point
    if let Some(emigration) = emigration_date {
        if emigration <= time_point {
            return false;
        }
    }

    true // Person is at risk if no censoring events occurred before time_point
}
