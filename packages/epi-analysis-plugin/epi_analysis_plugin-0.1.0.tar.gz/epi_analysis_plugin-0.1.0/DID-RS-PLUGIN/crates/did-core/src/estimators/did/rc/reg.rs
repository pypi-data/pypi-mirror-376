//! Outcome regression DID estimator for repeated cross sections
//! Implementation following Sant'Anna and Zhao (2020) equation (2.2)

use faer::prelude::*;
use faer::Mat;
use itertools::izip;

use crate::estimators::outcome::model::OutcomeModel;
use crate::DidError;

const FLOAT_EQ_EPSILON: f64 = 1e-10;

/// Outcome regression `DiD` estimator for repeated cross sections data
///
/// This implements the outcome regression DID estimator from
/// Sant'Anna and Zhao (2020) equation (2.2) for repeated cross-sectional data.
///
/// The estimator uses linear regression models for outcomes in each group/period
/// and constructs the DID estimate from the predicted values.
pub struct RegRC {
    // Input data (stacked format: pre and post periods)
    y: Mat<f64>,          // Outcome variable
    post: Mat<f64>,       // Post-treatment indicator
    treatment: Mat<f64>,  // Treatment group indicator
    covariates: Mat<f64>, // Covariates including intercept
    weights: Mat<f64>,    // Sampling weights
}

impl RegRC {
    #[must_use]
    pub fn new(
        y: Mat<f64>,
        post: Mat<f64>,
        treatment: Mat<f64>,
        covariates: Mat<f64>,
        weights: Option<Mat<f64>>,
    ) -> Self {
        let n = y.nrows();
        let weights = weights.unwrap_or_else(|| Mat::from_fn(n, 1, |_, _| 1.0));

        Self {
            y,
            post,
            treatment,
            covariates,
            weights,
        }
    }

    /// Estimate ATT using outcome regression approach for repeated cross sections
    ///
    /// # Errors
    /// Returns `DidError` if:
    /// - Data validation fails (missing groups, invalid indicators)
    /// - Outcome regression fails due to matrix singularity
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

        // Step 2: Estimate outcome regressions for all four groups
        let reg_coeffs = self.estimate_outcome_regressions(&normalized_weights)?;

        // Step 3: Compute predicted outcomes
        let predicted_outcomes = self.compute_predicted_outcomes(&reg_coeffs);

        // Step 4: Compute regression-based ATT estimate
        let att = self.compute_reg_att(&predicted_outcomes, &normalized_weights)?;

        // Step 5: Compute influence function
        let influence_function = self.compute_influence_function(
            &reg_coeffs,
            &predicted_outcomes,
            &normalized_weights,
            att,
        );

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

    /// Compute the regression-based ATT estimate
    ///
    /// The outcome regression DID estimator is:
    /// τ = E[m₁(X)|D=1] - E[m₀(X)|D=1] - (E[m₁(X)|D=0] - E[m₀(X)|D=0])
    ///
    /// Where `m_t(X)` are the outcome regression functions for period t
    fn compute_reg_att(
        &self,
        predicted_outcomes: &[Vec<f64>; 4],
        weights: &[f64],
    ) -> Result<f64, DidError> {
        let n = self.y.nrows();
        let treatment_vals = self.treatment.col_as_slice(0);

        let [pred_cont_pre, pred_cont_post, pred_treat_pre, pred_treat_post] = predicted_outcomes;

        // Compute weighted means of predicted outcomes for treated and control groups
        let mut sum_treat_weights = 0.0;
        let mut sum_cont_weights = 0.0;

        let mut sum_treat_pre = 0.0;
        let mut sum_treat_post = 0.0;
        let mut sum_cont_pre = 0.0;
        let mut sum_cont_post = 0.0;

        for i in 0..n {
            let d = treatment_vals[i];
            let w = weights[i];

            if (d - 1.0).abs() < FLOAT_EQ_EPSILON {
                // For treated units, use predictions from all four models
                sum_treat_pre += w * pred_treat_pre[i];
                sum_treat_post += w * pred_treat_post[i];
                sum_treat_weights += w;
            } else {
                // For control units, use predictions from all four models
                sum_cont_pre += w * pred_cont_pre[i];
                sum_cont_post += w * pred_cont_post[i];
                sum_cont_weights += w;
            }
        }

        if sum_treat_weights == 0.0 || sum_cont_weights == 0.0 {
            return Err(DidError::Estimation(
                "Zero total weight for treated or control group".to_string(),
            ));
        }

        // Compute group means
        let mean_treat_pre = sum_treat_pre / sum_treat_weights;
        let mean_treat_post = sum_treat_post / sum_treat_weights;
        let mean_cont_pre = sum_cont_pre / sum_cont_weights;
        let mean_cont_post = sum_cont_post / sum_cont_weights;

        // Regression DID estimate: DID for treated - DID for control
        let reg_att = (mean_treat_post - mean_treat_pre) - (mean_cont_post - mean_cont_pre);

        Ok(reg_att)
    }

