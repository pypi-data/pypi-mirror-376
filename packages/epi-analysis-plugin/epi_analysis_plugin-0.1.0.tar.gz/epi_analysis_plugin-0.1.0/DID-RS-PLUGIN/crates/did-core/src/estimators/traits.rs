use crate::estimators::types::EstResult;
use crate::DidError;

pub trait Estimator {
    fn estimate(&self) -> Result<EstResult, DidError>;
}
