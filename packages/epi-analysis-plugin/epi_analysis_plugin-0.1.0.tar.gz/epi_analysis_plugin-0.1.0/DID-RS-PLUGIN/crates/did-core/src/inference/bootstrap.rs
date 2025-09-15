use faer::Mat;
use rand::rngs::StdRng;
use rand::{rng, Rng, SeedableRng};
use rayon::prelude::*;

/// Generate Rademacher weights {-1, +1} using `BMisc` C++ bit extraction method
/// This mimics the `fill_rademacher` function in BMisc.cpp
fn generate_rademacher_weights(n: usize, rng: &mut StdRng) -> Vec<f64> {
    let mut weights = vec![0.0; n];
    let num_integers = ((n as f64) / 31.0).ceil() as usize;
    let mut k = 0;

    // Process full 31-bit integers
    for _ in 0..num_integers.saturating_sub(1) {
        // Generate random integer up to 2^31 - 1 = 2147483647
        let curr = rng.random_range(0..2147483647);

        // Extract 31 bits (j from 30 down to 0)
        for j in (0..=30).rev() {
            if k >= n {
                break;
            }
            weights[k] = if (curr >> j) & 1 == 1 { 1.0 } else { -1.0 };
            k += 1;
        }
    }

    // Handle remaining weights from the last integer
    if k < n {
        let curr = rng.random_range(0..2147483647);
        let mut j = 30;
        while k < n && j >= 0 {
            weights[k] = if (curr >> j) & 1 == 1 { 1.0 } else { -1.0 };
            k += 1;
            j -= 1;
        }
    }

    weights
}

pub struct MultiplierBootstrap {
    iterations: usize,
    _cluster_var: Option<String>,
    rng_seed: Option<u64>,
}

impl MultiplierBootstrap {
    #[must_use]
    pub const fn new(
        iterations: usize,
        cluster_var: Option<String>,
        rng_seed: Option<u64>,
    ) -> Self {
        Self {
            iterations,
            _cluster_var: cluster_var,
            rng_seed,
        }
    }

    #[must_use]
    pub fn compute_standard_errors(&self, influence_function: &Mat<f64>) -> Vec<f64> {
        let n_obs = influence_function.nrows();
        let n_att = influence_function.ncols();

        // Use R's exact standard error computation: V = t(inffunc) %*% inffunc / n, se = sqrt(diag(V) / n)
        // This matches lines 295-296 in att_gt.R
        let mut se = vec![0.0; n_att];
        for (i, se_val) in se.iter_mut().enumerate().take(n_att) {
            let influence_col = influence_function.col_as_slice(i);
            // R: V[i,i] = sum(inffunc[,i]^2) / n
            let variance = influence_col.iter().map(|x| x.powi(2)).sum::<f64>() / n_obs as f64;
            // R: se[i] = sqrt(V[i,i] / n) = sqrt(sum(inffunc[,i]^2) / n^2)
            *se_val = (variance / n_obs as f64).sqrt();
        }
        se
    }

    /// Compute uniform confidence bands using multiplier bootstrap
    /// This replicates R's `mboot()` function for computing critical values and uniform bands
    #[must_use]
    pub fn compute_uniform_bands(
        &self,
        influence_function: &Mat<f64>,
        att_estimates: &[f64],
    ) -> (Vec<f64>, Vec<f64>) {
        let n_obs = influence_function.nrows();
        let n_att = influence_function.ncols();

        // Create a seeded RNG for reproducibility
        let mut main_rng: StdRng = if let Some(seed) = self.rng_seed {
            StdRng::seed_from_u64(seed)
        } else {
            StdRng::from_rng(&mut rng())
        };

        // Generate seeds for each parallel iteration to ensure determinism
        let seeds: Vec<u64> = (0..self.iterations).map(|_| main_rng.random()).collect();

        // Step 1: Generate bootstrap distribution matrix (iterations x n_att)
        let bootstrap_results: Vec<Vec<f64>> = seeds
            .into_par_iter()
            .map(|seed| {
                let mut rng = StdRng::seed_from_u64(seed);
                let rademacher_weights = generate_rademacher_weights(n_obs, &mut rng);

                let mut iteration_results = vec![0.0; n_att];
                for col_idx in 0..n_att {
                    let influence_col = influence_function.col_as_slice(col_idx);
                    let dot_product: f64 = influence_col
                        .iter()
                        .zip(&rademacher_weights)
                        .map(|(inf, weight)| inf * weight)
                        .sum();
                    // Following R: sqrt(n) * (dot_product / n) = dot_product / sqrt(n)
                    iteration_results[col_idx] = dot_product / (n_obs as f64).sqrt();
                }
                iteration_results
            })
            .collect();

        // Step 2: Compute bootstrap standard errors (bSigma) for each column
        let mut bsigma = vec![0.0; n_att];
        for col_idx in 0..n_att {
            let mut column_values: Vec<f64> =
                bootstrap_results.iter().map(|row| row[col_idx]).collect();
            column_values.sort_by(|a, b| a.partial_cmp(b).unwrap());

            // R type=1 quantiles
            let n_bootstrap = column_values.len();
            let q75_idx = ((n_bootstrap as f64 * 0.75).ceil() as usize - 1).min(n_bootstrap - 1);
            let q25_idx = ((n_bootstrap as f64 * 0.25).ceil() as usize - 1).min(n_bootstrap - 1);
            let q75 = column_values[q75_idx];
            let q25 = column_values[q25_idx];

            // qnorm(0.75) ≈ 0.6745, qnorm(0.25) ≈ -0.6745
            let qnorm_diff = 0.6745 - (-0.6745); // ≈ 1.349
            bsigma[col_idx] = (q75 - q25) / qnorm_diff;
        }

        // Step 3: Compute critical value for uniform confidence bands
        // R: bT <- apply(bres, 1, function(b) max(abs(b/bSigma), na.rm = T))
        let bt_values: Vec<f64> = bootstrap_results
            .iter()
            .map(|row| {
                row.iter()
                    .zip(&bsigma)
                    .map(|(b, sigma)| {
                        if *sigma > f64::EPSILON {
                            (b / sigma).abs()
                        } else {
                            0.0
                        }
                    })
                    .fold(0.0f64, f64::max)
            })
            .filter(|x| x.is_finite())
            .collect();

        // Critical value: quantile(bT, 1-alp, type=1)
        // Using alpha = 0.05 for 95% confidence bands
        let alpha = 0.05;
        let mut sorted_bt = bt_values;
        sorted_bt.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let critical_idx =
            ((sorted_bt.len() as f64 * (1.0 - alpha)).ceil() as usize - 1).min(sorted_bt.len() - 1);
        let critical_value = if sorted_bt.is_empty() {
            1.96 // fallback to normal critical value
        } else {
            sorted_bt[critical_idx]
        };

        // Step 4: Compute standard errors: se = bSigma / sqrt(n_clusters)
        let n_clusters = n_obs; // No clustering in basic case
        let standard_errors: Vec<f64> = bsigma
            .iter()
            .map(|sigma| sigma / (n_clusters as f64).sqrt())
            .collect();

        // Step 5: Compute confidence bounds
        let low_bounds: Vec<f64> = att_estimates
            .iter()
            .zip(&standard_errors)
            .map(|(att, se)| att - critical_value * se)
            .collect();

        let high_bounds: Vec<f64> = att_estimates
            .iter()
            .zip(&standard_errors)
            .map(|(att, se)| att + critical_value * se)
            .collect();

        (low_bounds, high_bounds)
    }