    /// Compute the influence function for the regression estimator
    ///
    /// This involves the influence functions of all the outcome regression estimations
    /// and how they contribute to the final DID estimate.
    fn compute_influence_function(
        &self,
        _reg_coeffs: &[Mat<f64>; 4],
        predicted_outcomes: &[Vec<f64>; 4],
        weights: &[f64],
        _att_estimate: f64,
    ) -> Mat<f64> {
        let n = self.y.nrows();
        let treatment_vals = self.treatment.col_as_slice(0);
        let post_vals = self.post.col_as_slice(0);
        let y_vals = self.y.col_as_slice(0);

        let [out_cont_pre, out_cont_post, _, _] = predicted_outcomes;

        // Asymptotic linear representation of OLS parameters
        let asy_lin_rep_ols_pre = self.asy_lin_rep_ols((0.0, 0.0), out_cont_pre, weights);
        let asy_lin_rep_ols_post = self.asy_lin_rep_ols((0.0, 1.0), out_cont_post, weights);

        let w_treat_pre: Vec<f64> = izip!(treatment_vals, post_vals, weights)
            .map(|(&d, &p, &w)| d * (1.0 - p) * w)
            .collect();
        let w_treat_post: Vec<f64> = izip!(treatment_vals, post_vals, weights)
            .map(|(&d, &p, &w)| d * p * w)
            .collect();
        let w_cont: Vec<f64> = izip!(treatment_vals, weights)
            .map(|(&d, &w)| d * w)
            .collect();

        let mean_w_treat_pre = w_treat_pre.iter().sum::<f64>() / n as f64;
        let mean_w_treat_post = w_treat_post.iter().sum::<f64>() / n as f64;
        let mean_w_cont = w_cont.iter().sum::<f64>() / n as f64;

        let reg_att_treat_pre: Vec<f64> =
            izip!(&w_treat_pre, y_vals).map(|(&w, &y)| w * y).collect();
        let reg_att_treat_post: Vec<f64> =
            izip!(&w_treat_post, y_vals).map(|(&w, &y)| w * y).collect();
        let reg_att_cont: Vec<f64> = izip!(&w_cont, out_cont_post, out_cont_pre)
            .map(|(&w, &post, &pre)| w * (post - pre))
            .collect();

        let eta_treat_pre = reg_att_treat_pre.iter().sum::<f64>() / (n as f64 * mean_w_treat_pre);
        let eta_treat_post =
            reg_att_treat_post.iter().sum::<f64>() / (n as f64 * mean_w_treat_post);
        let eta_cont = reg_att_cont.iter().sum::<f64>() / (n as f64 * mean_w_cont);

        let inf_treat_pre: Vec<f64> = izip!(&reg_att_treat_pre, &w_treat_pre)
            .map(|(&reg, &w)| w.mul_add(-eta_treat_pre, reg) / mean_w_treat_pre)
            .collect();
        let inf_treat_post: Vec<f64> = izip!(&reg_att_treat_post, &w_treat_post)
            .map(|(&reg, &w)| w.mul_add(-eta_treat_post, reg) / mean_w_treat_post)
            .collect();
        let inf_treat: Vec<f64> = izip!(inf_treat_post, inf_treat_pre)
            .map(|(post, pre)| post - pre)
            .collect();

        let inf_cont_1: Vec<f64> = izip!(&reg_att_cont, &w_cont)
            .map(|(&reg, &w)| w.mul_add(-eta_cont, reg))
            .collect();

        let mut m1: Mat<f64> = Mat::zeros(self.covariates.ncols(), 1);
        for (i, &weight) in w_cont.iter().enumerate().take(n) {
            for j in 0..self.covariates.ncols() {
                *m1.get_mut(j, 0) += weight * self.covariates.get(i, j);
            }
        }
        m1 /= n as f64;

        let inf_cont_2_post = &asy_lin_rep_ols_post * &m1;
        let inf_cont_2_pre = &asy_lin_rep_ols_pre * &m1;

        let inf_control: Vec<f64> = izip!(
            inf_cont_1,
            inf_cont_2_post.col_as_slice(0),
            inf_cont_2_pre.col_as_slice(0)
        )
        .map(|(a, &b, &c)| (a + b - c) / mean_w_cont)
        .collect();

        let reg_att_inf_func_vec: Vec<f64> =
            izip!(inf_treat, inf_control).map(|(a, b)| a - b).collect();

        Mat::from_fn(n, 1, |r, _| reg_att_inf_func_vec[r])
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
}
