#![allow(clippy::unused_unit)]
use std::collections::HashSet;

use polars::prelude::*;
use pyo3_polars::derive::polars_expr;

use crate::config::MatchingConfig;
use crate::matching::core::{build_control_pool, find_eligible_controls, select_random_controls};

#[allow(clippy::unnecessary_wraps)]
fn output_type_func(_input_fields: &[Field]) -> PolarsResult<Field> {
    Ok(Field::new(
        PlSmallStr::from_static(""),
        DataType::List(Box::new(DataType::String)),
    ))
}

/// Case-control matching function exposed as Polars plugin
#[polars_expr(output_type_func=output_type_func)]
pub fn match_controls(inputs: &[Series], kwargs: MatchingConfig) -> PolarsResult<Series> {
    // Input validation - we need at least case PNRs, case birth dates, control PNRs, control birth dates
    if inputs.len() < 4 {
        polars_bail!(ComputeError: "match_controls requires at least 4 input series: case_pnrs, case_birth_dates, control_pnrs, control_birth_dates");
    }

    // Extract input series
    let case_pnrs = inputs[0].str()?;
    let case_birth_dates = inputs[1].date()?;
    let control_pnrs = inputs[2].str()?;
    let control_birth_dates = inputs[3].date()?;

    // Optional parent birth date series
    let case_mother_birth_dates = if inputs.len() > 4 {
        Some(inputs[4].date()?)
    } else {
        None
    };
    let case_father_birth_dates = if inputs.len() > 5 {
        Some(inputs[5].date()?)
    } else {
        None
    };
    let control_mother_birth_dates = if inputs.len() > 6 {
        Some(inputs[6].date()?)
    } else {
        None
    };
    let control_father_birth_dates = if inputs.len() > 7 {
        Some(inputs[7].date()?)
    } else {
        None
    };

    // Build control pool with optimized structure
    let controls = build_control_pool(
        control_pnrs,
        control_birth_dates,
        control_mother_birth_dates,
        control_father_birth_dates,
    );

    // Track used controls to avoid reuse
    let mut used_control_indices = HashSet::new();

    // Process each case
    let mut results = Vec::with_capacity(case_pnrs.len());

    for case_idx in 0..case_pnrs.len() {
        if let (Some(_case_pnr), Some(case_birth_date)) =
            (case_pnrs.get(case_idx), case_birth_dates.phys.get(case_idx))
        {
            let case_birth_day = case_birth_date;

            // Get case parent birth dates if matching is enabled
            let case_mother_birth_day = if kwargs.match_parent_birth_dates {
                case_mother_birth_dates.and_then(|ca| ca.phys.get(case_idx))
            } else {
                None
            };

            let case_father_birth_day =
                if kwargs.match_parent_birth_dates && !kwargs.match_mother_birth_date_only {
                    case_father_birth_dates.and_then(|ca| ca.phys.get(case_idx))
                } else {
                    None
                };

            // Find eligible controls
            let eligible_controls = find_eligible_controls(
                &controls,
                case_birth_day,
                case_mother_birth_day,
                case_father_birth_day,
                &used_control_indices,
                &kwargs,
            );

            // Select random controls up to matching_ratio
            let selected_controls = select_random_controls(
                &controls,
                &eligible_controls,
                kwargs.matching_ratio,
                &mut used_control_indices,
            );

            // Convert to Polars list format
            if selected_controls.is_empty() {
                results.push(None);
            } else {
                results.push(Some(selected_controls));
            }
        } else {
            results.push(None);
        }
    }

    // Convert results to Polars Series
    let list_series: ListChunked = results
        .into_iter()
        .map(|opt_vec| {
            opt_vec.map(|vec| {
                let strings: Vec<Option<&str>> = vec.iter().map(|s| Some(s.as_str())).collect();
                Series::new(PlSmallStr::from_static(""), strings)
            })
        })
        .collect();

    Ok(list_series.into_series())
}

