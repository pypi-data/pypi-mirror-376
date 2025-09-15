use std::collections::HashSet;

use faer::Mat;

use super::AggregatedEffect;
use crate::computation::aggregation::{
    ci_from_att_se, group_prob_or_err, se_from_influence_col, uniform_band_critical,
    weighted_average_with_if, z_from_confidence,
};
use crate::{AttGtResult, DidError, DidResult};

/// Aggregate ATT(g,t) by calendar time t, weighting groups by sampling probability.
/// Returns per-time effects and an overall average.
///
/// # Errors
/// Returns an error if required group probabilities are missing.
pub fn compute_calendar_aggregation_exact(
    did: &DidResult,
    confidence_level: f64,
    use_uniform_bands: bool,
) -> Result<(Vec<AggregatedEffect>, f64, f64, f64, f64), DidError> {
    let inf_m = &did.influence_function;

    let min_group = did.att_gt.iter().map(|r| r.group).min().unwrap_or(0);
    let mut times: Vec<i64> = did
        .att_gt
        .iter()
        .map(|r| r.time)
        .filter(|&t| t >= min_group)
        .collect::<HashSet<_>>()
        .into_iter()
        .collect();
    times.sort_unstable();

    let mut time_atts = Vec::new();
    let mut time_infs: Vec<Mat<f64>> = Vec::new();

    for &t in &times {
        let idx: Vec<(usize, &AttGtResult)> = did
            .att_gt
            .iter()
            .enumerate()
            .filter(|(_, r)| r.time == t && r.group <= r.time)
            .collect();

        if idx.is_empty() {
            continue;
        }

        let mut w = Vec::with_capacity(idx.len());
        let mut atts = Vec::with_capacity(idx.len());
        let mut indices = Vec::with_capacity(idx.len());
        for (i, r) in &idx {
            w.push(group_prob_or_err(&did.group_probabilities, r.group)?);
            atts.push(r.att);
            indices.push(*i);
        }

        let (att, inf) = weighted_average_with_if(inf_m, &atts, &indices, &w);
        time_atts.push(att);
        time_infs.push(inf);
    }

    let overall_att = if time_atts.is_empty() {
        0.0
    } else {
        time_atts.iter().sum::<f64>() / time_atts.len() as f64
    };

    let mut overall_inf = Mat::zeros(inf_m.nrows(), 1);
    let eq_w = if time_infs.is_empty() {
        0.0
    } else {
        1.0 / time_infs.len() as f64
    };
    for inf in &time_infs {
        for r in 0..overall_inf.nrows() {
            *overall_inf.get_mut(r, 0) += eq_w * inf.get(r, 0);
        }
    }

    let overall_se = if time_infs.is_empty() {
        0.0
    } else {
        se_from_influence_col(&overall_inf)
    };
    let z = z_from_confidence(confidence_level);
    let (overall_low, overall_high) = ci_from_att_se(overall_att, overall_se, z);

    let mut effects = Vec::new();
    for (i, &t) in times.iter().enumerate() {
        if i >= time_atts.len() {
            continue;
        }
        let att = time_atts[i];
        let inf = &time_infs[i];
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
            time: Some(t),
            event_time: None,
            att,
            se,
            conf_low: low,
            conf_high: high,
        });
    }

    Ok((effects, overall_att, overall_se, overall_low, overall_high))
}
