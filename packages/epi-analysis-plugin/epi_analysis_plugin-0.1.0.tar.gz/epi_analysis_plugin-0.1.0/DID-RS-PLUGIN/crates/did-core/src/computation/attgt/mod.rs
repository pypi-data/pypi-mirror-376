pub mod data_access;
pub mod estimate;
pub mod influence;
pub mod panel_estimator;
pub mod panel_wide_builder;
pub mod rc_estimator;
pub mod stats;

use std::collections::HashMap;

use data_access::DataArrays;
use faer::Mat;
use influence::{combine_influence_functions, scale_influence_col};
use panel_estimator::compute_single_att_gt_panel;
use panel_wide_builder::{setup_2x2_comparison, ComparisonParams};
use rc_estimator::compute_single_att_gt_rc_direct;
use stats::fill_attgt_stats;

use crate::computation::attgt::estimate::AttGtEstimate;
use crate::inference::bootstrap::MultiplierBootstrap;
use crate::inference::standard_errors::compute_attgt_se;
use crate::types::{AttGtResult, DidConfig, DidResult, PanelType};
use crate::DidError;

type InfluenceFunctionData = (Mat<f64>, Vec<usize>);
type AttGtComputationResult = Result<(Vec<AttGtResult>, Vec<InfluenceFunctionData>), DidError>;

pub struct AttGtComputer {
    pub(crate) config: DidConfig,
    pub(crate) data: crate::data::preprocessed::PreprocessedData,
}

/// Thin public entry to ATT(g,t) computation
pub fn compute_att_gt(
    config: DidConfig,
    data: crate::data::preprocessed::PreprocessedData,
) -> Result<crate::types::DidResult, DidError> {
    AttGtComputer::new(config, data).compute()
}

impl AttGtComputer {
    #[must_use]
    pub const fn new(config: DidConfig, data: crate::data::preprocessed::PreprocessedData) -> Self {
        Self { config, data }
    }

    pub fn compute(&self) -> Result<DidResult, DidError> {
        let arrays = data_access::DataArrays::new(&self.data, &self.config)?;
        let (sorted_groups, sorted_times) = sorted_time_groups(&self.data);
        let (unique_ids, id_to_idx) = build_id_mapping(arrays.id);

        let n_for_scaling_and_se = unique_ids.len();

        let (mut att_gt_results, influence_functions) = self.compute_all_att_gt(
            &arrays,
            &sorted_groups,
            &sorted_times,
            &id_to_idx,
            n_for_scaling_and_se,
        )?;

        let combined_influence =
            combine_influence_functions(&influence_functions, unique_ids.len());

        fill_attgt_stats(&mut att_gt_results, 1.96);
        self.apply_uniform_confidence_bands(&mut att_gt_results, &combined_influence);

        let (group_probabilities, unit_data) = self.compute_group_probabilities(&unique_ids)?;

        Ok(DidResult {
            att_gt: att_gt_results,
            influence_function: combined_influence,
            n_obs: unique_ids.len(),
            n_groups: self.data.glist.len(),
            n_periods: self.data.tlist.len(),
            method: self.config.method.clone(),
            config: self.config.clone(),
            group_probabilities,
            unit_data,
        })
    }
}

impl AttGtComputer {
    fn compute_all_att_gt(
        &self,
        arrays: &DataArrays<'_>,
        sorted_groups: &[i64],
        sorted_times: &[i64],
        id_to_idx: &HashMap<i64, usize>,
        n_for_scaling: usize,
    ) -> AttGtComputationResult {
        let mut results = Vec::new();
        let mut infs = Vec::new();

        for &g in sorted_groups {
            for &t in sorted_times {
                let pret = if t >= g { g - 1 } else { t - 1 };
                if !sorted_times.contains(&pret) {
                    continue;
                }

                let (batch, original_indices) = setup_2x2_comparison(
                    self,
                    ComparisonParams {
                        g,
                        t,
                        pret,
                        group_array: arrays.group,
                        time_array: arrays.time,
                        id_array: arrays.id,
                        id_to_idx,
                    },
                )?;

                if batch.num_rows() == 0 {
                    let n_unique = count_unique_ids(arrays.id);
                    results.push(zero_att_gt(g, t));
                    infs.push((Mat::zeros(n_unique, 1), (0..n_unique).collect()));
                    continue;
                }

                let est = match self.data.panel_type {
                    PanelType::RepeatedCrossSections => {
                        compute_single_att_gt_rc_direct(self, g, t)?
                    },
                    PanelType::UnbalancedPanel | PanelType::BalancedPanel => {
                        // Test: Use RC for ATT estimation but Panel for influence functions
                        let rc_est = compute_single_att_gt_rc_direct(self, g, t)?;
                        let panel_est = compute_single_att_gt_panel(self, g, t, &batch)?;

                        // Use RC ATT but Panel influence function
                        AttGtEstimate {
                            att: rc_est.att,
                            inf: panel_est.inf,
                            n1: panel_est.n1,
                        }
                    },
                };

                let mut res = crate::types::AttGtResult {
                    group: g,
                    time: t,
                    att: est.att,
                    se: 0.0,
                    t_stat: 0.0,
                    p_value: 0.0,
                    conf_low: 0.0,
                    conf_high: 0.0,
                };
                let mut inf = est.inf;
                let n1 = est.n1;

                // Apply unified scaling for all estimation methods
                if n1 > 0 {
                    let sf = n_for_scaling as f64 / n1 as f64;
                    scale_influence_col(&mut inf, sf);
                }

                // For RC path: aggregate per-observation to per-unit AFTER scaling
                if matches!(self.data.panel_type, PanelType::RepeatedCrossSections) {
                    inf = aggregate_rc_influence_by_id(&inf, &original_indices, n_for_scaling)?;
                }

                // Then compute standard error using scaled influence function
                if inf.nrows() > 0 {
                    let se = compute_attgt_se(inf.col_as_slice(0), inf.nrows() as f64);
                    res.se = se;
                }

                results.push(res);
                infs.push((inf, original_indices));
            }
        }

        Ok((results, infs))
    }

