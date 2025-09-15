use faer::Mat;

use crate::computation::aggregation::weights::{
    compute_weight_influence_function, weighted_average_with_wif,
};
use crate::computation::aggregation::{group_prob_or_err, weighted_average_with_if};
use crate::inference::standard_errors::compute_aggte_se;
use crate::{AttGtResult, DidError, DidResult};

/// Simple overall ATT: weighted average of all valid ATT(g,t) entries.
/// Returns (att, se, influence).
///
/// # Errors
/// Returns an error if required group probabilities are missing.
pub fn compute_simple_aggregation(did: &DidResult) -> Result<(f64, f64, Mat<f64>), DidError> {
    let keepers: Vec<(usize, &AttGtResult)> = did
        .att_gt
        .iter()
        .enumerate()
        .filter(|(_, r)| r.group <= r.time)
        .collect();

    if keepers.is_empty() {
        return Ok((0.0, 0.0, Mat::zeros(did.influence_function.nrows(), 1)));
    }

    let mut unnorm_w = Vec::with_capacity(keepers.len());
    let mut atts = Vec::with_capacity(keepers.len());
    let mut idxs = Vec::with_capacity(keepers.len());
    for (i, r) in &keepers {
        unnorm_w.push(group_prob_or_err(&did.group_probabilities, r.group)?);
        atts.push(r.att);
        idxs.push(*i);
    }

    // Compute weight influence function to account for estimation uncertainty in group probabilities
    // This follows R's simple aggregation: simple.wif <- wif(keepers, pg, weights.ind, G, group)
    let group_assignments: Vec<i64> = keepers.iter().map(|(_, r)| r.group).collect();
    let keeper_indices: Vec<usize> = keepers.iter().map(|(i, _)| *i).collect();

    let weight_if = compute_weight_influence_function(
        &keeper_indices,
        &did.group_probabilities,
        &did.unit_data,
        &group_assignments,
    );

    // Get all ATT estimates for the WIF function (R: att[whichones])
    let all_atts: Vec<f64> = did.att_gt.iter().map(|r| r.att).collect();

    // Compute aggregated influence function with weight correction
    // R: simple.if <- get_agg_inf_func(att=att, inffunc1=inffunc1, whichones=keepers,
    //                                  weights.agg=pg[keepers]/sum(pg[keepers]), wif=simple.wif)
    // Compute ATT using standard weighted average (WIF should not affect point estimate)
    let (att, _) = weighted_average_with_if(&did.influence_function, &atts, &idxs, &unnorm_w);

    // Compute influence function WITH weight correction (this is where WIF matters)
    let (_, inf) = weighted_average_with_wif(
        &did.influence_function,
        &all_atts, // Pass all ATT estimates so indexing works correctly
        &keeper_indices,
        &unnorm_w,
        Some(&weight_if), // Re-enable WIF implementation
    );

    // Use the correct R formula: sqrt(mean(if^2) / n)
    let n = inf.nrows() as f64;
    let col = inf.col_as_slice(0);
    let se = compute_aggte_se(col, n);

    Ok((att, se, inf))
}
