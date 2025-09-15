//! Doubly robust DID estimator for repeated cross sections
//! Implementation of Sant'Anna and Zhao (2020) equation (3.4)

use faer::prelude::*;
use faer::Mat;
use itertools::izip;

use crate::estimators::outcome::model::OutcomeModel;
use crate::estimators::propensity::logistic::LogisticPS;
use crate::estimators::propensity::{Config, LossFunction, PropensityEstimator};
use crate::DidError;

const FLOAT_EQ_EPSILON: f64 = 1e-10;

/// Doubly Robust `DiD` estimator for repeated cross sections data
///
/// This implements the locally efficient doubly robust estimator from
/// Sant'Anna and Zhao (2020) equation (3.4) for repeated cross-sectional data.
///
/// Key differences from panel version:
/// - Uses separate outcome regressions for treated/control in pre/post periods
/// - More complex influence function construction
/// - Different identification strategy based on repeated cross sections
pub struct DRDIDRC {
    // Input data (stacked format: pre and post periods)
    y: Mat<f64>,          // Outcome variable
    post: Mat<f64>,       // Post-treatment indicator
    treatment: Mat<f64>,  // Treatment group indicator
    covariates: Mat<f64>, // Covariates including intercept
    weights: Mat<f64>,    // Sampling weights
    loss: LossFunction,
}

impl DRDIDRC {
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

    /// Estimate ATT using doubly robust approach for repeated cross sections
    ///
    /// # Errors
    /// Returns `DidError` if:
    /// - Data validation fails (missing groups, invalid indicators)
    /// - Propensity score estimation fails
    /// - Outcome regression fails due to singularity
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

        // Step 3: Estimate outcome regressions for all four groups
        let reg_coeffs = self.estimate_outcome_regressions(&normalized_weights)?;

        // Step 4: Compute predicted outcomes
        let predicted_outcomes = self.compute_predicted_outcomes(&reg_coeffs);

        // Step 5: Compute DR-DiD estimate
        let att = self.compute_att_estimate(&ps_fit, &predicted_outcomes, &normalized_weights);

        // Step 6: Compute influence function
        let influence_function =
            self.compute_influence_function(&ps_fit, &predicted_outcomes, &normalized_weights);

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

        // Check we have all four groups: (D=0,post=0), (D=0,post=1), (D=1,post=0), (D=1,post=1)
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

