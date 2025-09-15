#![warn(clippy::all)]
// re-enable all Clippy lints just for this module
// #![warn(clippy::pedantic)] // (optional) add more strictness if desired
#![warn(clippy::nursery)] // (optional) add more strictness if desired
                          // #![allow(clippy::cast_precision_loss)]
                          // #![allow(clippy::cast_possible_truncation)]
pub mod api;
pub mod computation;
pub mod data;
pub mod diagnostics;
pub mod error;
pub mod estimators;
pub mod inference;
pub mod prelude;
pub mod types;

pub use api::DidEstimator;
pub use error::DidError;
pub use types::{AttGtResult, DidConfig, DidResult};