    /// # Panics
    ///
    /// This function will panic if the quantile is not between 0 and 1.

    /// Compute bootstrap standard error for single influence function column
    /// This replicates R's `getSE()` -> `mboot()` -> bout$se calculation exactly
    #[must_use]
    pub fn compute_bootstrap_se_single_column(&self, influence_function: &Mat<f64>) -> f64 {
        let n_obs = influence_function.nrows();

        // Create a seeded RNG for reproducibility
        let mut main_rng: StdRng = if let Some(seed) = self.rng_seed {
            StdRng::seed_from_u64(seed)
        } else {
            StdRng::from_rng(&mut rng())
        };

        // Generate seeds for each parallel iteration to ensure determinism
        let seeds: Vec<u64> = (0..self.iterations).map(|_| main_rng.random()).collect();

        // Step 1: Generate bootstrap distribution using exact BMisc methodology
        let bootstrap_dist: Vec<f64> = seeds
            .into_par_iter()
            .map(|seed| {
                let mut rng = StdRng::seed_from_u64(seed);

                // Generate Rademacher weights exactly like BMisc C++ implementation
                let rademacher_weights = generate_rademacher_weights(n_obs, &mut rng);

                // Compute dot product: inf_func_col · rademacher_weights
                let influence_col = influence_function.col_as_slice(0);
                let dot_product: f64 = influence_col
                    .iter()
                    .zip(&rademacher_weights)
                    .map(|(inf, weight)| inf * weight)
                    .sum();

                // BMisc formula: (dot_product / n) * sqrt(n) = dot_product / sqrt(n)
                dot_product / (n_obs as f64).sqrt()
            })
            .collect();

        // Step 2: Compute IQR-based standard error (mboot.R lines 111-113)
        // bSigma <- apply(bres, 2, function(b) (quantile(b, .75, type=1) - quantile(b, .25, type=1))/(qnorm(.75) - qnorm(.25)))
        let mut sorted_dist = bootstrap_dist;
        sorted_dist.sort_by(|a, b| a.partial_cmp(b).unwrap());

        // R type=1 quantiles
        let n_bootstrap = sorted_dist.len();
        let q75_idx = ((n_bootstrap as f64 * 0.75).ceil() as usize - 1).min(n_bootstrap - 1);
        let q25_idx = ((n_bootstrap as f64 * 0.25).ceil() as usize - 1).min(n_bootstrap - 1);
        let q75 = sorted_dist[q75_idx];
        let q25 = sorted_dist[q25_idx];

        // qnorm(0.75) ≈ 0.6745, qnorm(0.25) ≈ -0.6745
        let qnorm_diff = 0.6745 - (-0.6745); // ≈ 1.349
        let bsigma = (q75 - q25) / qnorm_diff;

        // Step 3: Return bootstrap SE (mboot.R line 122)
        // se[ndg.dim] <- as.numeric(bSigma) / sqrt(n_clusters)
        let n_clusters = n_obs; // No clustering for simple aggregation
        bsigma / (n_clusters as f64).sqrt()
    }
}
