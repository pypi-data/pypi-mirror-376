//! Doubly robust DID estimator
use faer::prelude::*;
use faer::Mat;

use crate::estimators::outcome::model::OutcomeModel;
use crate::estimators::propensity::logistic::LogisticPS;
use crate::estimators::propensity::{Config, LossFunction, PropensityEstimator};
use crate::DidError;
// use statrs::distribution::{ContinuousCDF, Normal};

/// Parameters for influence function computation
#[derive(Copy, Clone)]
struct InfluenceParams<'a> {
    w_treat: &'a [f64],
    w_cont: &'a [f64],
    dr_att_treat: &'a [f64],
    dr_att_cont: &'a [f64],
    eta_treat: f64,
    eta_cont: f64,
    mean_w_treat: f64,
    mean_w_cont: f64,
    ps_fit: &'a [f64],
    out_delta: &'a [f64],
    weights: &'a [f64],
}

pub struct DRDID {
    // Input data
    delta_y: Mat<f64>,
    treatment: Mat<f64>,  // D variable
    covariates: Mat<f64>, // Including intercept
    weights: Mat<f64>,
    loss: LossFunction,
}

impl DRDID {
    #[must_use]
    pub fn new(
        x_pscore: &Mat<f64>, // covariates for propensity score
        y_pscore: Mat<f64>,  // treatment indicator
        _x_reg: Mat<f64>,    // covariates for regression (will be ignored in panel version)
        y_reg: Mat<f64>,     // delta_y (outcome differences)
        loss: LossFunction,
    ) -> Self {
        let n = y_reg.nrows();
        let weights = Mat::from_fn(n, 1, |_, _| 1.0);

        // Create covariates matrix with intercept if needed
        let mut covariates = Mat::zeros(n, x_pscore.ncols());
        for i in 0..n {
            for j in 0..x_pscore.ncols() {
                *covariates.get_mut(i, j) = *x_pscore.get(i, j);
            }
        }

        Self {
            delta_y: y_reg,
            treatment: y_pscore,
            covariates,
            weights,
            loss,
        }
    }

