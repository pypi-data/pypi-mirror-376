use std::fs::File;
use std::sync::Arc;

use arrow::csv;
use arrow::record_batch::RecordBatch;
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;

use crate::computation::attgt::AttGtComputer;
use crate::data::preprocessed::PreprocessedData;
use crate::types::PanelType;
use crate::{DidConfig, DidError, DidResult};

pub struct DidEstimator {
    data: RecordBatch,
    config: DidConfig,
}

impl DidEstimator {
    pub const fn from_batch(data: RecordBatch, config: DidConfig) -> Result<Self, DidError> {
        Ok(Self { data, config })
    }

    pub fn from_csv(path: &str, config: DidConfig) -> Result<Self, DidError> {
        let schema =
            arrow::csv::infer_schema_from_files(&[path.to_string()], b',', Some(100), true)?;
        let schema = Arc::new(schema);

        let file = File::open(path)?;
        let builder = csv::ReaderBuilder::new(schema.clone()).with_header(true);
        let csv_reader = builder.build(file)?;

        let mut batches = Vec::new();
        for batch_result in csv_reader {
            batches.push(batch_result?);
        }

        if batches.is_empty() {
            return Err(DidError::Io(std::io::Error::other(
                "CSV file is empty or contains no data.",
            )));
        }

        let batch = arrow::compute::concat_batches(&schema, &batches)?;
        Self::from_batch(batch, config)
    }

    pub fn from_parquet(path: &str, config: DidConfig) -> Result<Self, DidError> {
        let file = File::open(path)?;
        let builder = ParquetRecordBatchReaderBuilder::try_new(file)?;
        let mut reader = builder.build()?;
        let batch = reader
            .next()
            .ok_or(DidError::Io(std::io::Error::other("No data in Parquet")))??;
        Self::from_batch(batch, config)
    }

    #[must_use]
    pub const fn data(&self) -> &RecordBatch {
        &self.data
    }

    pub fn fit(&self) -> Result<DidResult, DidError> {
        let preprocessed_data = PreprocessedData::from_config(self.data.clone(), &self.config)?;
        preprocessed_data.validate_args(&self.config)?;
        //preprocessed_data.standardize_data(&self.config)?;

        let computer = AttGtComputer::new(self.config.clone(), preprocessed_data);
        computer.compute()
    }

    /// Get panel information for diagnostics
    pub fn get_panel_info(&self) -> Result<(PanelType, bool, usize), DidError> {
        let preprocessed_data = PreprocessedData::from_config(self.data.clone(), &self.config)?;
        Ok(preprocessed_data.get_panel_info())
    }
}