    fn apply_uniform_confidence_bands(
        &self,
        att_gt_results: &mut [AttGtResult],
        combined_influence: &Mat<f64>,
    ) {
        if att_gt_results.is_empty() {
            return;
        }
        let atts: Vec<f64> = att_gt_results.iter().map(|r| r.att).collect();
        let bootstrap =
            MultiplierBootstrap::new(self.config.bootstrap_iterations, None, self.config.rng_seed);
        let (low, high) = bootstrap.compute_uniform_bands(combined_influence, &atts);
        for (i, r) in att_gt_results.iter_mut().enumerate() {
            r.conf_low = low[i];
            r.conf_high = high[i];
        }
    }

    fn compute_group_probabilities(
        &self,
        unique_ids: &[i64],
    ) -> Result<(HashMap<i64, f64>, crate::types::UnitData), DidError> {
        let arrays = data_access::DataArrays::new(&self.data, &self.config)?;

        let weights: Vec<f64> = if let Some(weights_var) = &self.config.weights_var {
            if let Some(weights_col) = self.data.data.column_by_name(weights_var) {
                if let Some(float_array) = weights_col
                    .as_any()
                    .downcast_ref::<arrow::array::Float64Array>()
                {
                    unique_ids
                        .iter()
                        .enumerate()
                        .map(|(i, _)| float_array.value(i))
                        .collect()
                } else if let Some(int_array) = weights_col
                    .as_any()
                    .downcast_ref::<arrow::array::Int64Array>()
                {
                    unique_ids
                        .iter()
                        .enumerate()
                        .map(|(i, _)| int_array.value(i) as f64)
                        .collect()
                } else {
                    return Err(DidError::Specification(format!(
                        "Weights column '{weights_var}' must be numeric"
                    )));
                }
            } else {
                return Err(DidError::Specification(format!(
                    "Weights column '{weights_var}' not found"
                )));
            }
        } else {
            vec![1.0; unique_ids.len()]
        };

        let mut probs = HashMap::new();
        for &group in &self.data.glist {
            let mut wsum = 0.0;
            let mut wtot = 0.0;

            for (i, &_id) in unique_ids.iter().enumerate() {
                let gval = arrays.group.value(i);
                let w = weights[i];
                if gval == group {
                    wsum += w;
                }
                wtot += w;
            }

            let p = if wtot > 0.0 { wsum / wtot } else { 0.0 };
            probs.insert(group, p);
        }

        // Collect unit data for weight influence function
        let unit_groups: Vec<i64> = unique_ids
            .iter()
            .enumerate()
            .map(|(i, _)| arrays.group.value(i))
            .collect();

        let unit_data = crate::types::UnitData {
            unit_ids: unique_ids.to_vec(),
            unit_groups,
            unit_weights: weights,
        };

        Ok((probs, unit_data))
    }
}

fn sorted_time_groups(data: &crate::data::preprocessed::PreprocessedData) -> (Vec<i64>, Vec<i64>) {
    let mut groups = data.glist.clone();
    groups.sort_unstable();
    let mut times = data.tlist.clone();
    times.sort_unstable();
    (groups, times)
}

fn build_id_mapping(
    id_array: &arrow::array::Int64Array,
) -> (Vec<i64>, std::collections::HashMap<i64, usize>) {
    use std::collections::{HashMap, HashSet};
    let unique_ids: Vec<i64> = id_array
        .values()
        .iter()
        .copied()
        .collect::<HashSet<_>>()
        .into_iter()
        .collect();
    let id_to_idx: HashMap<i64, usize> = unique_ids
        .iter()
        .enumerate()
        .map(|(i, &id)| (id, i))
        .collect();
    (unique_ids, id_to_idx)
}

fn count_unique_ids(id_array: &arrow::array::Int64Array) -> usize {
    use std::collections::HashSet;
    id_array
        .values()
        .iter()
        .copied()
        .collect::<HashSet<_>>()
        .len()
}

const fn zero_att_gt(group: i64, time: i64) -> crate::types::AttGtResult {
    crate::types::AttGtResult {
        group,
        time,
        att: 0.0,
        se: 0.0,
        t_stat: 0.0,
        p_value: 1.0,
        conf_low: 0.0,
        conf_high: 0.0,
    }
}

/// Aggregate per-observation influence functions by ID to get per-unit influence functions
/// This must be called AFTER scaling to preserve the scale
fn aggregate_rc_influence_by_id(
    inf: &Mat<f64>,
    original_indices: &[usize],
    n_unique_ids: usize,
) -> Result<Mat<f64>, DidError> {
    let mut aggregated = Mat::zeros(n_unique_ids, 1);

    // Sum influence function values by unit ID
    for (obs_idx, &unit_idx) in original_indices.iter().enumerate() {
        let inf_val = inf.get(obs_idx, 0);
        *aggregated.get_mut(unit_idx, 0) += inf_val;
    }

    Ok(aggregated)
}