    /// Panel data DRDID based on Python implementation
    ///
    /// # Errors
    /// Returns `DidError` if:
    /// - There are no control or treated units in the data
    /// - Propensity score estimation fails
    /// - Matrix operations fail due to singularity or numerical issues
    pub fn estimate_panel(&self) -> Result<(f64, Mat<f64>), DidError> {
        let n = self.delta_y.nrows();

        // Pre-estimation checks for control and treated units
        let has_controls = self.treatment.col_as_slice(0).contains(&0.0);
        let has_treated = self.treatment.col_as_slice(0).contains(&1.0);

        if !has_treated {
            return Err(DidError::Estimation(
                "No treated units in estimation sample".to_string(),
            ));
        }

        if !has_controls {
            return Err(DidError::Estimation(
                "No control units available for outcome regression".to_string(),
            ));
        }

        // Step 1: Normalize weights
        let weight_mean = self.weights.col_as_slice(0).iter().sum::<f64>() / n as f64;
        let normalized_weights: Vec<f64> = self
            .weights
            .col_as_slice(0)
            .iter()
            .map(|w| w / weight_mean)
            .collect();

        // Step 2: Estimate propensity scores
        let cfg = Config {
            loss: self.loss,
            ..Default::default()
        };
        let est = LogisticPS::new(cfg);
        let params = est.fit(&self.covariates, &self.treatment)?;
        let ps_beta_vec: Vec<f64> = params.beta.col_as_slice(0).to_vec();
        let ps_fit = self.compute_propensity_scores(&ps_beta_vec);

        // Step 3: Outcome regression for control group (mask = D == 0)
        let control_mask: Vec<bool> = self
            .treatment
            .col_as_slice(0)
            .iter()
            .map(|&d| d == 0.0)
            .collect();

        let (control_indices, control_weights): (Vec<usize>, Vec<f64>) = control_mask
            .iter()
            .enumerate()
            .filter_map(|(i, &is_control)| {
                if is_control {
                    Some((i, normalized_weights[i]))
                } else {
                    None
                }
            })
            .unzip();

        // control_indices should not be empty due to earlier check, but keep as safety net
        if control_indices.is_empty() {
            return Err(DidError::Estimation(
                "No control units available for outcome regression".to_string(),
            ));
        }

        let x_control = Mat::from_fn(control_indices.len(), self.covariates.ncols(), |r, c| {
            *self.covariates.get(control_indices[r], c)
        });
        let y_control = Mat::from_fn(control_indices.len(), 1, |r, _| {
            *self.delta_y.get(control_indices[r], 0)
        });

        let outcome = crate::estimators::outcome::linear::LinearOutcome::default();
        let reg_coeffs = outcome.fit(&x_control, &y_control, Some(&control_weights));
        let out_delta: Vec<f64> = (0..n)
            .map(|i| {
                let mut pred = 0.0;
                for j in 0..self.covariates.ncols() {
                    pred += self.covariates.get(i, j) * reg_coeffs.get(j, 0);
                }
                pred
            })
            .collect();

        // Step 4: Compute Traditional Doubly Robust DiD estimators (Python formula)
        let w_treat: Vec<f64> = (0..n)
            .map(|i| normalized_weights[i] * self.treatment.get(i, 0))
            .collect();

        let w_cont: Vec<f64> = (0..n)
            .map(|i| {
                let d = self.treatment.get(i, 0);
                let ps = ps_fit[i].min(1.0 - 1e-16);
                normalized_weights[i] * ps * (1.0 - d) / (1.0 - ps).max(1e-16)
            })
            .collect();

        let dr_att_treat: Vec<f64> = (0..n)
            .map(|i| w_treat[i] * (self.delta_y.get(i, 0) - out_delta[i]))
            .collect();

        let dr_att_cont: Vec<f64> = (0..n)
            .map(|i| w_cont[i] * (self.delta_y.get(i, 0) - out_delta[i]))
            .collect();

        // Python: eta_treat = np.mean(dr_att_treat) / np.mean(w_treat)
        // Python: eta_cont = np.mean(dr_att_cont) / np.mean(w_cont)
        let mean_w_treat = w_treat.iter().sum::<f64>() / n as f64;
        let mean_w_cont = w_cont.iter().sum::<f64>() / n as f64;

        let sum_dr_att_treat = dr_att_treat.iter().sum::<f64>() / n as f64;
        let sum_dr_att_cont = dr_att_cont.iter().sum::<f64>() / n as f64;

        let eta_treat = sum_dr_att_treat / mean_w_treat;
        let eta_cont = sum_dr_att_cont / mean_w_cont;

        let dr_att = eta_treat - eta_cont;

        // Step 5: Compute complete influence function (Python-style)
        let influence_func = self.compute_influence_function(InfluenceParams {
            w_treat: &w_treat,
            w_cont: &w_cont,
            dr_att_treat: &dr_att_treat,
            dr_att_cont: &dr_att_cont,
            eta_treat,
            eta_cont,
            mean_w_treat,
            mean_w_cont,
            ps_fit: &ps_fit,
            out_delta: &out_delta,
            weights: &normalized_weights,
        });

        Ok((dr_att, influence_func))
    }

    /// Legacy estimate method for backward compatibility
    ///
    /// # Errors
    /// Returns `DidError` if the underlying panel estimation fails
    pub fn estimate(&self) -> Result<(f64, Mat<f64>), DidError> {
        self.estimate_panel()
    }

    /// Compute propensity scores from estimated coefficients
    fn compute_propensity_scores(&self, beta: &[f64]) -> Vec<f64> {
        let n = self.covariates.nrows();
        let mut scores = Vec::with_capacity(n);

        for i in 0..n {
            let mut linear_pred = 0.0;
            for (j, &beta_j) in beta.iter().enumerate().take(self.covariates.ncols()) {
                linear_pred += self.covariates.get(i, j) * beta_j;
            }
            // Apply logistic transformation with numerical stability
            let score = 1.0 / (1.0 + (-linear_pred.clamp(-700.0, 700.0)).exp());
            scores.push(score);
        }

        scores
    }