    /// Estimate outcome regressions for all four groups
    /// Returns coefficients for: [`control_pre`, `control_post`, `treated_pre`, `treated_post`]
    fn estimate_outcome_regressions(&self, weights: &[f64]) -> Result<[Mat<f64>; 4], DidError> {
        let mut coefficients = Vec::new();

        // Define the four groups: (D, post) combinations
        let groups = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)];

        for &(d_val, post_val) in &groups {
            // Filter observations for this group
            let mut group_indices = Vec::new();
            let treatment_vals = self.treatment.col_as_slice(0);
            let post_vals = self.post.col_as_slice(0);

            for i in 0..self.y.nrows() {
                if (treatment_vals[i] - d_val).abs() < 1e-10
                    && (post_vals[i] - post_val).abs() < 1e-10
                {
                    group_indices.push(i);
                }
            }

            if group_indices.is_empty() {
                return Err(DidError::Estimation(format!(
                    "No observations for group D={d_val}, post={post_val}"
                )));
            }

            // Create design matrix and outcome vector for this group
            let n_group = group_indices.len();
            let k = self.covariates.ncols();

            let mut x_group = Mat::zeros(n_group, k);
            let mut y_group = Mat::zeros(n_group, 1);
            let mut w_group = Vec::with_capacity(n_group);

            for (j, &idx) in group_indices.iter().enumerate() {
                // Copy covariates
                for col in 0..k {
                    *x_group.get_mut(j, col) = *self.covariates.get(idx, col);
                }
                // Copy outcome
                *y_group.get_mut(j, 0) = *self.y.get(idx, 0);
                // Copy weight
                w_group.push(weights[idx]);
            }

            let outcome = crate::estimators::outcome::linear::LinearOutcome::default();
            let reg_coeff = outcome.fit(&x_group, &y_group, Some(&w_group));
            coefficients.push(reg_coeff);
        }

        Ok([
            coefficients[0].clone(), // control_pre
            coefficients[1].clone(), // control_post
            coefficients[2].clone(), // treated_pre
            coefficients[3].clone(), // treated_post
        ])
    }

    // /// Perform weighted ordinary least squares
    // fn weighted_ols(
    //     design_matrix: &Mat<f64>,
    //     outcome_vector: &Mat<f64>,
    //     weights: &[f64],
    // ) -> Result<Mat<f64>, DidError> {
    //     let num_obs = design_matrix.nrows();
    //     let num_vars = design_matrix.ncols();

    //     // Create weighted design matrix: W^{1/2}X
    //     let mut weighted_x = Mat::zeros(num_obs, num_vars);
    //     let mut weighted_y = Mat::zeros(num_obs, 1);

    //     for (i, &weight) in weights.iter().enumerate().take(num_obs) {
    //         let sqrt_weight = weight.sqrt();
    //         for j in 0..num_vars {
    //             *weighted_x.get_mut(i, j) = sqrt_weight * design_matrix.get(i, j);
    //         }
    //         *weighted_y.get_mut(i, 0) = sqrt_weight * outcome_vector.get(i, 0);
    //     }

    //     // Compute X'WX = (WX)'(WX)
    //     let x_transpose_x = weighted_x.transpose() * &weighted_x;

    //     // Check for singularity
    //     let singular_values = x_transpose_x.singular_values()?;
    //     if singular_values.is_empty() {
    //         return Err(DidError::Estimation(
    //             "Singular value computation failed.".to_string(),
    //         ));
    //     }
    //     let condition_number = singular_values[0] / singular_values[singular_values.len() - 1];
    //     if condition_number > 1e12 {
    //         return Err(DidError::Estimation(
    //             "Design matrix is near-singular. Consider removing collinear covariates."
    //                 .to_string(),
    //         ));
    //     }

    //     // Solve: β = (X'WX)^(-1) X'Wy
    //     let x_transpose_y = weighted_x.transpose() * &weighted_y;
    //     let beta = x_transpose_x.qr().solve(&x_transpose_y);

    //     Ok(beta)
    // }

    /// Compute predicted outcomes for all observations using the regression coefficients
    fn compute_predicted_outcomes(&self, reg_coeffs: &[Mat<f64>; 4]) -> [Vec<f64>; 4] {
        let n = self.y.nrows();
        let mut predicted = [
            Vec::with_capacity(n),
            Vec::with_capacity(n),
            Vec::with_capacity(n),
            Vec::with_capacity(n),
        ];

        // For each observation, compute predicted outcome under each of the four scenarios
        for i in 0..n {
            for (j, reg_coeff) in reg_coeffs.iter().enumerate() {
                let mut pred = 0.0;
                for k in 0..self.covariates.ncols() {
                    pred += self.covariates.get(i, k) * reg_coeff.get(k, 0);
                }
                predicted[j].push(pred);
            }
        }

        predicted
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
            // Avoid extreme values
            let trimmed_ps = ps.clamp(1e-6, 1.0 - 1e-6);
            ps_fit.push(trimmed_ps);
        }

        ps_fit
    }

    /// Compute the doubly robust ATT estimate
    fn compute_att_estimate(
        &self,
        ps_fit: &[f64],
        predicted_outcomes: &[Vec<f64>; 4],
        weights: &[f64],
    ) -> f64 {
        let n = self.y.nrows();
        let treatment_vals = self.treatment.col_as_slice(0);
        let post_vals = self.post.col_as_slice(0);
        let y_vals = self.y.col_as_slice(0);

        let [out_cont_pre, out_cont_post, out_treat_pre, out_treat_post] = predicted_outcomes;

        // Initialize components
        let mut eta_treat_pre = 0.0;
        let mut eta_treat_post = 0.0;
        let mut eta_cont_pre = 0.0;
        let mut eta_cont_post = 0.0;
        let mut eta_d_post = 0.0;
        let mut eta_dt1_post = 0.0;
        let mut eta_d_pre = 0.0;
        let mut eta_dt0_pre = 0.0;

        let mut w_treat_pre_sum = 0.0;
        let mut w_treat_post_sum = 0.0;
        let mut w_cont_pre_sum = 0.0;
        let mut w_cont_post_sum = 0.0;
        let mut w_d_sum = 0.0;
        let mut w_dt1_sum = 0.0;
        let mut w_dt0_sum = 0.0;

        // Compute weighted components (following R's drdid_rc.R lines 163-196)
        for i in 0..n {
            let d = treatment_vals[i];
            let post = post_vals[i];
            let y = y_vals[i];
            let ps = ps_fit[i];
            let w = weights[i];

            // Trim propensity scores
            let ps_trimmed = if d == 0.0 { ps.min(0.995) } else { ps };

            // Compute weights for different components
            let w_treat_pre = d * (1.0 - post) * w;
            let w_treat_post = d * post * w;
            let w_cont_pre = ps_trimmed * (1.0 - d) * (1.0 - post) * w / (1.0 - ps_trimmed);
            let w_cont_post = ps_trimmed * (1.0 - d) * post * w / (1.0 - ps_trimmed);
            let w_d = d * w;
            let w_dt1 = d * post * w;
            let w_dt0 = d * (1.0 - post) * w;

            // Outcome prediction for control group
            let out_cont = if (post - 1.0).abs() < FLOAT_EQ_EPSILON {
                out_cont_post[i]
            } else {
                out_cont_pre[i]
            };

            // Accumulate weighted outcomes
            eta_treat_pre += w_treat_pre * (y - out_cont);
            eta_treat_post += w_treat_post * (y - out_cont);
            eta_cont_pre += w_cont_pre * (y - out_cont);
            eta_cont_post += w_cont_post * (y - out_cont);

            // Additional terms for local efficiency
            eta_d_post += w_d * (out_treat_post[i] - out_cont_post[i]);
            eta_dt1_post += w_dt1 * (out_treat_post[i] - out_cont_post[i]);
            eta_d_pre += w_d * (out_treat_pre[i] - out_cont_pre[i]);
            eta_dt0_pre += w_dt0 * (out_treat_pre[i] - out_cont_pre[i]);

            // Accumulate weight sums
            w_treat_pre_sum += w_treat_pre;
            w_treat_post_sum += w_treat_post;
            w_cont_pre_sum += w_cont_pre;
            w_cont_post_sum += w_cont_post;
            w_d_sum += w_d;
            w_dt1_sum += w_dt1;
            w_dt0_sum += w_dt0;
        }

        // Normalize by weight sums
        let att_treat_pre = eta_treat_pre / w_treat_pre_sum;
        let att_treat_post = eta_treat_post / w_treat_post_sum;
        let att_cont_pre = eta_cont_pre / w_cont_pre_sum;
        let att_cont_post = eta_cont_post / w_cont_post_sum;
        let att_d_post = eta_d_post / w_d_sum;
        let att_dt1_post = eta_dt1_post / w_dt1_sum;
        let att_d_pre = eta_d_pre / w_d_sum;
        let att_dt0_pre = eta_dt0_pre / w_dt0_sum;

        // Final DR ATT estimate (R line 199-200)

        (att_treat_post - att_treat_pre) - (att_cont_post - att_cont_pre)
            + (att_d_post - att_dt1_post)
            - (att_d_pre - att_dt0_pre)
    }

    /// Compute the influence function for the DR estimator
    /// This is the most complex part - implements R's lines 202-351
    fn compute_influence_function(
        &self,
        ps_fit: &[f64],
        predicted_outcomes: &[Vec<f64>; 4],
        weights: &[f64],
    ) -> Mat<f64> {
        let n = self.y.nrows();
        let treatment_vals = self.treatment.col_as_slice(0);
        let post_vals = self.post.col_as_slice(0);
        let y_vals = self.y.col_as_slice(0);

        let [out_cont_pre, out_cont_post, out_treat_pre, out_treat_post] = predicted_outcomes;

        // Asymptotic linear representation of OLS parameters
        let asy_lin_rep_ols_pre = self.asy_lin_rep_ols((0.0, 0.0), out_cont_pre, weights);
        let asy_lin_rep_ols_post = self.asy_lin_rep_ols((0.0, 1.0), out_cont_post, weights);
        let asy_lin_rep_ols_pre_treat = self.asy_lin_rep_ols((1.0, 0.0), out_treat_pre, weights);
        let asy_lin_rep_ols_post_treat = self.asy_lin_rep_ols((1.0, 1.0), out_treat_post, weights);

        // Asymptotic linear representation of logit's beta's
        let asy_lin_rep_ps = self.asy_lin_rep_ps(ps_fit, weights);

        // Weights
        let ps_trimmed: Vec<f64> = treatment_vals
            .iter()
            .zip(ps_fit.iter())
            .map(|(&d, &ps)| if d == 0.0 { ps.min(0.995) } else { ps })
            .collect();

        let w_treat_pre: Vec<f64> = izip!(treatment_vals, post_vals, weights)
            .map(|(&d, &p, &w)| d * (1.0 - p) * w)
            .collect();
        let w_treat_post: Vec<f64> = izip!(treatment_vals, post_vals, weights)
            .map(|(&d, &p, &w)| d * p * w)
            .collect();
        let w_cont_pre: Vec<f64> = izip!(treatment_vals, post_vals, weights, &ps_trimmed)
            .map(|(&d, &p, &w, &ps)| ps * (1.0 - d) * (1.0 - p) * w / (1.0 - ps))
            .collect();
        let w_cont_post: Vec<f64> = izip!(treatment_vals, post_vals, weights, &ps_trimmed)
            .map(|(&d, &p, &w, &ps)| ps * (1.0 - d) * p * w / (1.0 - ps))
            .collect();
        let w_d: Vec<f64> = izip!(treatment_vals, weights)
            .map(|(&d, &w)| d * w)
            .collect();
        let w_dt1: Vec<f64> = izip!(treatment_vals, post_vals, weights)
            .map(|(&d, &p, &w)| d * p * w)
            .collect();
        let w_dt0: Vec<f64> = izip!(treatment_vals, post_vals, weights)
            .map(|(&d, &p, &w)| d * (1.0 - p) * w)
            .collect();

        let mean_w_treat_pre = w_treat_pre.iter().sum::<f64>() / n as f64;
        let mean_w_treat_post = w_treat_post.iter().sum::<f64>() / n as f64;
        let mean_w_cont_pre = w_cont_pre.iter().sum::<f64>() / n as f64;
        let mean_w_cont_post = w_cont_post.iter().sum::<f64>() / n as f64;
        let mean_w_d = w_d.iter().sum::<f64>() / n as f64;
        let mean_w_dt1 = w_dt1.iter().sum::<f64>() / n as f64;
        let mean_w_dt0 = w_dt0.iter().sum::<f64>() / n as f64;

        let out_y_cont: Vec<f64> = izip!(post_vals, out_cont_post, out_cont_pre)
            .map(|(&p, &post, &pre)| p.mul_add(post, (1.0 - p) * pre))
            .collect();

        let eta_treat_pre: Vec<f64> = izip!(&w_treat_pre, y_vals, &out_y_cont)
            .map(|(&w, &y, &out)| w * (y - out) / mean_w_treat_pre)
            .collect();
        let eta_treat_post: Vec<f64> = izip!(&w_treat_post, y_vals, &out_y_cont)
            .map(|(&w, &y, &out)| w * (y - out) / mean_w_treat_post)
            .collect();
        let eta_cont_pre: Vec<f64> = izip!(&w_cont_pre, y_vals, &out_y_cont)
            .map(|(&w, &y, &out)| w * (y - out) / mean_w_cont_pre)
            .collect();
        let eta_cont_post: Vec<f64> = izip!(&w_cont_post, y_vals, &out_y_cont)
            .map(|(&w, &y, &out)| w * (y - out) / mean_w_cont_post)
            .collect();

        let att_treat_pre = eta_treat_pre.iter().sum::<f64>() / n as f64;
        let att_treat_post = eta_treat_post.iter().sum::<f64>() / n as f64;
        let att_cont_pre = eta_cont_pre.iter().sum::<f64>() / n as f64;
        let att_cont_post = eta_cont_post.iter().sum::<f64>() / n as f64;

        // Influence function components
        let inf_treat_pre: Vec<f64> = izip!(eta_treat_pre, &w_treat_pre)
            .map(|(eta, w)| eta - w * att_treat_pre / mean_w_treat_pre)
            .collect();
        let inf_treat_post: Vec<f64> = izip!(eta_treat_post, &w_treat_post)
            .map(|(eta, w)| eta - w * att_treat_post / mean_w_treat_post)
            .collect();

        let m1_post = self.compute_moment_matrix(&w_treat_post, post_vals, mean_w_treat_post, true);
        let m1_pre = self.compute_moment_matrix(&w_treat_pre, post_vals, mean_w_treat_pre, false);

        let inf_treat_or_post = &asy_lin_rep_ols_post * &m1_post;
        let inf_treat_or_pre = &asy_lin_rep_ols_pre * &m1_pre;

        let inf_cont_pre: Vec<f64> = izip!(eta_cont_pre, &w_cont_pre)
            .map(|(eta, w)| eta - w * att_cont_pre / mean_w_cont_pre)
            .collect();
        let inf_cont_post: Vec<f64> = izip!(eta_cont_post, &w_cont_post)
            .map(|(eta, w)| eta - w * att_cont_post / mean_w_cont_post)
            .collect();

        let m2_pre = self.compute_moment_matrix_ps(
            &w_cont_pre,
            y_vals,
            &out_y_cont,
            att_cont_pre,
            mean_w_cont_pre,
        );
        let m2_post = self.compute_moment_matrix_ps(
            &w_cont_post,
            y_vals,
            &out_y_cont,
            att_cont_post,
            mean_w_cont_post,
        );

        let inf_cont_ps = &asy_lin_rep_ps * (m2_post - m2_pre);

        let m3_post = self.compute_moment_matrix(&w_cont_post, post_vals, mean_w_cont_post, true);
        let m3_pre = self.compute_moment_matrix(&w_cont_pre, post_vals, mean_w_cont_pre, false);

        let inf_cont_or_post = &asy_lin_rep_ols_post * &m3_post;
        let inf_cont_or_pre = &asy_lin_rep_ols_pre * &m3_pre;

        let eta_d_post: Vec<f64> = izip!(&w_d, out_treat_post, out_cont_post)
            .map(|(w, t, c)| w * (t - c) / mean_w_d)
            .collect();
        let eta_dt1_post: Vec<f64> = izip!(&w_dt1, out_treat_post, out_cont_post)
            .map(|(w, t, c)| w * (t - c) / mean_w_dt1)
            .collect();
        let eta_d_pre: Vec<f64> = izip!(&w_d, out_treat_pre, out_cont_pre)
            .map(|(w, t, c)| w * (t - c) / mean_w_d)
            .collect();
        let eta_dt0_pre: Vec<f64> = izip!(&w_dt0, out_treat_pre, out_cont_pre)
            .map(|(w, t, c)| w * (t - c) / mean_w_dt0)
            .collect();

        let att_d_post = eta_d_post.iter().sum::<f64>() / n as f64;
        let att_dt1_post = eta_dt1_post.iter().sum::<f64>() / n as f64;
        let att_d_pre = eta_d_pre.iter().sum::<f64>() / n as f64;
        let att_dt0_pre = eta_dt0_pre.iter().sum::<f64>() / n as f64;

        let inf_eff1: Vec<f64> = izip!(eta_d_post, &w_d)
            .map(|(eta, w)| eta - w * att_d_post / mean_w_d)
            .collect();
        let inf_eff2: Vec<f64> = izip!(eta_dt1_post, &w_dt1)
            .map(|(eta, w)| eta - w * att_dt1_post / mean_w_dt1)
            .collect();
        let inf_eff3: Vec<f64> = izip!(eta_d_pre, &w_d)
            .map(|(eta, w)| eta - w * att_d_pre / mean_w_d)
            .collect();
        let inf_eff4: Vec<f64> = izip!(eta_dt0_pre, &w_dt0)
            .map(|(eta, w)| eta - w * att_dt0_pre / mean_w_dt0)
            .collect();

        let inf_eff: Vec<f64> = izip!(inf_eff1, inf_eff2, inf_eff3, inf_eff4)
            .map(|(a, b, c, d)| (a - b) - (c - d))
            .collect();

        let mom_post = self.compute_moment_matrix_eff(&w_d, &w_dt1, mean_w_d, mean_w_dt1);
        let mom_pre = self.compute_moment_matrix_eff(&w_d, &w_dt0, mean_w_d, mean_w_dt0);

        let inf_or_post = (&asy_lin_rep_ols_post_treat - &asy_lin_rep_ols_post) * &mom_post;
        let inf_or_pre = (&asy_lin_rep_ols_pre_treat - &asy_lin_rep_ols_pre) * &mom_pre;

        let inf_treat_or = inf_treat_or_post + inf_treat_or_pre;
        let inf_cont_or = inf_cont_or_post + inf_cont_or_pre;
        let inf_or = inf_or_post - inf_or_pre;

        let inf_treat: Mat<f64> = Mat::from_fn(n, 1, |r, _| {
            (inf_treat_post[r] - inf_treat_pre[r]) + inf_treat_or.get(r, 0)
        });

        let inf_cont: Mat<f64> = Mat::from_fn(n, 1, |r, _| {
            (inf_cont_post[r] - inf_cont_pre[r]) + inf_cont_ps.get(r, 0) + inf_cont_or.get(r, 0)
        });

        let inf_eff_mat = Mat::from_fn(n, 1, |r, _| inf_eff[r]);

        let dr_att_inf_func1 = inf_treat - inf_cont;

        dr_att_inf_func1 + inf_eff_mat + inf_or
    }

    fn asy_lin_rep_ols(
        &self,
        group: (f64, f64),
        predicted_outcomes: &[f64],
        weights: &[f64],
    ) -> Mat<f64> {
        let n = self.y.nrows();
        let k = self.covariates.ncols();
        let treatment_vals = self.treatment.col_as_slice(0);
        let post_vals = self.post.col_as_slice(0);
        let y_vals = self.y.col_as_slice(0);

        let mut weights_ols = Mat::zeros(n, 1);
        for i in 0..n {
            if (treatment_vals[i] - group.0).abs() < 1e-10 && (post_vals[i] - group.1).abs() < 1e-10
            {
                *weights_ols.get_mut(i, 0) = weights[i];
            }
        }

        let mut weighted_covariates = Mat::zeros(n, k);
        for i in 0..n {
            for j in 0..k {
                *weighted_covariates.get_mut(i, j) =
                    weights_ols.get(i, 0) * self.covariates.get(i, j);
            }
        }

        let mut weighted_residuals_x = Mat::zeros(n, k);
        for i in 0..n {
            let residual = y_vals[i] - predicted_outcomes[i];
            for j in 0..k {
                *weighted_residuals_x.get_mut(i, j) =
                    weights_ols.get(i, 0) * residual * self.covariates.get(i, j);
            }
        }

        let xpx = weighted_covariates.transpose() * &self.covariates / n as f64;
        let xpx_inv = xpx.qr().solve(&Mat::identity(k, k));

        &weighted_residuals_x * &xpx_inv
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

    fn compute_moment_matrix(
        &self,
        w_treat: &[f64],
        post_vals: &[f64],
        mean_w_treat: f64,
        is_post: bool,
    ) -> Mat<f64> {
        let n = self.y.nrows();
        let k = self.covariates.ncols();
        let mut m: Mat<f64> = Mat::zeros(k, 1);

        for i in 0..n {
            let post_val = if is_post {
                post_vals[i]
            } else {
                1.0 - post_vals[i]
            };
            for j in 0..k {
                *m.get_mut(j, 0) -= w_treat[i] * post_val * self.covariates.get(i, j);
            }
        }
        m / (n as f64 * mean_w_treat)
    }

    fn compute_moment_matrix_ps(
        &self,
        w_cont: &[f64],
        y_vals: &[f64],
        out_y_cont: &[f64],
        att_cont: f64,
        mean_w_cont: f64,
    ) -> Mat<f64> {
        let n = self.y.nrows();
        let k = self.covariates.ncols();
        let mut m: Mat<f64> = Mat::zeros(k, 1);

        for i in 0..n {
            let val = w_cont[i] * (y_vals[i] - out_y_cont[i] - att_cont);
            for j in 0..k {
                *m.get_mut(j, 0) += val * self.covariates.get(i, j);
            }
        }
        m / (n as f64 * mean_w_cont)
    }

    fn compute_moment_matrix_eff(
        &self,
        w_d: &[f64],
        w_dt: &[f64],
        mean_w_d: f64,
        mean_w_dt: f64,
    ) -> Mat<f64> {
        let n = self.y.nrows();
        let k = self.covariates.ncols();
        let mut m: Mat<f64> = Mat::zeros(k, 1);

        for i in 0..n {
            let val = w_d[i] / mean_w_d - w_dt[i] / mean_w_dt;
            for j in 0..k {
                *m.get_mut(j, 0) += val * self.covariates.get(i, j);
            }
        }
        m / n as f64
    }
}

impl crate::estimators::traits::Estimator for DRDIDRC {
    fn estimate(&self) -> Result<crate::estimators::types::EstResult, crate::DidError> {
        let (att, inf) = Self::estimate(self)?;
        Ok(crate::estimators::types::EstResult { att, inf })
    }
}
