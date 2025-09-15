//! Inverse Probability Weighted DID estimator for repeated cross sections
//! Implementation of Abadie (2005) IPW estimator

use faer::prelude::*;
use faer::Mat;
use itertools::izip;

use crate::estimators::propensity::logistic::LogisticPS;
use crate::estimators::propensity::{Config, LossFunction, PropensityEstimator};
use crate::DidError;

const FLOAT_EQ_EPSILON: f64 = 1e-10;

/// IPW `DiD` estimator for repeated cross sections data
///
/// This implements Abadie's (2005) inverse probability weighted estimator
/// for repeated cross-sectional data. The estimator is of the Horwitz-Thompson type
/// where IPW weights are NOT normalized to sum to one.
pub struct IPWRC {
    // Input data (stacked format: pre and post periods)
    y: Mat<f64>,          // Outcome variable
    post: Mat<f64>,       // Post-treatment indicator
    treatment: Mat<f64>,  // Treatment group indicator
    covariates: Mat<f64>, // Covariates including intercept
    weights: Mat<f64>,    // Sampling weights
    loss: LossFunction,
}

impl IPWRC {
    #[must_use]
    pub fn new(
        y: Mat<f64>,
        post: Mat<f64>,
        treatment: Mat<f64>,
        covariates: Mat<f64>,
        weights: Option<Mat<f64>>,
        loss: LossFunction,
    ) -> Self {
        let n = y.nrows();
        let weights = weights.unwrap_or_else(|| Mat::from_fn(n, 1, |_, _| 1.0));

        Self {
            y,
            post,
            treatment,
            covariates,
            weights,
            loss,
        }
    }

    /// Estimate ATT using IPW approach for repeated cross sections
    ///
    /// # Errors
    /// Returns `DidError` if:
    /// - Data validation fails (missing groups, invalid indicators)
    /// - Propensity score estimation fails
    /// - Matrix operations fail due to numerical issues
    pub fn estimate(&self) -> Result<(f64, Mat<f64>), DidError> {
        let n = self.y.nrows();

        // Pre-estimation checks
        self.validate_data()?;

        // Step 1: Normalize weights
        let weight_mean = self.weights.col_as_slice(0).iter().sum::<f64>() / n as f64;
        let normalized_weights: Vec<f64> = self
            .weights
            .col_as_slice(0)
            .iter()
            .map(|w| w / weight_mean)
            .collect();

        // Step 2: Estimate propensity scores (for treatment group membership)
        let cfg = Config {
            loss: self.loss,
            ..Default::default()
        };
        let est = LogisticPS::new(cfg);
        let params = est.fit(&self.covariates, &self.treatment)?;
        let ps_fit = self.compute_propensity_scores(&params.beta);

        // Step 3: Compute IPW ATT estimate
        let att = self.compute_ipw_att(&ps_fit, &normalized_weights)?;

        // Step 4: Compute influence function
        let influence_function =
            self.compute_influence_function(&ps_fit, &params.beta, &normalized_weights, att);

        Ok((att, influence_function))
    }

    /// Validate input data for repeated cross sections
    fn validate_data(&self) -> Result<(), DidError> {
        let treatment_vals = self.treatment.col_as_slice(0);
        let post_vals = self.post.col_as_slice(0);

        // Check we have treated and control units
        if !treatment_vals.contains(&1.0) {
            return Err(DidError::Estimation("No treated units found".to_string()));
        }
        if !treatment_vals.contains(&0.0) {
            return Err(DidError::Estimation("No control units found".to_string()));
        }

        // Check we have pre and post periods
        if !post_vals.contains(&1.0) {
            return Err(DidError::Estimation(
                "No post-treatment observations found".to_string(),
            ));
        }
        if !post_vals.contains(&0.0) {
            return Err(DidError::Estimation(
                "No pre-treatment observations found".to_string(),
            ));
        }

        // Check we have all four groups
        let mut group_counts = [0; 4];
        for i in 0..self.y.nrows() {
            let d_val = treatment_vals[i];
            let p_val = post_vals[i];

            // Validate that treatment and period are binary (0 or 1)
            if !(d_val.abs() < FLOAT_EQ_EPSILON || (d_val - 1.0).abs() < FLOAT_EQ_EPSILON) {
                return Err(DidError::Preprocessing(format!(
                    "Treatment indicator must be 0 or 1, found: {d_val}"
                )));
            }
            if !(p_val.abs() < FLOAT_EQ_EPSILON || (p_val - 1.0).abs() < FLOAT_EQ_EPSILON) {
                return Err(DidError::Preprocessing(format!(
                    "Period indicator must be 0 or 1, found: {p_val}"
                )));
            }

            let d = usize::from((d_val - 1.0).abs() < FLOAT_EQ_EPSILON);
            let p = usize::from((p_val - 1.0).abs() < FLOAT_EQ_EPSILON);
            group_counts[d * 2 + p] += 1;
        }

        for (i, &count) in group_counts.iter().enumerate() {
            if count == 0 {
                let group_name = match i {
                    0 => "control pre-treatment",
                    1 => "control post-treatment",
                    2 => "treated pre-treatment",
                    3 => "treated post-treatment",
                    _ => unreachable!(),
                };
                return Err(DidError::Estimation(format!(
                    "No observations in {group_name} group"
                )));
            }
        }

        Ok(())
    }

