use std::collections::HashMap;

use faer::Mat;

use crate::inference::bootstrap::MultiplierBootstrap;
use crate::DidError;

#[must_use]
pub fn z_from_confidence(confidence_level: f64) -> f64 {
    match confidence_level {
        0.90 => 1.645,
        0.95 => 1.96,
        0.99 => 2.576,
        _ => 1.96,
    }
}

#[must_use]
pub fn se_from_influence_col(inf: &Mat<f64>) -> f64 {
    let n = inf.nrows() as f64;
    let col = inf.col_as_slice(0);
    (col.iter().map(|x| x * x).sum::<f64>() / n).sqrt() / n.sqrt()
}

#[must_use]
pub fn ci_from_att_se(att: f64, se: f64, z: f64) -> (f64, f64) {
    (z.mul_add(-se, att), z.mul_add(se, att))
}

// Returns the delta = att - lband, caller can divide by se to get z_crit and form CI.
#[must_use]
pub fn uniform_band_critical(inf: &Mat<f64>, att: f64) -> f64 {
    let bootstrap = MultiplierBootstrap::new(1000, None, None);
    let (low, _) = bootstrap.compute_uniform_bands(inf, &[att]);
    att - low[0]
}

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

pub fn group_prob_or_err(map: &HashMap<i64, f64>, group: i64) -> Result<f64, DidError> {
    map.get(&group).copied().ok_or_else(|| {
        DidError::Specification(format!("Group probability not found for group {group}"))
    })
}
