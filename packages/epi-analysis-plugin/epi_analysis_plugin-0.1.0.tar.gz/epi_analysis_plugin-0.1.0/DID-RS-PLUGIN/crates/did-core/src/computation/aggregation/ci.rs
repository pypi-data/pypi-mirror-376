/// Z critical value for a given confidence level (approximate).
#[must_use]
pub fn z_from_confidence(confidence_level: f64) -> f64 {
    match confidence_level {
        0.90 => 1.645,
        0.95 => 1.96,
        0.99 => 2.576,
        _ => 1.96,
    }
}

#[must_use]
pub fn ci_from_att_se(att: f64, se: f64, z: f64) -> (f64, f64) {
    (z.mul_add(-se, att), z.mul_add(se, att))
}