    /// Compute propensity scores from estimated coefficients
    fn compute_propensity_scores(&self, beta: &Mat<f64>) -> Vec<f64> {
        let n = self.y.nrows();
        let mut ps_fit = Vec::with_capacity(n);

        for i in 0..n {
            let mut linear_pred = 0.0;
            for j in 0..self.covariates.ncols() {
                linear_pred += self.covariates.get(i, j) * beta.get(j, 0);
            }

            // Apply logistic function
            let ps = 1.0 / (1.0 + (-linear_pred).exp());
            // Avoid extreme values (trim at 0.995 for controls)
            let trimmed_ps = ps.clamp(1e-6, 0.995);
            ps_fit.push(trimmed_ps);
        }

        ps_fit
    }

    /// Compute the IPW ATT estimate following Abadie (2005)
    ///
    /// The IPW estimator is:
    /// τ = E[Y₁(D=1,t=1)] - E[Y₁(D=1,t=0)] - E[Y₀(D=0,t=1)] + E[Y₀(D=0,t=0)]
    ///
    /// Where expectations are weighted by inverse propensity score weights
    fn compute_ipw_att(&self, ps_fit: &[f64], weights: &[f64]) -> Result<f64, DidError> {
        let n = self.y.nrows();
        let treatment_vals = self.treatment.col_as_slice(0);
        let post_vals = self.post.col_as_slice(0);
        let y_vals = self.y.col_as_slice(0);

        // Initialize weighted sums for each group
        let mut sum_treat_post = 0.0; // E[Y₁(D=1,t=1)]
        let mut sum_treat_pre = 0.0; // E[Y₁(D=1,t=0)]
        let mut sum_cont_post = 0.0; // E[Y₀(D=0,t=1)]
        let mut sum_cont_pre = 0.0; // E[Y₀(D=0,t=0)]

        let mut weight_treat_post = 0.0;
        let mut weight_treat_pre = 0.0;
        let mut weight_cont_post = 0.0;
        let mut weight_cont_pre = 0.0;

        // Compute IPW-weighted means for each group
        for i in 0..n {
            let d_val = treatment_vals[i];
            let post_val = post_vals[i];
            let y_val = y_vals[i];
            let ps_val = ps_fit[i];
            let w_val = weights[i];

            if (d_val - 1.0).abs() < FLOAT_EQ_EPSILON && (post_val - 1.0).abs() < FLOAT_EQ_EPSILON {
                let ipw_weight = w_val;
                sum_treat_post += ipw_weight * y_val;
                weight_treat_post += ipw_weight;
            } else if (d_val - 1.0).abs() < FLOAT_EQ_EPSILON && post_val.abs() < FLOAT_EQ_EPSILON {
                let ipw_weight = w_val;
                sum_treat_pre += ipw_weight * y_val;
                weight_treat_pre += ipw_weight;
            } else if d_val.abs() < FLOAT_EQ_EPSILON && (post_val - 1.0).abs() < FLOAT_EQ_EPSILON {
                let ipw_weight = w_val * ps_val / (1.0 - ps_val);
                sum_cont_post += ipw_weight * y_val;
                weight_cont_post += ipw_weight;
            } else if d_val == 0.0 && post_val == 0.0 {
                let ipw_weight = w_val * ps_val / (1.0 - ps_val);
                sum_cont_pre += ipw_weight * y_val;
                weight_cont_pre += ipw_weight;
            }
        }

        // Check for zero weights (would indicate no observations in some group)
        if weight_treat_post == 0.0
            || weight_treat_pre == 0.0
            || weight_cont_post == 0.0
            || weight_cont_pre == 0.0
        {
            return Err(DidError::Estimation(
                "One or more groups have zero total weight".to_string(),
            ));
        }

        // Compute group means
        let mean_treat_post = sum_treat_post / weight_treat_post;
        let mean_treat_pre = sum_treat_pre / weight_treat_pre;
        let mean_cont_post = sum_cont_post / weight_cont_post;
        let mean_cont_pre = sum_cont_pre / weight_cont_pre;

        // IPW DID estimate
        let ipw_att = (mean_treat_post - mean_treat_pre) - (mean_cont_post - mean_cont_pre);

        Ok(ipw_att)
    }

