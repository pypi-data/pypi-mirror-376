// Core traits and types
pub mod traits;
pub mod types;

// Common utilities shared across estimators
pub mod common;
pub mod outcome;
pub mod propensity;

// Main DID estimators organized by data structure
pub mod did;

// Legacy estimators (consider deprecating)
pub mod simple_did;

// Re-export commonly used items
pub use traits::Estimator;
pub use types::EstResult;
