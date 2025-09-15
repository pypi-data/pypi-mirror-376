use std::collections::HashMap;

use faer::Mat;

use crate::types::UnitData;

#[must_use]
pub fn weighted_column(influence: &Mat<f64>, indices: &[usize], weights: &[f64]) -> Mat<f64> {
    let n = influence.nrows();
    let mut out = Mat::zeros(n, 1);
    for (k, &idx) in indices.iter().enumerate() {
        let w = weights[k];
        for r in 0..n {
            let v = influence.get(r, idx);
            *out.get_mut(r, 0) += w * v;
        }
    }
    out
}

#[must_use]
pub fn weighted_average_with_if(
    influence: &Mat<f64>,
    atts: &[f64],
    indices: &[usize],
    unnorm_w: &[f64],
) -> (f64, Mat<f64>) {
    let total_w: f64 = unnorm_w.iter().sum();
    let norm_w: Vec<f64> = unnorm_w.iter().map(|w| w / total_w).collect();
    let att = atts.iter().zip(&norm_w).map(|(a, w)| a * w).sum::<f64>();
    let inf = weighted_column(influence, indices, &norm_w);
    (att, inf)
}

/// Compute the weight influence function (wif) following R's implementation
///
/// This function computes the extra term that shows up in the influence function
/// for aggregated treatment effect parameters due to estimating the weights.
///
/// Follows R's wif function in compute.aggte.R
#[must_use]
pub fn compute_weight_influence_function(
    keepers: &[usize],
    group_probabilities: &HashMap<i64, f64>,
    unit_data: &UnitData,
    group_assignments: &[i64],
) -> Mat<f64> {
    let n_units = unit_data.unit_ids.len();
    let n_keepers = keepers.len();

    // Extract group probabilities for the keeper indices
    let pg: Vec<f64> = group_assignments
        .iter()
        .map(|&group| group_probabilities[&group])
        .collect();

    let sum_pg: f64 = pg.iter().sum();

    // Initialize result matrix: n_units x n_keepers
    let mut wif = Mat::zeros(n_units, n_keepers);

    // R: if1 <- sapply(keepers, function(k) {
    //   (weights.ind * 1*BMisc::TorF(G==group[k]) - pg[k]) / sum(pg[keepers])
    // })
    for (keeper_idx, &target_group) in group_assignments.iter().enumerate() {
        let pg_k = pg[keeper_idx];

        for unit_idx in 0..n_units {
            let weight = unit_data.unit_weights[unit_idx];
            let unit_group = unit_data.unit_groups[unit_idx];

            // TorF(G==group[k]) is 1.0 if unit is in target group, 0.0 otherwise
            let group_indicator = if unit_group == target_group { 1.0 } else { 0.0 };

            let if1_value = weight.mul_add(group_indicator, -pg_k) / sum_pg;
            *wif.get_mut(unit_idx, keeper_idx) = if1_value;
        }
    }

    // R: if2 <- base::rowSums( sapply( keepers, function(k) {
    //   weights.ind*1*BMisc::TorF(G==group[k]) - pg[k]
    // })) %*% t(pg[keepers]/(sum(pg[keepers])^2))

    // First compute row sums of the inner sapply
    let mut row_sums = vec![0.0; n_units];
    for unit_idx in 0..n_units {
        let weight = unit_data.unit_weights[unit_idx];
        let unit_group = unit_data.unit_groups[unit_idx];

        let mut sum = 0.0;
        for (keeper_idx, &target_group) in group_assignments.iter().enumerate() {
            let pg_k = pg[keeper_idx];
            let group_indicator = if unit_group == target_group { 1.0 } else { 0.0 };
            sum += weight.mul_add(group_indicator, -pg_k);
        }
        row_sums[unit_idx] = sum;
    }

    // Now compute the outer product: row_sums %*% t(pg[keepers]/(sum(pg[keepers])^2))
    let sum_pg_squared = sum_pg * sum_pg;
    for unit_idx in 0..n_units {
        for keeper_idx in 0..n_keepers {
            let if2_value = row_sums[unit_idx] * (pg[keeper_idx] / sum_pg_squared);
            *wif.get_mut(unit_idx, keeper_idx) -= if2_value; // subtract because R does if1 - if2
        }
    }

    wif
}

/// Enhanced version of `weighted_average_with_if` that includes weight influence function
/// Following R's `get_agg_inf_func` implementation
#[must_use]
pub fn weighted_average_with_wif(
    influence_function: &Mat<f64>,
    att_estimates: &[f64],
    keeper_indices: &[usize],
    unnormalized_weights: &[f64],
    weight_if: Option<&Mat<f64>>,
) -> (f64, Mat<f64>) {
    // Normalize weights
    let total_w: f64 = unnormalized_weights.iter().sum();
    let normalized_weights: Vec<f64> = unnormalized_weights.iter().map(|w| w / total_w).collect();

    // Compute weighted ATT estimate
    let att = att_estimates
        .iter()
        .zip(&normalized_weights)
        .map(|(a, w)| a * w)
        .sum::<f64>();

    // Compute basic weighted influence function
    let n_units = influence_function.nrows();
    let mut result = Mat::zeros(n_units, 1);

    // R: thisinffunc <- inffunc1[,whichones]%*%weights.agg
    for (i, &keeper_idx) in keeper_indices.iter().enumerate() {
        let weight = normalized_weights[i];
        for unit_idx in 0..n_units {
            let influence_val = influence_function.get(unit_idx, keeper_idx);
            *result.get_mut(unit_idx, 0) += influence_val * weight;
        }
    }

    // R: if (!is.null(wif)) { thisinffunc <- thisinffunc + wif%*%as.matrix(att[whichones]) }
    if let Some(wif) = weight_if {
        for unit_idx in 0..n_units {
            let mut wif_contribution = 0.0;
            for (i, &keeper_idx) in keeper_indices.iter().enumerate() {
                let att_val = att_estimates[keeper_idx]; // Use the actual keeper index to get correct ATT
                let wif_val = wif.get(unit_idx, i);
                wif_contribution += wif_val * att_val;
            }
            *result.get_mut(unit_idx, 0) += wif_contribution;
        }
    }

    (att, result)
}
