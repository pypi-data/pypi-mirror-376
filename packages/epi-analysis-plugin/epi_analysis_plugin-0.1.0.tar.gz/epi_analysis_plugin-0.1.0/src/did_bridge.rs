use std::sync::Arc;

use anyhow::{anyhow, Result};
use arrow::array::{
    ArrayRef, BooleanArray, Date32Array, Float64Array, Int64Array, LargeStringArray,
};
use arrow::datatypes::{DataType as ArrowDataType, Field as ArrowField, Schema as ArrowSchema};
use arrow::record_batch::RecordBatch;
use polars::prelude::*;

fn series_to_arrow(s: &Series) -> Result<(ArrayRef, ArrowField)> {
    let name = s.name().as_str().to_string();
    let nullable = s.null_count() > 0;
    match s.dtype() {
        DataType::Int64 => {
            let ca = s.i64()?;
            let arr = Int64Array::from_iter(ca);
            let field = ArrowField::new(name, ArrowDataType::Int64, nullable);
            Ok((Arc::new(arr) as ArrayRef, field))
        },
        DataType::Float64 => {
            let ca = s.f64()?;
            let arr = Float64Array::from_iter(ca);
            let field = ArrowField::new(name, ArrowDataType::Float64, nullable);
            Ok((Arc::new(arr) as ArrayRef, field))
        },
        DataType::Boolean => {
            let ca = s.bool()?;
            let arr = BooleanArray::from_iter(ca);
            let field = ArrowField::new(name, ArrowDataType::Boolean, nullable);
            Ok((Arc::new(arr) as ArrayRef, field))
        },
        DataType::String => {
            let ca = s.str()?;
            let arr = LargeStringArray::from_iter(ca);
            let field = ArrowField::new(name, ArrowDataType::LargeUtf8, nullable);
            Ok((Arc::new(arr) as ArrayRef, field))
        },
        DataType::Date => {
            // Cast to physical i32 for safe iteration
            let phys = s.cast(&DataType::Int32)?;
            let ca = phys.i32()?;
            let arr = Date32Array::from_iter(ca);
            let field = ArrowField::new(name, ArrowDataType::Date32, nullable);
            Ok((Arc::new(arr) as ArrayRef, field))
        },
        // Add more types as needed; for MVP restrict to DID-relevant types
        dt => Err(anyhow!(
            "Unsupported data type in DID bridge: {:?} for column {}",
            dt,
            s.name()
        )),
    }
}

pub fn polars_df_to_arrow1_batch(df: &DataFrame) -> Result<RecordBatch> {
    // Ensure single chunks to keep things simple in MVP
    let mut df = df.clone();
    df.rechunk_mut();

    let mut fields = Vec::with_capacity(df.width());
    let mut arrays: Vec<ArrayRef> = Vec::with_capacity(df.width());

    for c in df.get_columns() {
        let col = df
            .column(c.name())
            .map_err(|e| anyhow!("Failed to get column {}: {e}", c.name()))?;
        let s = col
            .as_series()
            .ok_or_else(|| anyhow!("Failed to view column {} as series", c.name()))?;
        let (arr, field) = series_to_arrow(s)?;
        arrays.push(arr);
        fields.push(field);
    }

    let schema = Arc::new(ArrowSchema::new(fields));
    let batch = RecordBatch::try_new(schema, arrays)?;
    Ok(batch)
}
