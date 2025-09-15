use faer::Mat;

use crate::DidError;

pub trait PropensityEstimator {
    fn fit(&self, x: &Mat<f64>, d: &Mat<f64>) -> Result<Params, DidError>;
}

use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
pub enum LossFunction {
    Logistic,
    Tan2019,
    Graham2012,
}

#[derive(Clone, Debug)]
pub struct Config {
    pub max_iter: u64,
    pub tol: f64,
    pub min_weight: f64,
    pub vstar: f64,
    pub loss: LossFunction,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            max_iter: 100,
            tol: 1e-6,
            min_weight: 1e-10,
            vstar: 700.0,
            loss: LossFunction::Logistic,
        }
    }
}

#[derive(Clone, Debug)]
pub struct Params {
    pub beta: Mat<f64>,
}
