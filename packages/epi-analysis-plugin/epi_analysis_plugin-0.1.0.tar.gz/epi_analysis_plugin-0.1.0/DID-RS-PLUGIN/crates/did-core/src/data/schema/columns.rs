use arrow::array::{BooleanArray, Float64Array, Int64Array, StringArray};
use arrow::record_batch::RecordBatch;

use crate::DidError;

pub fn int64_array<'a>(data: &'a RecordBatch, name: &str) -> Result<&'a Int64Array, DidError> {
    data.column_by_name(name)
        .ok_or_else(|| DidError::Specification(format!("column '{name}' not found")))?
        .as_any()
        .downcast_ref::<Int64Array>()
        .ok_or_else(|| DidError::Specification(format!("column '{name}' must be Int64")))
}

pub fn float64_array<'a>(data: &'a RecordBatch, name: &str) -> Result<&'a Float64Array, DidError> {
    data.column_by_name(name)
        .ok_or_else(|| DidError::Specification(format!("column '{name}' not found")))?
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| DidError::Specification(format!("column '{name}' must be Float64")))
}

pub fn bool_array<'a>(data: &'a RecordBatch, name: &str) -> Result<&'a BooleanArray, DidError> {
    data.column_by_name(name)
        .ok_or_else(|| DidError::Specification(format!("column '{name}' not found")))?
        .as_any()
        .downcast_ref::<BooleanArray>()
        .ok_or_else(|| DidError::Specification(format!("column '{name}' must be Boolean")))
}

pub fn string_array<'a>(data: &'a RecordBatch, name: &str) -> Result<&'a StringArray, DidError> {
    data.column_by_name(name)
        .ok_or_else(|| DidError::Specification(format!("column '{name}' not found")))?
        .as_any()
        .downcast_ref::<StringArray>()
        .ok_or_else(|| DidError::Specification(format!("column '{name}' must be String")))
}
