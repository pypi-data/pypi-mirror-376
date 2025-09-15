use arrow::record_batch::RecordBatch;

use super::validation;
use crate::data::preprocessed::PreprocessedData;
use crate::{DidConfig, DidError};

pub struct PreprocessBuilder {
    data: RecordBatch,
    config: DidConfig,
}

impl PreprocessBuilder {
    #[must_use]
    pub const fn new(data: RecordBatch, config: DidConfig) -> Self {
        Self { data, config }
    }

    pub fn validate(&self) -> Result<(), DidError> {
        validation::validate_schema(&self.data, &self.config)
    }

    pub fn build(self) -> Result<PreprocessedData, DidError> {
        PreprocessedData::from_config(self.data, &self.config)
    }
}
