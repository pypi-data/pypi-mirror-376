use faer::linalg::solvers::DenseSolveCore;
use faer::Mat;
use log::debug;

use super::ipt::ipt_loss_grad_hess;
use super::trust::fit_trust;
use super::{Config, Params, PropensityEstimator};
use crate::estimators::propensity::irls::irls;
use crate::DidError;

pub struct LogisticPS {
    pub cfg: Config,
}

impl LogisticPS {
    #[must_use]
    pub const fn new(cfg: Config) -> Self {
        Self { cfg }
    }
}

impl PropensityEstimator for LogisticPS {
    fn fit(&self, design: &Mat<f64>, target: &Mat<f64>) -> Result<Params, DidError> {
        let beta0 = initial_beta(design, target);
        let beta = if let Ok(b) = fit_trust(design, target, &beta0, self.cfg.max_iter, self.cfg.tol)
        {
            debug!("Trust method succeeded");
            b
        } else {
            debug!("Trust failed; trying IPT");
            let mut b = beta0.clone();
            for _ in 0..self.cfg.max_iter {
                let (_loss, g, h) = ipt_loss_grad_hess(design, target, &b, self.cfg.vstar);
                let delta = h.qr().inverse() * &g;
                let new_b = &b - &delta;
                if delta.norm_l2() < self.cfg.tol {
                    b = new_b;
                    break;
                }
                b = new_b;
            }
            if b.norm_l2().is_finite() {
                b
            } else {
                irls(
                    design,
                    target,
                    self.cfg.max_iter,
                    self.cfg.tol,
                    self.cfg.min_weight,
                )?
            }
        };
        Ok(Params { beta })
    }
}

fn initial_beta(x: &Mat<f64>, d: &Mat<f64>) -> Mat<f64> {
    let mut b = Mat::zeros(x.ncols(), 1);
    let y_mean = d.col_as_slice(0).iter().sum::<f64>() / d.nrows() as f64;
    let emp = if y_mean <= 0.001 {
        -6.907
    } else if y_mean >= 0.999 {
        6.907
    } else {
        (y_mean / (1.0 - y_mean)).ln()
    };
    *b.get_mut(0, 0) = emp;
    b
}