    /// Compute complete influence function following Python implementation
    fn compute_influence_function(&self, params: InfluenceParams<'_>) -> Mat<f64> {
        let n = self.delta_y.nrows();
        let p = self.covariates.ncols();

        // 1. Compute OLS asymptotic linear representation (asy_lin_rep_wols)
        // This follows: wols_eX * inv(X'WX/n) where W are control unit weights
        let control_mask: Vec<bool> = self
            .treatment
            .col_as_slice(0)
            .iter()
            .map(|&d| d == 0.0)
            .collect();

        // Build weighted matrices for control units only
        let mut xtw_x = Mat::<f64>::zeros(p, p); // X'WX
        let mut wols_ex = Mat::<f64>::zeros(n, p); // weighted residuals * X for all units

        for (i, &is_control) in control_mask.iter().enumerate() {
            let residual = self.delta_y.get(i, 0) - params.out_delta[i];
            let weight = if is_control { params.weights[i] } else { 0.0 };

            // wols_eX for all units (but weighted by control status)
            for j in 0..p {
                *wols_ex.get_mut(i, j) = weight * residual * self.covariates.get(i, j);
            }

            // X'WX only for control units
            if is_control {
                for j in 0..p {
                    for k in 0..p {
                        *xtw_x.get_mut(j, k) +=
                            self.covariates.get(i, j) * weight * self.covariates.get(i, k);
                    }
                }
            }
        }

        // XpX_inv = inv(X'WX / n) with numerical stability
        let mut xtw_x_scaled = xtw_x / (n as f64);

        // Add small regularization for numerical stability
        for i in 0..p {
            *xtw_x_scaled.get_mut(i, i) += 1e-12;
        }

        // Solve for inverse
        let identity = Mat::<f64>::identity(p, p);
        let xtw_x_inv = xtw_x_scaled.qr().solve(&identity);
        let asy_lin_rep_wols = &wols_ex * &xtw_x_inv;

        // 2. Compute propensity score asymptotic linear representation
        let mut score_ps = Mat::<f64>::zeros(n, p);
        for i in 0..n {
            let ps_residual = self.treatment.get(i, 0) - params.ps_fit[i];
            for j in 0..p {
                *score_ps.get_mut(i, j) =
                    params.weights[i] * ps_residual * self.covariates.get(i, j);
            }
        }

        // Build proper Hessian: -E[∇²ℓ] = E[X'diag(ps*(1-ps))X]
        let mut hessian_ps = Mat::<f64>::zeros(p, p);
        for i in 0..n {
            let ps_var = params.ps_fit[i] * (1.0 - params.ps_fit[i]);
            for j in 0..p {
                for k in 0..p {
                    *hessian_ps.get_mut(j, k) += params.weights[i]
                        * ps_var
                        * self.covariates.get(i, j)
                        * self.covariates.get(i, k);
                }
            }
        }
        let mut hessian_ps = hessian_ps / (n as f64);

        // Add regularization for stability
        for i in 0..p {
            *hessian_ps.get_mut(i, i) += 1e-12;
        }

        let hessian_ps_inv = hessian_ps.qr().solve(&Mat::<f64>::identity(p, p));
        let asy_lin_rep_ps = &score_ps * &hessian_ps_inv;

        // 3. Compute moment matrices
        let mut m1 = vec![0.0; p]; // mean(w_treat * X)
        let mut m2 = vec![0.0; p]; // mean(w_cont * (deltaY - out_delta - eta_cont) * X)
        let mut m3 = vec![0.0; p]; // mean(w_cont * X)

        for i in 0..n {
            for j in 0..p {
                m1[j] += params.w_treat[i] * self.covariates.get(i, j);
                m3[j] += params.w_cont[i] * self.covariates.get(i, j);

                let term = self.delta_y.get(i, 0) - params.out_delta[i] - params.eta_cont;
                m2[j] += params.w_cont[i] * term * self.covariates.get(i, j);
            }
        }

        // Normalize by sample size
        for j in 0..p {
            m1[j] /= n as f64;
            m2[j] /= n as f64;
            m3[j] /= n as f64;
        }

        // 4. Compute final influence function
        let mut influence_func = Mat::<f64>::zeros(n, 1);

        for i in 0..n {
            // Basic influence terms
            let inf_treat_1 = params.w_treat[i].mul_add(-params.eta_treat, params.dr_att_treat[i]);
            let inf_cont_1 = params.w_cont[i].mul_add(-params.eta_cont, params.dr_att_cont[i]);

            // Correction terms from OLS uncertainty
            let inf_treat_2: f64 = (0..p).map(|j| asy_lin_rep_wols.get(i, j) * m1[j]).sum();
            let inf_cont_3: f64 = (0..p).map(|j| asy_lin_rep_wols.get(i, j) * m3[j]).sum();

            // Correction term from propensity score uncertainty
            let inf_cont_2: f64 = m2
                .iter()
                .enumerate()
                .map(|(j, &m2_val)| asy_lin_rep_ps.get(i, j) * m2_val)
                .sum();

            // Combine all terms (following Python exactly)
            let inf_treat = (inf_treat_1 - inf_treat_2) / params.mean_w_treat;
            let inf_control = (inf_cont_1 + inf_cont_2 - inf_cont_3) / params.mean_w_cont;

            *influence_func.get_mut(i, 0) = inf_treat - inf_control;
        }

        influence_func
    }
}

impl crate::estimators::traits::Estimator for DRDID {
    fn estimate(&self) -> Result<crate::estimators::types::EstResult, crate::DidError> {
        let (att, inf) = self.estimate_panel()?;
        Ok(crate::estimators::types::EstResult { att, inf })
    }
}
