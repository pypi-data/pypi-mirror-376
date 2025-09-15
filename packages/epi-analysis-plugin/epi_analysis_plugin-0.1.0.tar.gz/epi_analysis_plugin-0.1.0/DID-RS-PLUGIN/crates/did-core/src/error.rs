use std::fmt;

use faer::linalg::svd::SvdError;
use thiserror::Error;

#[derive(Debug)]
pub struct FaerSvdError(pub SvdError);

impl fmt::Display for FaerSvdError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "SVD error: {:?}", self.0)
    }
}

impl std::error::Error for FaerSvdError {}

#[derive(Debug, Error)]
pub enum DidError {
    #[error("Data preprocessing error: {0}")]
    Preprocessing(String),
    #[error("Model specification error: {0}")]
    Specification(String),
    #[error("Estimation failed: {0}")]
    Estimation(String),
    #[error("Convergence error: {0}")]
    Convergence(String),
    #[error("Bootstrap error: {0}")]
    Bootstrap(String),
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Arrow error: {0}")]
    Arrow(#[from] arrow::error::ArrowError),
    #[error("Parquet error: {0}")]
    Parquet(#[from] parquet::errors::ParquetError),
    #[error("SVD error: {0}")]
    Svd(#[from] FaerSvdError),
}

impl From<SvdError> for DidError {
    fn from(err: SvdError) -> Self {
        Self::Svd(FaerSvdError(err))
    }
}
