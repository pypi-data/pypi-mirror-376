use faer::linalg::solvers::DenseSolveCore;
use faer::prelude::*;
use statrs::distribution::{ChiSquared, ContinuousCDF};

use crate::{DidError, DidResult};

pub struct ParallelTrendsTest {
    pub test_statistic: f64,
    pub p_value: f64,
    pub critical_values: Vec<f64>,
    pub reject_null: bool,
}

impl DidResult {
    /// # Errors
    ///
    /// This function returns an error if there are no pre-treatment periods.
    ///
    /// # Panics
    ///
    /// This function will panic if the chi-squared distribution cannot be created.
    pub fn test_parallel_trends(&self) -> Result<ParallelTrendsTest, DidError> {
        let pre_treatment_att_indices = self
            .att_gt
            .iter()
            .enumerate()
            .filter(|(_, r)| r.time < r.group)
            .map(|(i, _)| i)
            .collect::<Vec<_>>();

        if pre_treatment_att_indices.is_empty() {
            return Err(DidError::Specification(
                "No pre-treatment periods found".to_string(),
            ));
        }

        let pre_treatment_att = pre_treatment_att_indices
            .iter()
            .map(|&i| self.att_gt[i].clone())
            .collect::<Vec<_>>();

        let beta = Mat::from_fn(pre_treatment_att.len(), 1, |r, _| pre_treatment_att[r].att);

        let n_pre_treatment = pre_treatment_att_indices.len();
        let mut influence = Mat::zeros(self.influence_function.nrows(), n_pre_treatment);

        for (j, &i) in pre_treatment_att_indices.iter().enumerate() {
            influence
                .as_mut()
                .col_mut(j)
                .copy_from(&self.influence_function.as_ref().col(i));
        }

        let v_inv = (influence.transpose() * &influence / influence.nrows() as f64)
            .qr()
            .inverse();
        let wald = (beta.transpose() * &v_inv * &beta).get(0, 0) / pre_treatment_att.len() as f64;

        let chi2 = ChiSquared::new(pre_treatment_att.len() as f64).unwrap();
        let p_value = 1.0 - chi2.cdf(wald);
        let critical_value = chi2.inverse_cdf(0.95);

        Ok(ParallelTrendsTest {
            test_statistic: wald,
            p_value,
            critical_values: vec![critical_value],
            reject_null: wald > critical_value,
        })
    }
}
