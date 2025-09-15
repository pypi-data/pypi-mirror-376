use polars::prelude::*;

/// Convert a column to "days since epoch" (Int32).
/// - If it's already `Date`, cast directly to Int32.
/// - If it's `Datetime`, convert ms → days and cast to Int32.
/// - Otherwise, leave unchanged.
pub fn col_to_days_since_epoch(df: &DataFrame, colname: &str) -> PolarsResult<Expr> {
    let dtype = df.schema().get(colname).unwrap();

    let expr = match dtype {
        DataType::Date => {
            // Date is already stored as days since epoch (i32), keep as Int32
            col(colname).cast(DataType::Int32).alias(colname)
        },
        DataType::Datetime(_, _) => {
            // Convert ms → days and cast to Int32
            (col(colname).dt().timestamp(TimeUnit::Milliseconds) / lit(86_400_000i64))
                .cast(DataType::Int32)
                .alias(colname)
        },
        _ => {
            // Leave unchanged
            col(colname)
        },
    };

    Ok(expr)
}

/// Convert a column to i32 days since epoch, handling both Date and Int32/Int64 types
pub fn col_to_i32_days(df: &DataFrame, colname: &str) -> PolarsResult<Expr> {
    let dtype = df.schema().get(colname).unwrap();

    let expr = match dtype {
        DataType::Date => {
            // Date is already stored as days since epoch (i32)
            col(colname).alias(colname)
        },
        DataType::Int32 => {
            // Already i32, assume it's days since epoch
            col(colname).alias(colname)
        },
        DataType::Int64 => {
            // Convert i64 to i32 (assume it's days since epoch)
            col(colname).cast(DataType::Int32).alias(colname)
        },
        DataType::Datetime(_, _) => {
            // Convert datetime to days since epoch as i32
            (col(colname).dt().timestamp(TimeUnit::Milliseconds) / lit(86_400_000i64))
                .cast(DataType::Int32)
                .alias(colname)
        },
        _ => {
            // For other types, try to cast to i32
            col(colname).cast(DataType::Int32).alias(colname)
        },
    };

    Ok(expr)
}
