use std::path::Path;

use anyhow::{anyhow, Result};
use polars::prelude::*;

pub mod categorization;

use crate::extractors::education::categorization::{
    create_hfaudd_lookup, hfaudd_to_category, is_temporally_valid, EducationLevel,
};
use crate::utilities::{col_to_days_since_epoch, col_to_i32_days};

/// Education record with temporal validity
#[derive(Debug, Clone)]
pub struct EducationRecord {
    pub hfaudd: String,
    pub level_code: Option<u8>,
    pub level: EducationLevel,
    pub valid_from: Option<i32>, // HF_VFRA as days since epoch
    pub valid_to: Option<i32>,   // HF_VTIL as days since epoch
}

/// Extract highest attained education level from UDDF register data
pub fn extract_highest_education_level(
    df: &DataFrame,
    identifier_col: &str,
    index_date_col: &str,
    uddf_file_path: &str,
) -> Result<DataFrame> {
    extract_highest_education_level_detailed(
        df,
        identifier_col,
        index_date_col,
        uddf_file_path,
        false,
    )
}

/// Extract highest attained education level from UDDF register data with optional detailed output
pub fn extract_highest_education_level_detailed(
    df: &DataFrame,
    identifier_col: &str,
    index_date_col: &str,
    uddf_file_path: &str,
    include_hfaudd_code: bool,
) -> Result<DataFrame> {
    // Validate inputs
    if df.height() == 0 {
        return Err(anyhow!("Input dataframe is empty"));
    }

    let required_cols = vec![identifier_col, index_date_col];
    for col_name in &required_cols {
        let col_str = PlSmallStr::from(*col_name);
        if !df.get_column_names().contains(&&col_str) {
            return Err(anyhow!("Required column '{}' not found", col_name));
        }
    }

    // Load HFAUDD categorization lookup
    let hfaudd_lookup = create_hfaudd_lookup()?;

    // Load UDDF file and normalize date columns
    let uddf_path = Path::new(uddf_file_path);
    let mut uddf_df = if uddf_path.extension().and_then(|s| s.to_str()) == Some("parquet") {
        LazyFrame::scan_parquet(PlPath::from_str(uddf_file_path), ScanArgsParquet::default())?
            .collect()?
    } else if uddf_path
        .extension()
        .and_then(|s| s.to_str())
        .map(|s| s.to_lowercase())
        == Some("ipc".to_string())
        || uddf_path.extension().and_then(|s| s.to_str()) == Some("feather")
        || uddf_path.extension().and_then(|s| s.to_str()) == Some("arrow")
    {
        LazyFrame::scan_ipc(PlPath::from_str(uddf_file_path), ScanArgsIpc::default())?.collect()?
    } else {
        return Err(anyhow!(
            "Unsupported UDDF file format. Use .parquet or .ipc/.feather/.arrow"
        ));
    };

    // Normalize HF_VFRA and HF_VTIL columns to i32 days since epoch
    let vfra_expr = col_to_i32_days(&uddf_df, "HF_VFRA")?;
    let vtil_expr = col_to_i32_days(&uddf_df, "HF_VTIL")?;

    uddf_df = uddf_df
        .lazy()
        .with_columns([vfra_expr, vtil_expr])
        .collect()?;

    // Validate UDDF columns
    let required_uddf_cols = vec![identifier_col, "HFAUDD", "HF_VFRA", "HF_VTIL"];
    for col_name in &required_uddf_cols {
        let col_str = PlSmallStr::from(*col_name);
        if !uddf_df.get_column_names().contains(&&col_str) {
            return Err(anyhow!("UDDF file missing required column: {}", col_name));
        }
    }

    // Process each individual to find highest education level
    let mut results: Vec<(String, String, Option<String>, Option<u8>)> = Vec::new();

    // Convert input dataframe to extract individual info and handle date conversion
    let individuals = df
        .clone()
        .lazy()
        .with_columns([col_to_days_since_epoch(df, index_date_col)?])
        .collect()?;

    let pnrs = individuals.column(identifier_col)?.str()?;
    let index_dates = individuals.column(index_date_col)?.i32()?;

    for i in 0..individuals.height() {
        if let (Some(pnr), Some(index_date)) = (pnrs.get(i), index_dates.get(i)) {
            let index_date_i32 = index_date;

            // Get all education records for this individual
            let person_education = uddf_df
                .clone()
                .lazy()
                .filter(col(identifier_col).eq(lit(pnr)))
                .collect()?;

            // Parse education records
            let mut education_records = Vec::new();

            if person_education.height() > 0 {
                let hfaudd_col = person_education.column("HFAUDD")?.str()?;
                let vfra_col = person_education.column("HF_VFRA")?.date()?;
                let vtil_col = person_education.column("HF_VTIL")?.date()?;

                for j in 0..person_education.height() {
                    if let Some(hfaudd_str) = hfaudd_col.get(j) {
                        let level_code = hfaudd_lookup.get(hfaudd_str).copied();
                        let level = hfaudd_to_category(hfaudd_str, level_code);

                        let valid_from = vfra_col.phys.get(j);
                        let valid_to = vtil_col.phys.get(j);

                        let record = EducationRecord {
                            hfaudd: hfaudd_str.to_string(),
                            level_code,
                            level,
                            valid_from,
                            valid_to,
                        };

                        education_records.push(record);
                    }
                }
            }

            // Filter temporally valid records and find highest level
            let valid_records: Vec<_> = education_records
                .into_iter()
                .filter(|record| is_temporally_valid(record, index_date_i32))
                .collect();

            // Find highest education level (exclude unknown/missing)
            let highest_record = valid_records
                .iter()
                .filter(|record| record.level != EducationLevel::Unknown)
                .max_by_key(|record| record.level.priority());

            let (highest_level, highest_hfaudd, highest_level_code) =
                if let Some(record) = highest_record {
                    (
                        &record.level,
                        Some(record.hfaudd.clone()),
                        record.level_code,
                    )
                } else {
                    (&EducationLevel::Unknown, None, None)
                };

            results.push((
                pnr.to_string(),
                highest_level.as_str().to_string(),
                highest_hfaudd,
                highest_level_code,
            ));
        }
    }

    // Create result DataFrame
    let result_pnrs: Vec<String> = results.iter().map(|(pnr, _, _, _)| pnr.clone()).collect();
    let result_levels: Vec<String> = results
        .iter()
        .map(|(_, level, _, _)| level.clone())
        .collect();

    let mut result_df = df! {
        identifier_col => result_pnrs,
        "highest_education_level" => result_levels,
    }?;

    // Optionally include HFAUDD code and level code
    if include_hfaudd_code {
        let result_hfaudd: Vec<Option<String>> = results
            .iter()
            .map(|(_, _, hfaudd, _)| hfaudd.clone())
            .collect();
        let result_level_codes: Vec<Option<u8>> = results
            .iter()
            .map(|(_, _, _, level_code)| *level_code)
            .collect();

        result_df = result_df
            .lazy()
            .with_columns([
                Series::new("hfaudd_code".into(), &result_hfaudd).lit(),
                Series::new("level_code".into(), &result_level_codes).lit(),
            ])
            .collect()?;
    }

    // Join with original dataframe
    let final_result = df
        .clone()
        .lazy()
        .join(
            result_df.lazy(),
            [col(identifier_col)],
            [col(identifier_col)],
            JoinArgs::new(JoinType::Left),
        )
        .collect()?;

    Ok(final_result)
}

