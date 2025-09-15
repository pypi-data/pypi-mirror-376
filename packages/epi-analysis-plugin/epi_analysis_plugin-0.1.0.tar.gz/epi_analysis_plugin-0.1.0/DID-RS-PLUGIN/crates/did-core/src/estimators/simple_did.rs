//! Simple 2x2 `DiD` estimator
use faer::prelude::*;
use faer::Mat;

use crate::DidError;

pub struct SimpleDidEstimator {
    x: Mat<f64>,
    y: Mat<f64>,
}

impl SimpleDidEstimator {
    #[must_use]
    pub const fn new(x: Mat<f64>, y: Mat<f64>) -> Self {
        Self { x, y }
    }

    /// # Errors
    ///
    /// This function returns an error if the estimation fails.
    pub fn estimate(&self) -> Result<(f64, Mat<f64>), DidError> {
        let beta = self.x.qr().solve(&self.y);

        let error = &self.y - &(&self.x * &beta);
        let influence_function = {
            let mut influence_function = Mat::zeros(self.x.nrows(), self.x.ncols());
            for i in 0..self.x.nrows() {
                for j in 0..self.x.ncols() {
                    *influence_function.get_mut(i, j) = self.x.get(i, j) * error.get(i, 0);
                }
            }
            influence_function
        };

        Ok((*beta.get(0, 0), influence_function))
    }
}
