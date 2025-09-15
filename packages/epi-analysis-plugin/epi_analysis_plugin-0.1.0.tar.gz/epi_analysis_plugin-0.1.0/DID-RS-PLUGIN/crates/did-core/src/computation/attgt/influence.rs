use faer::Mat;

/// Multiply the first column of an influence matrix by a factor.
pub fn scale_influence_col(inf: &mut Mat<f64>, factor: f64) {
    for i in 0..inf.nrows() {
        *inf.get_mut(i, 0) *= factor;
    }
}

/// Stack per-(g,t) influence columns into a single matrix aligned by original id indices.
#[must_use]
pub fn combine_influence_functions(
    influence_functions: &[(Mat<f64>, Vec<usize>)],
    n_unique_ids: usize,
) -> Mat<f64> {
    let n_results = influence_functions.len();
    let mut out = Mat::zeros(n_unique_ids, n_results);
    for (i, (inf, orig_idx)) in influence_functions.iter().enumerate() {
        for (j, &row_idx) in orig_idx.iter().enumerate() {
            *out.get_mut(row_idx, i) = *inf.get(j, 0);
        }
    }
    out
}
