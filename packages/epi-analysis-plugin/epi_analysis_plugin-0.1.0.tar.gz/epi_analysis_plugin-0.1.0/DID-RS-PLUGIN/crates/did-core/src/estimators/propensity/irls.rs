use faer::prelude::*;
use faer::sparse::SparseColMat;
use faer::Mat;

use super::common::{debug_matrix_ranges, empirical_logit, safe_sigmoid};
use crate::DidError;

pub fn irls(
    design: &Mat<f64>,
    target: &Mat<f64>,
    max_iter: u64,
    tol: f64,
    min_weight: f64,
) -> Result<Mat<f64>, DidError> {
    let mut beta = initial_beta(design, target);
    for iter in 0..max_iter {
        let x_beta = design * &beta;
        let p_hat = prob(&x_beta);
        let w = weights(&p_hat, min_weight);
        let w_sparse = diag_sparse(&w)?;
        let z = working_response(design, target, &x_beta, &p_hat, &w);
        let new_beta = solve_wls(design, &w_sparse, &z);
        let change = (&new_beta - &beta).norm_l2();
        if iter < 5 || iter % 10 == 0 {
            debug_matrix_ranges("p_hat", &p_hat);
            debug_matrix_ranges("w", &w);
        }
        if change < tol {
            return Ok(new_beta);
        }
        beta = new_beta;
    }
    Err(DidError::Convergence("IRLS did not converge".to_string()))
}

fn initial_beta(design: &Mat<f64>, target: &Mat<f64>) -> Mat<f64> {
    let mut beta0 = Mat::zeros(design.ncols(), 1);
    *beta0.get_mut(0, 0) = empirical_logit(target);
    beta0
}

fn prob(x_beta: &Mat<f64>) -> Mat<f64> {
    let mut prob_vec = Mat::zeros(x_beta.nrows(), 1);
    for row in 0..x_beta.nrows() {
        *prob_vec.get_mut(row, 0) = safe_sigmoid(*x_beta.get(row, 0));
    }
    prob_vec
}

fn weights(prob_vec: &Mat<f64>, min_weight: f64) -> Mat<f64> {
    let mut w_mat = Mat::zeros(prob_vec.nrows(), 1);
    for row in 0..prob_vec.nrows() {
        let pval = prob_vec.get(row, 0);
        *w_mat.get_mut(row, 0) = (pval * (1.0 - pval)).max(min_weight);
    }
    w_mat
}

fn diag_sparse(w: &Mat<f64>) -> Result<SparseColMat<usize, f64>, DidError> {
    let mut triplets = Vec::with_capacity(w.nrows());
    for (i, &val) in w.col_as_slice(0).iter().enumerate() {
        triplets.push(faer::sparse::Triplet::new(i, i, val));
    }
    SparseColMat::<usize, f64>::try_new_from_triplets(w.nrows(), w.nrows(), &triplets)
        .map_err(|e| DidError::Estimation(format!("Failed to create weight matrix: {e}")))
}

fn working_response(
    _x: &Mat<f64>,
    d: &Mat<f64>,
    x_beta: &Mat<f64>,
    p_hat: &Mat<f64>,
    w: &Mat<f64>,
) -> Mat<f64> {
    let mut z = Mat::zeros(x_beta.nrows(), 1);
    for i in 0..x_beta.nrows() {
        let eta = x_beta.get(i, 0);
        let p = p_hat.get(i, 0);
        let di = *d.get(i, 0);
        let wi = *w.get(i, 0);
        *z.get_mut(i, 0) = eta + (di - p) / wi;
    }
    z
}

fn solve_wls(x: &Mat<f64>, w: &SparseColMat<usize, f64>, z: &Mat<f64>) -> Mat<f64> {
    let x_t_w = x.transpose() * w;
    let mut x_t_w_x = &x_t_w * x;
    let x_t_w_z = &x_t_w * z;
    let reg = 1e-8;
    for i in 0..x_t_w_x.ncols() {
        *x_t_w_x.get_mut(i, i) += reg;
    }
    x_t_w_x.partial_piv_lu().solve(&x_t_w_z)
}
