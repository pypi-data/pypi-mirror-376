use faer::Mat;

use super::AggregatedEffect;
use crate::computation::aggregation::{
    ci_from_att_se, group_prob_or_err, se_from_influence_col, uniform_band_critical,
    weighted_column, z_from_confidence,
};
use crate::{AttGtResult, DidError, DidResult};

/// Aggregate ATT(g,t) by treatment group, weighting groups by sampling probability.
/// Returns per-group effects and an overall average across groups.
///
/// # Errors
/// Returns an error if required group probabilities are missing.
pub fn compute_group_aggregation_exact(
    did: &DidResult,
    confidence_level: f64,
    use_uniform_bands: bool,
) -> Result<(Vec<AggregatedEffect>, f64, f64, f64, f64), DidError> {
    let inf_m = &did.influence_function;

    let mut groups: Vec<i64> = did.att_gt.iter().map(|r| r.group).collect();
    groups.sort_unstable();
    groups.dedup();

    let mut group_atts = Vec::new();
    let mut group_infs: Vec<Mat<f64>> = Vec::new();

    for g in &groups {
        let idx: Vec<(usize, &AttGtResult)> = did
            .att_gt
            .iter()
            .enumerate()
            .filter(|(_, r)| r.group == *g && r.group <= r.time)
            .collect();

        if idx.is_empty() {
            continue;
        }

        let n_post = idx.len() as f64;
        let atts: Vec<f64> = idx.iter().map(|(_, r)| r.att).collect();
        let indices: Vec<usize> = idx.iter().map(|(i, _)| *i).collect();
        let eq_w = vec![1.0 / n_post; idx.len()];

        let att = atts.iter().sum::<f64>() / n_post;
        let inf = weighted_column(inf_m, &indices, &eq_w);

        group_atts.push(att);
        group_infs.push(inf);
    }

    let mut w = Vec::new();
    for (i, g) in groups.iter().enumerate() {
        if i < group_atts.len() {
            w.push(group_prob_or_err(&did.group_probabilities, *g)?);
        }
    }

    let total_w: f64 = w.iter().sum();
    let norm_w: Vec<f64> = w.iter().map(|x| x / total_w).collect();
    let overall_att = group_atts
        .iter()
        .zip(&norm_w)
        .map(|(a, w)| a * w)
        .sum::<f64>();

    let mut overall_inf = Mat::zeros(inf_m.nrows(), 1);
    for (k, inf) in group_infs.iter().enumerate() {
        if k < norm_w.len() {
            let w = norm_w[k];
            for r in 0..overall_inf.nrows() {
                *overall_inf.get_mut(r, 0) += w * inf.get(r, 0);
            }
        }
    }

    let overall_se = se_from_influence_col(&overall_inf);
    let z = z_from_confidence(confidence_level);
    let (overall_low, overall_high) = ci_from_att_se(overall_att, overall_se, z);

    let mut effects = Vec::new();
    for (i, &g) in groups.iter().enumerate() {
        if i >= group_atts.len() {
            continue;
        }
        let att = group_atts[i];
        let inf = &group_infs[i];
        let se = se_from_influence_col(inf);
        let (low, high) = if use_uniform_bands {
            let delta = uniform_band_critical(inf, att);
            let crit = delta / se;
            ci_from_att_se(att, se, crit)
        } else {
            ci_from_att_se(att, se, z)
        };
        effects.push(AggregatedEffect {
            group: Some(g),
            time: None,
            event_time: None,
            att,
            se,
            conf_low: low,
            conf_high: high,
        });
    }

    Ok((effects, overall_att, overall_se, overall_low, overall_high))
}
