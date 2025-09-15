//! Regression estimator
use faer::prelude::*;
use faer::Mat;

use crate::DidError;

pub struct REGEstimator {
    pub x: Mat<f64>,
    pub y: Mat<f64>,
    pub weights: Option<Mat<f64>>,
}

impl REGEstimator {
    #[must_use]
    pub const fn new(x: Mat<f64>, y: Mat<f64>, weights: Option<Mat<f64>>) -> Self {
        Self { x, y, weights }
    }

    /// # Errors
    ///
    /// This function returns an error if the estimation fails.
    ///
    /// # Panics
    ///
    /// This function will panic if the weights are not of the correct size.
    pub fn estimate(&self) -> Result<(f64, Mat<f64>), DidError> {
        let w = self
            .weights
            .clone()
            .unwrap_or_else(|| Mat::from_fn(self.x.nrows(), 1, |_, _| 1.0));
        let w_sparse = {
            let mut triplets = Vec::new();
            for i in 0..w.nrows() {
                triplets.push(faer::sparse::Triplet::new(i, i, *w.get(i, 0)));
            }
            faer::sparse::SparseColMat::<usize, f64>::try_new_from_triplets(
                w.nrows(),
                w.nrows(),
                &triplets,
            )
            .unwrap()
        };
        let x_t_w = self.x.transpose().as_ref() * &w_sparse;
        let x_t_w_x = &x_t_w * &self.x;
        let x_t_w_y = &x_t_w * &self.y;
        let beta = x_t_w_x.qr().solve(&x_t_w_y);

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
