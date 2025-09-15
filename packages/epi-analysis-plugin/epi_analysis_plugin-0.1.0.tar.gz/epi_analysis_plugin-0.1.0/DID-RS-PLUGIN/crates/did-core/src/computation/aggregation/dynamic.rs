use std::collections::HashMap;

use faer::Mat;

use super::AggregatedEffect;
use crate::computation::aggregation::{
    ci_from_att_se, group_prob_or_err, se_from_influence_col, uniform_band_critical,
    weighted_average_with_if, z_from_confidence,
};
use crate::{AttGtResult, DidError, DidResult};

/// Aggregate ATT(g,t) by event time (t - g), weighting groups by sampling probability.
/// Returns per-event-time effects and an overall post-treatment average.
///
/// # Errors
/// Returns an error if required group probabilities are missing.
pub fn compute_dynamic_aggregation_exact(
    did: &DidResult,
    confidence_level: f64,
    use_uniform_bands: bool,
) -> Result<(Vec<AggregatedEffect>, f64, f64, f64, f64), DidError> {
    let inf_m = &did.influence_function;

    let mut by_et: HashMap<i64, Vec<(usize, AttGtResult)>> = HashMap::new();
    for (i, r) in did.att_gt.iter().cloned().enumerate() {
        by_et.entry(r.time - r.group).or_default().push((i, r));
    }

    let mut ets = Vec::new();
    let mut att_vec = Vec::new();
    let mut inf_vec: Vec<Mat<f64>> = Vec::new();

    for (et, rows) in by_et {
        let mut w = Vec::with_capacity(rows.len());
        let mut atts = Vec::with_capacity(rows.len());
        let mut idxs = Vec::with_capacity(rows.len());
        for (i, r) in &rows {
            w.push(group_prob_or_err(&did.group_probabilities, r.group)?);
            atts.push(r.att);
            idxs.push(*i);
        }
        let (att, inf) = weighted_average_with_if(inf_m, &atts, &idxs, &w);
        ets.push(et);
        att_vec.push(att);
        inf_vec.push(inf);
    }

    let mut ord: Vec<usize> = (0..ets.len()).collect();
    ord.sort_by_key(|&i| ets[i]);

    let z = z_from_confidence(confidence_level);
    let mut effects = Vec::with_capacity(ord.len());

    for &i in &ord {
        let att = att_vec[i];
        let inf = &inf_vec[i];
        let se = se_from_influence_col(inf);
        let (low, high) = if use_uniform_bands {
            let delta = uniform_band_critical(inf, att);
            let crit = delta / se;
            ci_from_att_se(att, se, crit)
        } else {
            ci_from_att_se(att, se, z)
        };
        effects.push(AggregatedEffect {
            group: None,
            time: None,
            event_time: Some(ets[i]),
            att,
            se,
            conf_low: low,
            conf_high: high,
        });
    }

    let pos: Vec<usize> = ord.into_iter().filter(|&i| ets[i] >= 0).collect();
    if pos.is_empty() {
        return Ok((effects, 0.0, 0.0, 0.0, 0.0));
    }

    let overall_att = pos.iter().map(|&i| att_vec[i]).sum::<f64>() / pos.len() as f64;

    let mut overall_inf = Mat::zeros(inf_m.nrows(), 1);
    let w_eq = 1.0 / pos.len() as f64;
    for &i in &pos {
        let inf = &inf_vec[i];
        for r in 0..overall_inf.nrows() {
            *overall_inf.get_mut(r, 0) += w_eq * inf.get(r, 0);
        }
    }

    let overall_se = se_from_influence_col(&overall_inf);
    let (overall_low, overall_high) = ci_from_att_se(overall_att, overall_se, z);

    Ok((effects, overall_att, overall_se, overall_low, overall_high))
}