/// Batch processing version for large datasets
pub fn extract_highest_education_level_batched(
    df: &DataFrame,
    batch_size: usize,
    identifier_col: &str,
    index_date_col: &str,
    uddf_file_path: &str,
) -> Result<DataFrame> {
    extract_highest_education_level_batched_detailed(
        df,
        batch_size,
        identifier_col,
        index_date_col,
        uddf_file_path,
        false,
    )
}

/// Batch processing version for large datasets with detailed output option
pub fn extract_highest_education_level_batched_detailed(
    df: &DataFrame,
    batch_size: usize,
    identifier_col: &str,
    index_date_col: &str,
    uddf_file_path: &str,
    include_hfaudd_code: bool,
) -> Result<DataFrame> {
    if df.height() <= batch_size {
        return extract_highest_education_level_detailed(
            df,
            identifier_col,
            index_date_col,
            uddf_file_path,
            include_hfaudd_code,
        );
    }

    let mut results = Vec::new();
    let total_rows = df.height();

    for i in (0..total_rows).step_by(batch_size) {
        let end = std::cmp::min(i + batch_size, total_rows);
        let batch = df.slice(i as i64, end - i);

        let batch_result = extract_highest_education_level_detailed(
            &batch,
            identifier_col,
            index_date_col,
            uddf_file_path,
            include_hfaudd_code,
        )?;

        results.push(batch_result);
    }

    let lazy_results: Vec<LazyFrame> = results
        .into_iter()
        .map(polars::prelude::IntoLazy::lazy)
        .collect();
    let combined = concat(&lazy_results, UnionArgs::default())?.collect()?;
    Ok(combined)
}
