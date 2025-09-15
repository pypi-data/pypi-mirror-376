use faer::Mat;
use log::debug;

#[must_use]
pub fn safe_sigmoid(v: f64) -> f64 {
    let z = v.clamp(-700.0, 700.0);
    1.0 / (1.0 + (-z).exp())
}

#[must_use]
pub fn empirical_logit(y: &Mat<f64>) -> f64 {
    let y_mean = y.col_as_slice(0).iter().sum::<f64>() / y.nrows() as f64;
    if y_mean <= 0.001 {
        -6.907
    } else if y_mean >= 0.999 {
        6.907
    } else {
        (y_mean / (1.0 - y_mean)).ln()
    }
}

pub fn debug_matrix_ranges(name: &str, m: &Mat<f64>) {
    debug!(
        "{} range = [{:.6}, {:.6}]",
        name,
        m.col_as_slice(0)
            .iter()
            .fold(f64::INFINITY, |a, &b| a.min(b)),
        m.col_as_slice(0)
            .iter()
            .fold(f64::NEG_INFINITY, |a, &b| a.max(b))
    );
}