/// Output type for `prepare_case_control_data` function - returns struct with cases and controls info
#[allow(clippy::unnecessary_wraps)]
fn prepare_output_type_func(_input_fields: &[Field]) -> PolarsResult<Field> {
    Ok(Field::new(
        PlSmallStr::from_static(""),
        DataType::Struct(vec![
            Field::new(PlSmallStr::from_static("n_cases"), DataType::UInt32),
            Field::new(PlSmallStr::from_static("n_controls"), DataType::UInt32),
            Field::new(PlSmallStr::from_static("cases_df_json"), DataType::String),
            Field::new(
                PlSmallStr::from_static("controls_df_json"),
                DataType::String,
            ),
        ]),
    ))
}

/// Prepare case and control `DataFrames` from combined MFR/LPR data
/// Input: Series containing PNR, `SCD_STATUS` - returns summary statistics
/// Returns: Struct with case/control counts and basic info
#[polars_expr(output_type_func=prepare_output_type_func)]
pub fn prepare_case_control_data(inputs: &[Series]) -> PolarsResult<Series> {
    if inputs.len() < 2 {
        polars_bail!(ComputeError: "prepare_case_control_data requires at least PNR and SCD_STATUS series");
    }

    let pnrs = inputs[0].str()?;
    let scd_statuses = inputs[1].str()?;

    // Count cases and controls
    let mut n_cases = 0u32;
    let mut n_controls = 0u32;

    for i in 0..scd_statuses.len() {
        if let Some(status) = scd_statuses.get(i) {
            match status {
                "SCD" | "SCD_LATE" => n_cases += 1,
                "NO_SCD" => n_controls += 1,
                _ => {},
            }
        }
    }

    let total_records = pnrs.len();
    let summary_json = format!(
        "{{\"total_records\": {}, \"cases\": {}, \"controls\": {}, \"case_ratio\": {:.3}}}",
        total_records,
        n_cases,
        n_controls,
        if total_records > 0 {
            #[allow(clippy::cast_precision_loss)]
            {
                f64::from(n_cases) / (total_records as f64)
            }
        } else {
            0.0
        }
    );

    let series_vec = [
        Series::new(PlSmallStr::from_static("n_cases"), [n_cases]),
        Series::new(PlSmallStr::from_static("n_controls"), [n_controls]),
        Series::new(
            PlSmallStr::from_static("cases_df_json"),
            [summary_json.as_str()],
        ),
        Series::new(
            PlSmallStr::from_static("controls_df_json"),
            [summary_json.as_str()],
        ),
    ];
    let result_struct = StructChunked::from_series(
        PlSmallStr::from_static(""),
        series_vec.len(),
        series_vec.iter(),
    )?;

    Ok(result_struct.into_series())
}

/// Output type for integrated matching workflow
#[allow(clippy::unnecessary_wraps)]
fn workflow_output_type_func(_input_fields: &[Field]) -> PolarsResult<Field> {
    Ok(Field::new(
        PlSmallStr::from_static(""),
        DataType::Struct(vec![
            Field::new(PlSmallStr::from_static("case_pnr"), DataType::String),
            Field::new(
                PlSmallStr::from_static("matched_controls"),
                DataType::List(Box::new(DataType::String)),
            ),
            Field::new(PlSmallStr::from_static("n_matched"), DataType::UInt32),
            Field::new(PlSmallStr::from_static("scd_date"), DataType::Date),
            Field::new(PlSmallStr::from_static("icd_code"), DataType::String),
        ]),
    ))
}

