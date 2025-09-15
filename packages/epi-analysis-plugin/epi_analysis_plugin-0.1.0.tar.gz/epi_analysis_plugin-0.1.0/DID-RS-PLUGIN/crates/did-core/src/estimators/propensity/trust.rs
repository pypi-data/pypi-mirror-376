use faer::linalg::solvers::DenseSolveCore;
use faer::Mat;
use log::debug;

use crate::DidError;

#[must_use]
pub fn trust_loss_grad_hess(
    x: &Mat<f64>,
    d: &Mat<f64>,
    beta: &Mat<f64>,
) -> (f64, Mat<f64>, Mat<f64>) {
    let n = x.nrows();
    let p = x.ncols();
    let x_beta = x * beta;
    let iw = 1.0 / (n as f64);

    let mut loss = 0.0;
    let mut gradient = Mat::zeros(p, 1);
    let mut hessian = Mat::zeros(p, p);

    for i in 0..n {
        let ps_ind = *x_beta.get(i, 0);
        let di = *d.get(i, 0);
        let xi = x.row(i);

        let loss_contrib = if (di - 1.0).abs() < f64::EPSILON {
            ps_ind * iw
        } else {
            -ps_ind.exp() * iw
        };
        loss -= loss_contrib;

        let grad_contrib = if (di - 1.0).abs() < f64::EPSILON {
            -iw
        } else {
            ps_ind.exp() * iw
        };
        for j in 0..p {
            *gradient.get_mut(j, 0) += grad_contrib * xi.get(j);
        }

        let hess_contrib = if (di - 1.0).abs() < f64::EPSILON {
            0.0
        } else {
            ps_ind.exp() * iw
        };
        for j in 0..p {
            for k in 0..p {
                *hessian.get_mut(j, k) += hess_contrib * xi.get(j) * xi.get(k);
            }
        }
    }
    (loss, gradient, hessian)
}

pub fn fit_trust(
    x: &Mat<f64>,
    d: &Mat<f64>,
    beta0: &Mat<f64>,
    max_iter: u64,
    tol: f64,
) -> Result<Mat<f64>, DidError> {
    let mut beta = beta0.clone();
    for iter in 0..max_iter {
        let (loss, grad, mut hess) = trust_loss_grad_hess(x, d, &beta);
        if iter % 10 == 0 {
            debug!("Trust Iteration {iter}: loss = {loss:.6e}");
        }
        let reg = 1e-8;
        for i in 0..hess.ncols() {
            *hess.get_mut(i, i) += reg;
        }
        let delta = hess.qr().inverse() * &grad;
        let beta_new = &beta - &delta;
        if delta.norm_l2() < tol {
            return Ok(beta_new);
        }
        beta = beta_new;
    }
    Err(DidError::Convergence("Trust did not converge".to_string()))
}