    /// Compute the influence function for the IPW estimator
    ///
    /// This involves the influence function of the propensity score estimation
    /// and the IPW reweighting scheme.
    fn compute_influence_function(
        &self,
        ps_fit: &[f64],
        _ps_beta: &Mat<f64>,
        weights: &[f64],
        _att_estimate: f64,
    ) -> Mat<f64> {
        let n = self.y.nrows();
        let k = self.covariates.ncols();
        let treatment_vals = self.treatment.col_as_slice(0);
        let post_vals = self.post.col_as_slice(0);
        let y_vals = self.y.col_as_slice(0);

        // Asymptotic linear representation of logit's beta's
        let asy_lin_rep_ps = self.asy_lin_rep_ps(ps_fit, weights);

        let ps_trimmed: Vec<f64> = izip!(treatment_vals, ps_fit)
            .map(|(&d, &ps)| if d == 0.0 { ps.min(0.995) } else { ps })
            .collect();

        let w_treat_pre: Vec<f64> = izip!(treatment_vals, post_vals, weights, &ps_trimmed)
            .map(|(&d, &p, &w, &ps)| ps * d * (1.0 - p) * w)
            .collect();
        let w_treat_post: Vec<f64> = izip!(treatment_vals, post_vals, weights, &ps_trimmed)
            .map(|(&d, &p, &w, &ps)| ps * d * p * w)
            .collect();
        let w_cont_pre: Vec<f64> = izip!(treatment_vals, post_vals, weights, &ps_trimmed)
            .map(|(&d, &p, &w, &ps)| ps * (1.0 - d) * (1.0 - p) * w / (1.0 - ps))
            .collect();
        let w_cont_post: Vec<f64> = izip!(treatment_vals, post_vals, weights, &ps_trimmed)
            .map(|(&d, &p, &w, &ps)| ps * (1.0 - d) * p * w / (1.0 - ps))
            .collect();

        let pi_hat = izip!(weights, &ps_trimmed, treatment_vals)
            .map(|(&w, &ps, &d)| w * ps * d)
            .sum::<f64>()
            / n as f64;
        let lambda_hat = izip!(weights, &ps_trimmed, post_vals)
            .map(|(&w, &ps, &p)| w * ps * p)
            .sum::<f64>()
            / n as f64;
        let one_minus_lambda_hat = izip!(weights, &ps_trimmed, post_vals)
            .map(|(&w, &ps, &p)| w * ps * (1.0 - p))
            .sum::<f64>()
            / n as f64;

        let eta_treat_pre: Vec<f64> = izip!(&w_treat_pre, y_vals)
            .map(|(&w, &y)| w * y / (pi_hat * one_minus_lambda_hat))
            .collect();
        let eta_treat_post: Vec<f64> = izip!(&w_treat_post, y_vals)
            .map(|(&w, &y)| w * y / (pi_hat * lambda_hat))
            .collect();
        let eta_cont_pre: Vec<f64> = izip!(&w_cont_pre, y_vals)
            .map(|(&w, &y)| w * y / (pi_hat * one_minus_lambda_hat))
            .collect();
        let eta_cont_post: Vec<f64> = izip!(&w_cont_post, y_vals)
            .map(|(&w, &y)| w * y / (pi_hat * lambda_hat))
            .collect();

        let att_treat_pre = eta_treat_pre.iter().sum::<f64>() / n as f64;
        let att_treat_post = eta_treat_post.iter().sum::<f64>() / n as f64;
        let att_cont_pre = eta_cont_pre.iter().sum::<f64>() / n as f64;
        let att_cont_post = eta_cont_post.iter().sum::<f64>() / n as f64;

        let inf_treat_post1: Vec<f64> = izip!(&eta_treat_post)
            .map(|&eta| eta - att_treat_post)
            .collect();
        let inf_treat_post2: Vec<f64> = izip!(weights, treatment_vals)
            .map(|(&w, &d)| -w.mul_add(d, -pi_hat) * att_treat_post / pi_hat)
            .collect();
        let inf_treat_post3: Vec<f64> = izip!(weights, post_vals)
            .map(|(&w, &p)| -w.mul_add(p, -lambda_hat) * att_treat_post / lambda_hat)
            .collect();
        let inf_treat_post: Vec<f64> = izip!(inf_treat_post1, inf_treat_post2, inf_treat_post3)
            .map(|(a, b, c)| a + b + c)
            .collect();

        let inf_treat_pre1: Vec<f64> = izip!(&eta_treat_pre)
            .map(|&eta| eta - att_treat_pre)
            .collect();
        let inf_treat_pre2: Vec<f64> = izip!(weights, treatment_vals)
            .map(|(&w, &d)| -w.mul_add(d, -pi_hat) * att_treat_pre / pi_hat)
            .collect();
        let inf_treat_pre3: Vec<f64> = izip!(weights, post_vals)
            .map(|(&w, &p)| {
                -w.mul_add(1.0 - p, -one_minus_lambda_hat) * att_treat_pre / one_minus_lambda_hat
            })
            .collect();
        let inf_treat_pre_total: Vec<f64> = izip!(inf_treat_pre1, inf_treat_pre2, inf_treat_pre3)
            .map(|(a, b, c)| a + b + c)
            .collect();

        let inf_cont_post1: Vec<f64> = izip!(&eta_cont_post)
            .map(|&eta| eta - att_cont_post)
            .collect();
        let inf_cont_post2: Vec<f64> = izip!(weights, treatment_vals)
            .map(|(&w, &d)| -w.mul_add(d, -pi_hat) * att_cont_post / pi_hat)
            .collect();
        let inf_cont_post3: Vec<f64> = izip!(weights, post_vals)
            .map(|(&w, &p)| -w.mul_add(p, -lambda_hat) * att_cont_post / lambda_hat)
            .collect();
        let inf_cont_post: Vec<f64> = izip!(inf_cont_post1, inf_cont_post2, inf_cont_post3)
            .map(|(a, b, c)| a + b + c)
            .collect();

        let inf_cont_pre1: Vec<f64> = izip!(&eta_cont_pre)
            .map(|&eta| eta - att_cont_pre)
            .collect();
        let inf_cont_pre2: Vec<f64> = izip!(weights, treatment_vals)
            .map(|(&w, &d)| -w.mul_add(d, -pi_hat) * att_cont_pre / pi_hat)
            .collect();
        let inf_cont_pre3: Vec<f64> = izip!(weights, post_vals)
            .map(|(&w, &p)| {
                -w.mul_add(1.0 - p, -one_minus_lambda_hat) * att_cont_pre / one_minus_lambda_hat
            })
            .collect();
        let inf_cont_pre_total: Vec<f64> = izip!(inf_cont_pre1, inf_cont_pre2, inf_cont_pre3)
            .map(|(a, b, c)| a + b + c)
            .collect();

        let mut mom_logit_pre: Mat<f64> = Mat::zeros(k, 1);
        for (i, &eta) in eta_cont_pre.iter().enumerate().take(n) {
            for j in 0..k {
                *mom_logit_pre.get_mut(j, 0) -= eta * self.covariates.get(i, j);
            }
        }
        mom_logit_pre /= n as f64;

        let mut mom_logit_post: Mat<f64> = Mat::zeros(k, 1);
        for (i, &eta) in eta_cont_post.iter().enumerate().take(n) {
            for j in 0..k {
                *mom_logit_post.get_mut(j, 0) -= eta * self.covariates.get(i, j);
            }
        }
        mom_logit_post /= n as f64;

        let inf_logit = &asy_lin_rep_ps * (mom_logit_post - mom_logit_pre);

        let att_inf_func_vec: Vec<f64> = izip!(
            inf_treat_post,
            inf_treat_pre_total,
            inf_cont_post,
            inf_cont_pre_total,
            inf_logit.col_as_slice(0)
        )
        .map(|(a, b, c, d, e)| (a - b) - (c - d) + e)
        .collect();

        Mat::from_fn(n, 1, |r, _| att_inf_func_vec[r])
    }

    fn asy_lin_rep_ps(&self, ps_fit: &[f64], weights: &[f64]) -> Mat<f64> {
        let n = self.y.nrows();
        let k = self.covariates.ncols();
        let treatment_vals = self.treatment.col_as_slice(0);

        let w: Vec<f64> = izip!(ps_fit, weights)
            .map(|(&ps, &w)| ps * (1.0 - ps) * w)
            .collect();

        let mut hessian: Mat<f64> = Mat::zeros(k, k);
        for (i, &weight) in w.iter().enumerate().take(n) {
            for j in 0..k {
                for l in 0..k {
                    *hessian.get_mut(j, l) +=
                        weight * self.covariates.get(i, j) * self.covariates.get(i, l);
                }
            }
        }
        let hessian_inv = (hessian / n as f64).qr().solve(&Mat::identity(k, k));

        let mut score_ps = Mat::zeros(n, k);
        for i in 0..n {
            let score_i = (treatment_vals[i] - ps_fit[i]) * weights[i];
            for j in 0..k {
                *score_ps.get_mut(i, j) = score_i * self.covariates.get(i, j);
            }
        }

        &score_ps * &hessian_inv
    }
}
