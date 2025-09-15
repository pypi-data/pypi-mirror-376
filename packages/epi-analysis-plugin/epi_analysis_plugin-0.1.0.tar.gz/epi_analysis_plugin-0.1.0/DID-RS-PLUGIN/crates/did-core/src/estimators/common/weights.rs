#[must_use]
pub fn trim(ps: &[f64], eps: f64) -> Vec<f64> {
    ps.iter().map(|&p| p.clamp(eps, 1.0 - eps)).collect()
}

#[must_use]
pub fn stabilize(weights: &[f64]) -> Vec<f64> {
    let mean = weights.iter().sum::<f64>() / weights.len() as f64;
    weights.iter().map(|w| w / mean).collect()
}

#[must_use]
pub fn horvitz_thompson(outcome: &[f64], treat: &[f64], ps: &[f64]) -> f64 {
    let n = outcome.len();
    let mut sum = 0.0;
    for i in 0..n {
        sum += treat[i] * outcome[i] / ps[i] - (1.0 - treat[i]) * outcome[i] / (1.0 - ps[i]);
    }
    sum / n as f64
}

#[must_use]
pub fn diag_sparse_from_vec(w: &[f64]) -> faer::sparse::SparseColMat<usize, f64> {
    let mut triplets = Vec::with_capacity(w.len());
    for (i, &v) in w.iter().enumerate() {
        triplets.push(faer::sparse::Triplet::new(i, i, v));
    }
    faer::sparse::SparseColMat::try_new_from_triplets(w.len(), w.len(), &triplets).unwrap()
}
