use faer::Mat;

use crate::estimators::common::linalg::ridge_solve_spd;
use crate::estimators::outcome::model::OutcomeModel;

pub struct LinearOutcome {
    pub ridge: f64,
}

impl Default for LinearOutcome {
    fn default() -> Self {
        Self { ridge: 1e-8 }
    }
}

impl OutcomeModel for LinearOutcome {
    fn fit(&self, design: &Mat<f64>, target: &Mat<f64>, weights: Option<&[f64]>) -> Mat<f64> {
        weights.map_or_else(
            || {
                let a = design.transpose() * design;
                let b = design.transpose() * target;
                ridge_solve_spd(a, &b, self.ridge)
            },
            |wvec| {
                let x_t_w = design.transpose()
                    * &crate::estimators::common::weights::diag_sparse_from_vec(wvec);
                let a = &x_t_w * design;
                let b = &x_t_w * target;
                ridge_solve_spd(a, &b, self.ridge)
            },
        )
    }
    fn predict(&self, design: &Mat<f64>, beta: &Mat<f64>) -> Vec<f64> {
        let n = design.nrows();
        let mut out = Vec::with_capacity(n);
        for i in 0..n {
            let mut pred = 0.0;
            for j in 0..design.ncols() {
                pred += design.get(i, j) * beta.get(j, 0);
            }
            out.push(pred);
        }
        out
    }
}
