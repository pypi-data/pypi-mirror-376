use std::collections::{HashMap, HashSet};

use arrow::array::{Array, BooleanArray, Float64Array, Int64Array, StringArray};
use faer::Mat;

use super::estimate::AttGtEstimate;
use crate::computation::attgt::data_access::DataArrays;
use crate::data::preprocessed::PreprocessedData;
use crate::estimators::did::rc::drdid::DRDIDRC;
use crate::estimators::did::rc::ipw::IPWRC;
use crate::estimators::did::rc::reg::RegRC;
use crate::types::{BasePeriod, ControlGroup, DidConfig, EstimationMethod};
use crate::DidError;

pub fn compute_single_att_gt_rc_direct(
    this: &crate::computation::attgt::AttGtComputer,
    group: i64,
    time: i64,
) -> Result<AttGtEstimate, DidError> {
    let pret = match this.config.base_period {
        BasePeriod::Varying => {
            if time >= group {
                group - 1
            } else {
                time - 1
            }
        },
        BasePeriod::Universal => {
            let anticipation = 0;
            group - 1 - anticipation
        },
    };

    let rc = extract_rc_data_for_periods(&this.data, &this.config, group, time, pret)?;

    let n1 = rc.y.nrows();
    // Unconditional case: no covariates => call DRDIDRC with intercept-only to get RC influence
    let (att, inf) = if this.config.control_vars.is_empty() {
        let n = rc.y.nrows();
        let covariates = Mat::from_fn(n, 1, |_, _| 1.0);
        let est = DRDIDRC::new(
            rc.y,
            rc.post,
            rc.treatment,
            covariates,
            Some(rc.weights),
            this.config.loss,
        );
        est.estimate()?
    } else {
        match this.config.method {
            EstimationMethod::Dr => {
                let est = DRDIDRC::new(
                    rc.y,
                    rc.post,
                    rc.treatment,
                    rc.covariates,
                    Some(rc.weights),
                    this.config.loss,
                );
                est.estimate()?
            },
            EstimationMethod::Ip => {
                let est = IPWRC::new(
                    rc.y,
                    rc.post,
                    rc.treatment,
                    rc.covariates,
                    Some(rc.weights),
                    this.config.loss,
                );
                est.estimate()?
            },
            EstimationMethod::Reg => {
                let est = RegRC::new(rc.y, rc.post, rc.treatment, rc.covariates, Some(rc.weights));
                est.estimate()?
            },
        }
    };

    // CRITICAL: Apply R's scaling logic first, THEN aggregate
    // R does: attgt$att.inf.func <- (n/n1)*attgt$att.inf.func
    // THEN: aggte_inffunc = stats::aggregate(attgt$att.inf.func, list(rightids), sum)

    // Get total unique IDs count (equivalent to R's 'n')
    // Return scaled individual influence functions (like Panel path)
    // Don't aggregate by ID here - let the aggregation happen in simple.rs

    Ok(AttGtEstimate { att, inf, n1 })
}
#[allow(dead_code)]
struct RCData {
    y: Mat<f64>,
    post: Mat<f64>,
    treatment: Mat<f64>,
    covariates: Mat<f64>,
    weights: Mat<f64>,
    ids: Vec<i64>,
    original_indices: Vec<usize>,
}

