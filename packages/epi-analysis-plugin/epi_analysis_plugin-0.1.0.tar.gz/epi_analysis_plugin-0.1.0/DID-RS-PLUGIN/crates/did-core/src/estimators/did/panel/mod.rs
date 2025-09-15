// Panel data DID estimators (longitudinal data structure)
pub mod drdid;
pub mod ipw;
pub mod reg;

// Re-exports for convenience
pub use drdid::*;
pub use ipw::*;
pub use reg::*;
