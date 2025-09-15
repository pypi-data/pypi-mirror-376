use std::collections::HashMap;
use std::hash::BuildHasher;

use crate::DidError;

/// Fetch a group's sampling probability or return a specification error.
pub fn group_prob_or_err<S: BuildHasher>(
    map: &HashMap<i64, f64, S>,
    group: i64,
) -> Result<f64, DidError> {
    map.get(&group).copied().ok_or_else(|| {
        DidError::Specification(format!("Group probability not found for group {group}"))
    })
}
