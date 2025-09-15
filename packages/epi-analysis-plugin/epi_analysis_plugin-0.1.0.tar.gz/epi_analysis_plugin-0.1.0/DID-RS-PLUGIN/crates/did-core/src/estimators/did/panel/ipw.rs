//! Inverse probability weighting estimator
use faer::Mat;

use crate::estimators::propensity::logistic::LogisticPS;
use crate::estimators::propensity::{Config, LossFunction, PropensityEstimator};
use crate::DidError;

pub struct IPWEstimator {
    x: Mat<f64>,
    d: Mat<f64>,
    loss: LossFunction,
}

impl IPWEstimator {
    #[must_use]
    pub const fn new(x_pscore: Mat<f64>, y_pscore: Mat<f64>, loss: LossFunction) -> Self {
        Self {
            x: x_pscore,
            d: y_pscore,
            loss,
        }
    }

    /// # Errors
    ///
    /// This function returns an error if the estimation fails.
    pub fn estimate(&self) -> Result<(f64, Mat<f64>), DidError> {
        let cfg = Config {
            loss: self.loss,
            ..Default::default()
        };
        let est = LogisticPS::new(cfg);
        let params = est.fit(&self.x, &self.d)?;

        let x_beta = &self.x * &params.beta;
        let mut p_hat = Mat::zeros(x_beta.nrows(), x_beta.ncols());
        for i in 0..x_beta.nrows() {
            for j in 0..x_beta.ncols() {
                *p_hat.get_mut(i, j) = 1.0 / (1.0 + (-x_beta.get(i, j)).exp());
            }
        }

        let y = &self.d;
        let att = {
            let outcome: Vec<f64> = (0..y.nrows()).map(|i| *y.get(i, 0)).collect();
            let treat: Vec<f64> = outcome.clone();
            let ps: Vec<f64> = (0..p_hat.nrows()).map(|i| *p_hat.get(i, 0)).collect();
            crate::estimators::common::weights::horvitz_thompson(&outcome, &treat, &ps)
        };

        Ok((att, Mat::zeros(self.x.nrows(), self.x.ncols())))
    }
}