fn extract_rc_data_for_periods(
    data: &PreprocessedData,
    config: &DidConfig,
    group: i64,
    time: i64,
    pret: i64,
) -> Result<RCData, DidError> {
    let arrays = DataArrays::new(data, config)?;
    let outcome_array = data
        .data
        .column_by_name(&config.outcome_var)
        .ok_or_else(|| {
            DidError::Specification(format!("Outcome column '{}' not found", config.outcome_var))
        })?
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| DidError::Specification("Outcome column must be Float64".into()))?;

    // Standardize times/cohorts like did: gt_index = sort(union(glist, tlist))
    let gt_index: Vec<i64> = {
        let mut v = data.glist.clone();
        v.extend_from_slice(&data.tlist);
        v.sort_unstable();
        v.dedup();
        v
    };
    // Build mapping original -> standardized index (1-based in R; use 1-based to mirror logic)
    let mut idx_map = std::collections::HashMap::new();
    for (i, &val) in gt_index.iter().enumerate() {
        idx_map.insert(val, (i as i64) + 1);
    }
    let group_idx = *idx_map.get(&group).unwrap_or(&group);
    let time_idx = *idx_map.get(&time).unwrap_or(&time);
    let pret_idx = *idx_map.get(&pret).unwrap_or(&pret);

    let is_treated = |g_val: i64| *idx_map.get(&g_val).unwrap_or(&g_val) == group_idx;
    let is_control = |g_val: i64| match config.control_group {
        ControlGroup::NeverTreated => g_val == 0,
        ControlGroup::NotYetTreated => {
            let g_cohort = *idx_map.get(&g_val).unwrap_or(&g_val);
            let max_idx = time_idx.max(pret_idx);
            (g_val == 0) || ((g_cohort > max_idx) && (g_cohort != group_idx))
        },
    };

    // Prepare covariate specs: numeric/bool -> single column; string -> one-hot (drop last category)
    #[derive(Clone)]
    enum CovSpec {
        Numeric {
            var: String,
        },
        Categorical {
            var: String,
            categories: Vec<String>,
        }, // full set; we will drop last when expanding
    }

    let cov_specs: Vec<CovSpec> = config
        .control_vars
        .iter()
        .filter_map(|var| {
            if let Some(col) = data.data.column_by_name(var) {
                if col.as_any().is::<StringArray>() {
                    let arr = col.as_any().downcast_ref::<StringArray>().unwrap();
                    let mut cats: HashSet<String> = HashSet::new();
                    for i in 0..arr.len() {
                        if !arr.is_null(i) {
                            cats.insert(arr.value(i).to_owned());
                        }
                    }
                    let mut cats: Vec<String> = cats.into_iter().collect();
                    cats.sort();
                    Some(CovSpec::Categorical {
                        var: var.clone(),
                        categories: cats,
                    })
                } else {
                    Some(CovSpec::Numeric { var: var.clone() })
                }
            } else {
                None
            }
        })
        .collect();

    let mut y_vals = Vec::new();
    let mut post_vals = Vec::new();
    let mut treatment_vals = Vec::new();
    let mut cov_rows: Vec<Vec<f64>> = Vec::new();
    let mut weight_vals = Vec::new();
    let mut id_vals = Vec::new();
    let mut original_indices = Vec::new();

    let mut cnt_tp = 0usize;
    let mut cnt_tpre = 0usize;
    let mut cnt_cp = 0usize;
    let mut cnt_cpre = 0usize;
    for i in 0..data.data.num_rows() {
        let tval = arrays.time.value(i);
        let gval = arrays.group.value(i);

        if tval != time && tval != pret {
            continue;
        }
        let is_in_treated = is_treated(gval);
        let is_in_control = is_control(gval);
        if !is_in_treated && !is_in_control {
            continue;
        }

        let post_flag = if tval == time { 1.0 } else { 0.0 };
        if is_in_treated {
            if post_flag == 1.0 {
                cnt_tp += 1;
            } else {
                cnt_tpre += 1;
            }
        } else if post_flag == 1.0 {
            cnt_cp += 1;
        } else {
            cnt_cpre += 1;
        }

        y_vals.push(outcome_array.value(i));
        post_vals.push(post_flag);
        treatment_vals.push(if is_in_treated { 1.0 } else { 0.0 });
        weight_vals.push(1.0);
        id_vals.push(arrays.id.value(i));
        original_indices.push(i);

        let mut row: Vec<f64> = Vec::new();
        row.push(1.0); // intercept
        for spec in &cov_specs {
            match spec {
                CovSpec::Numeric { var } => {
                    row.push(extract_scalar_value(data, var, i));
                },
                CovSpec::Categorical { var, categories } => {
                    // Expand into K-1 dummies, drop the last category
                    let k = categories.len();
                    if k == 0 {
                        continue;
                    }
                    let val_opt = data
                        .data
                        .column_by_name(var)
                        .and_then(|col| col.as_any().downcast_ref::<StringArray>())
                        .and_then(|arr| {
                            if arr.is_null(i) {
                                None
                            } else {
                                Some(arr.value(i))
                            }
                        });
                    for cat in categories.iter().take(k.saturating_sub(1)) {
                        let is_match = val_opt.is_some_and(|v| v == cat);
                        row.push(if is_match { 1.0 } else { 0.0 });
                    }
                },
            }
        }
        cov_rows.push(row);
    }

    if group == 2004 && time == 2004 {
        log::info!(
            "RC cohort counts (g=2004,t=2004): T_post={cnt_tp}, T_pre={cnt_tpre}, C_post={cnt_cp}, C_pre={cnt_cpre}"
        );
    }

    let n_obs = y_vals.len();
    // Compute number of covariate columns from specs (intercept + numeric + (k-1) per categorical)
    let n_covs: usize = 1 + cov_specs
        .iter()
        .map(|s| match s {
            CovSpec::Numeric { .. } => 1usize,
            CovSpec::Categorical { categories, .. } => categories.len().saturating_sub(1),
        })
        .sum::<usize>();
    if n_obs == 0 {
        return Err(DidError::Estimation(format!(
            "No observations found for group {group} in periods {time} and {pret}"
        )));
    }

    let y = Mat::from_fn(n_obs, 1, |i, _| y_vals[i]);
    let post = Mat::from_fn(n_obs, 1, |i, _| post_vals[i]);
    let treatment = Mat::from_fn(n_obs, 1, |i, _| treatment_vals[i]);
    let weights = Mat::from_fn(n_obs, 1, |i, _| weight_vals[i]);
    let covariates = Mat::from_fn(n_obs, n_covs, |i, j| cov_rows[i][j]);

    Ok(RCData {
        y,
        post,
        treatment,
        covariates,
        weights,
        ids: id_vals,
        original_indices,
    })
}

