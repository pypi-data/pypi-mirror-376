use arrow::record_batch::RecordBatch;

use crate::{DidConfig, DidError};

pub fn validate_schema(data: &RecordBatch, config: &DidConfig) -> Result<(), DidError> {
    let schema = data.schema();
    let required = [
        config.outcome_var.as_str(),
        config.time_var.as_str(),
        config.id_var.as_str(),
    ];
    for name in required {
        if schema.field_with_name(name).is_err() {
            return Err(DidError::Specification(format!(
                "Variable '{name}' not found in data"
            )));
        }
    }
    if let Some(g) = &config.group_var {
        if schema.field_with_name(g).is_err() {
            return Err(DidError::Specification(format!(
                "Variable '{g}' not found in data"
            )));
        }
    }
    for var in &config.control_vars {
        if schema.field_with_name(var).is_err() {
            return Err(DidError::Specification(format!(
                "Variable '{var}' not found in data"
            )));
        }
    }
    Ok(())
}
