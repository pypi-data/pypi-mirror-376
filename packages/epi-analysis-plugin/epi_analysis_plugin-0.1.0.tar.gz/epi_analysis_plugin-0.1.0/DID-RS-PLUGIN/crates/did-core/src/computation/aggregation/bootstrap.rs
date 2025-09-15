use faer::Mat;

use crate::inference::bootstrap::MultiplierBootstrap;

#[must_use]
pub fn uniform_band_critical(inf: &Mat<f64>, att: f64) -> f64 {
    let bootstrap = MultiplierBootstrap::new(1000, None, None);
    let (low, _) = bootstrap.compute_uniform_bands(inf, &[att]);
    att - low[0]
}
