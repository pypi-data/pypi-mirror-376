use arrow::array::Int64Array;

use crate::data::preprocessed::PreprocessedData;
use crate::types::DidConfig;
use crate::DidError;

/// Borrowed Arrow views for core id/time/group columns.
pub struct DataArrays<'a> {
    pub group: &'a Int64Array,
    pub time: &'a Int64Array,
    pub id: &'a Int64Array,
}

impl<'a> DataArrays<'a> {
    /// Construct `DataArrays` by resolving column names from config.
    ///
    /// # Errors
    /// Returns an error if required columns are missing or of wrong type.
    pub fn new(data: &'a PreprocessedData, config: &DidConfig) -> Result<Self, DidError> {
        let group_var = config
            .group_var
            .as_deref()
            .ok_or_else(|| DidError::Specification("group_var missing".into()))?;
        let group = data
            .data
            .column_by_name(group_var)
            .ok_or_else(|| {
                DidError::Specification(format!("group column '{group_var}' not found"))
            })?
            .as_any()
            .downcast_ref::<Int64Array>()
            .ok_or_else(|| DidError::Specification("group column must be Int64".into()))?;
        let time = data
            .data
            .column_by_name(&config.time_var)
            .ok_or_else(|| {
                DidError::Specification(format!("time column '{}' not found", config.time_var))
            })?
            .as_any()
            .downcast_ref::<Int64Array>()
            .ok_or_else(|| DidError::Specification("time column must be Int64".into()))?;
        let id = data
            .data
            .column_by_name(&config.id_var)
            .ok_or_else(|| {
                DidError::Specification(format!("id column '{}' not found", config.id_var))
            })?
            .as_any()
            .downcast_ref::<Int64Array>()
            .ok_or_else(|| DidError::Specification("id column must be Int64".into()))?;
        Ok(Self { group, time, id })
    }
}
