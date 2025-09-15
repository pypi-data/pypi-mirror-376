use faer::prelude::*;
use faer::Mat;

#[must_use]
pub fn ridge_solve_spd(mut a: Mat<f64>, b: &Mat<f64>, lambda: f64) -> Mat<f64> {
    for i in 0..a.ncols() {
        *a.get_mut(i, i) += lambda;
    }
    a.partial_piv_lu().solve(b)
}

#[must_use]
pub fn xt_w_x(x_t_w: &Mat<f64>, x: &Mat<f64>) -> Mat<f64> {
    x_t_w * x
}

#[must_use]
pub fn xt_w_b(x_t_w: &Mat<f64>, b: &Mat<f64>) -> Mat<f64> {
    x_t_w * b
}