fn extract_scalar_value(data: &PreprocessedData, var: &str, row: usize) -> f64 {
    data.data.column_by_name(var).map_or(0.0, |col| {
        col.as_any().downcast_ref::<Float64Array>().map_or_else(
            || {
                col.as_any().downcast_ref::<Int64Array>().map_or_else(
                    || {
                        col.as_any()
                            .downcast_ref::<BooleanArray>()
                            .map_or(0.0, |ba| if ba.value(row) { 1.0 } else { 0.0 })
                    },
                    |ia| ia.value(row) as f64,
                )
            },
            |fa| fa.value(row),
        )
    })
}

/// Aggregate influence functions by ID for repeated cross-sections
/// This implements R's: `aggte_inffunc` = `stats::aggregate(attgt$att.inf.func`, list(rightids), sum)
///
/// The key insight: we need to aggregate by ID but return the influence function
/// in the same structure that the main algorithm expects (based on the original data ordering)
#[allow(dead_code)]
fn aggregate_influence_by_id(
    inf: &Mat<f64>,
    ids: &[i64],
    original_indices: &[usize],
    data: &PreprocessedData,
    config: &DidConfig,
) -> Result<Mat<f64>, DidError> {
    let ids_mat = Mat::from_fn(ids.len(), 1, |i, _| ids[i] as f64);
    if inf.nrows() != ids_mat.nrows() || ids.len() != original_indices.len() {
        return Err(DidError::Estimation(format!(
            "Dimension mismatch: inf={}, ids={}, indices={}",
            inf.nrows(),
            ids.len(),
            original_indices.len()
        )));
    }

    // Step 1: Aggregate influence function values by unique ID
    let mut id_to_inf = HashMap::new();
    for (i, &id) in ids.iter().enumerate() {
        let inf_val = inf[(i, 0)];
        *id_to_inf.entry(id).or_insert(0.0) += inf_val;
    }

    // Step 2: Get all unique IDs from the full dataset in original order
    let arrays = DataArrays::new(data, config)?;
    let mut seen_ids = std::collections::HashSet::new();
    let mut unique_dataset_ids = Vec::new();

    for i in 0..data.data.num_rows() {
        let id = arrays.id.value(i);
        if seen_ids.insert(id) {
            unique_dataset_ids.push(id);
        }
    }

    // Step 3: Create influence function matrix matching the full dataset structure
    // Each row corresponds to a unique ID in the original dataset order
    let n_unique = unique_dataset_ids.len();
    let mut aggregated = Mat::zeros(n_unique, 1);

    for (i, &id) in unique_dataset_ids.iter().enumerate() {
        if let Some(&inf_val) = id_to_inf.get(&id) {
            *aggregated.get_mut(i, 0) = inf_val;
        }
        // If ID not in our aggregated map, it stays 0.0 (correct for non-participants)
    }

    Ok(aggregated)
}
#[allow(dead_code)]
fn count_unique_ids(id_array: &arrow::array::Int64Array) -> usize {
    use std::collections::HashSet;
    id_array
        .values()
        .iter()
        .copied()
        .collect::<HashSet<_>>()
        .len()
}