/// Complete integrated matching workflow that takes MFR+LPR combined data
/// and returns matched cases with their controls
/// Input: `case_pnr`, `matched_controls_list`, `n_matched`, `scd_date`, `icd_code` series
#[polars_expr(output_type_func=workflow_output_type_func)]
pub fn integrated_matching_workflow(inputs: &[Series]) -> PolarsResult<Series> {
    if inputs.len() < 3 {
        polars_bail!(ComputeError: "integrated_matching_workflow requires at least case_pnr, matched_controls, and scd_date series");
    }

    let case_pnrs = inputs[0].str()?;
    let matched_controls = inputs[1].list()?;
    let _scd_dates = inputs[2].date()?;

    // Optional ICD codes
    let icd_codes = if inputs.len() > 3 {
        Some(inputs[3].str()?)
    } else {
        None
    };

    // Calculate n_matched for each case
    let mut n_matched_vec = Vec::with_capacity(case_pnrs.len());

    for i in 0..matched_controls.len() {
        let n_matched = matched_controls.get(i).map_or(0u32, |controls_list| {
            u32::try_from(controls_list.len()).unwrap_or(0u32)
        });
        n_matched_vec.push(n_matched);
    }

    // Create result series
    let case_pnr_series = inputs[0].clone();
    let matched_controls_series = inputs[1].clone();
    let n_matched_series = Series::new(PlSmallStr::from_static("n_matched"), n_matched_vec);
    let scd_date_series = inputs[2].clone();

    let icd_code_series = icd_codes.map_or_else(
        || {
            Series::new(
                PlSmallStr::from_static("icd_code"),
                vec![""; case_pnrs.len()],
            )
        },
        |icd| icd.clone().into_series(),
    );

    let series_vec = [
        case_pnr_series.with_name(PlSmallStr::from_static("case_pnr")),
        matched_controls_series.with_name(PlSmallStr::from_static("matched_controls")),
        n_matched_series,
        scd_date_series.with_name(PlSmallStr::from_static("scd_date")),
        icd_code_series,
    ];

    let result_struct = StructChunked::from_series(
        PlSmallStr::from_static(""),
        series_vec.len(),
        series_vec.iter(),
    )?;

    Ok(result_struct.into_series())
}

/// Validate matching configuration parameters
/// Input: Series with configuration values
/// Returns: Boolean series indicating validity
#[allow(clippy::unnecessary_wraps)]
fn validate_config_type_func(_input_fields: &[Field]) -> PolarsResult<Field> {
    Ok(Field::new(PlSmallStr::from_static(""), DataType::Boolean))
}

#[polars_expr(output_type_func=validate_config_type_func)]
pub fn validate_matching_config(inputs: &[Series]) -> PolarsResult<Series> {
    if inputs.is_empty() {
        polars_bail!(ComputeError: "validate_matching_config requires input series");
    }

    // Basic validation - check if we have reasonable parameters
    // For now, return true for all entries (can be expanded with actual validation logic)
    let validations = vec![true; inputs[0].len()];

    Ok(Series::new(PlSmallStr::from_static(""), validations))
}

/// Count potential matches for cases before actual matching
/// Input: case series and control series
/// Returns: Series with match counts
#[allow(clippy::unnecessary_wraps)]
fn count_matches_type_func(_input_fields: &[Field]) -> PolarsResult<Field> {
    Ok(Field::new(PlSmallStr::from_static(""), DataType::UInt32))
}

#[polars_expr(output_type_func=count_matches_type_func)]
pub fn count_potential_matches(inputs: &[Series], kwargs: MatchingConfig) -> PolarsResult<Series> {
    if inputs.len() < 4 {
        polars_bail!(ComputeError: "count_potential_matches requires at least case_pnrs, case_birth_dates, control_pnrs, control_birth_dates");
    }

    let case_pnrs = inputs[0].str()?;
    let case_birth_dates = inputs[1].date()?;
    let control_pnrs = inputs[2].str()?;
    let control_birth_dates = inputs[3].date()?;

    // Optional parent birth date series
    let control_mother_birth_dates = if inputs.len() > 4 {
        Some(inputs[4].date()?)
    } else {
        None
    };
    let control_father_birth_dates = if inputs.len() > 5 {
        Some(inputs[5].date()?)
    } else {
        None
    };

    // Build control pool
    let controls = build_control_pool(
        control_pnrs,
        control_birth_dates,
        control_mother_birth_dates,
        control_father_birth_dates,
    );

    let mut match_counts = Vec::with_capacity(case_pnrs.len());
    let used_control_indices = HashSet::new(); // Empty for counting

    // Count potential matches for each case
    for case_idx in 0..case_pnrs.len() {
        if let Some(case_birth_date) = case_birth_dates.phys.get(case_idx) {
            let eligible_controls = find_eligible_controls(
                &controls,
                case_birth_date,
                None, // Simplified - no parent matching for counting
                None,
                &used_control_indices,
                &kwargs,
            );
            match_counts.push(u32::try_from(eligible_controls.len()).unwrap_or(u32::MAX));
        } else {
            match_counts.push(0u32);
        }
    }

    Ok(Series::new(PlSmallStr::from_static(""), match_counts))
}
