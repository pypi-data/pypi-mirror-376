use faer::Mat;

/// Compute standard error from a single influence-function column.
#[must_use]
pub fn se_from_influence_col(inf: &Mat<f64>) -> f64 {
    let n = inf.nrows() as f64;
    let col = inf.col_as_slice(0);
    (col.iter().map(|x| x * x).sum::<f64>() / n).sqrt() / n.sqrt()
}
