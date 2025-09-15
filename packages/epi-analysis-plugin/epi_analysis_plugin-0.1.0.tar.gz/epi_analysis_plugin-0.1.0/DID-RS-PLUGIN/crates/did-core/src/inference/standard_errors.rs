/// Standard error calculation for aggregation using did package formula
/// From compute.aggte.R:651: return(sqrt( mean((thisinffunc)^2)/n ))
#[must_use]
pub fn compute_aggte_se(influence_col: &[f64], n: f64) -> f64 {
    if n > 0.0 {
        let mean_sq: f64 =
            influence_col.iter().map(|x| x.powi(2)).sum::<f64>() / influence_col.len() as f64;
        (mean_sq / n).sqrt()
    } else {
        0.0
    }
}

/// Standard errors for ATT(g,t) using did package formula.
/// R: V <- t(inffunc) %*% inffunc / n; se <- sqrt(diag(V)/n).
/// Equivalent: `sqrt(sum(influence_col^2)` / n^2).
#[must_use]
pub fn compute_attgt_se(influence_col: &[f64], n: f64) -> f64 {
    if n > 0.0 {
        // did package formula: V = t(inffunc) %*% inffunc / n, se = sqrt(diag(V) / n)
        // For single column: diag(V) = sum(influence_col^2) / n
        // So se = sqrt(sum(influence_col^2) / n / n) = sqrt(sum(influence_col^2)) / n
        let sum_sq: f64 = influence_col.iter().map(|x| x.powi(2)).sum();
        sum_sq.sqrt() / n
    } else {
        0.0
    }
}

/// Standard error calculation using DRDID package formula (for reference)
/// From `drdid_panel.R:220`: se.dr.att <- `stats::sd(dr.att.inf.func)/sqrt(n)`
#[must_use]
pub fn compute_attgt_se_drdid(influence_col: &[f64], n: f64) -> f64 {
    if n > 1.0 {
        let mean = influence_col.iter().sum::<f64>() / influence_col.len() as f64;
        let variance = influence_col
            .iter()
            .map(|x| (x - mean).powi(2))
            .sum::<f64>()
            / (influence_col.len() - 1) as f64;
        variance.sqrt() / n.sqrt()
    } else {
        0.0
    }
}
