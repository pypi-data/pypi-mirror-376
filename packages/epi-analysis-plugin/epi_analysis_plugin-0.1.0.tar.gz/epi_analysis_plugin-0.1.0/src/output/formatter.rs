use polars::prelude::*;

/// Create the requested output format: `MATCH_INDEX`, PNR, ROLE, `INDEX_DATE`
/// This transforms the matched cases into the long format requested by the user
pub fn create_match_output_format(matched_cases_df: &DataFrame) -> PolarsResult<DataFrame> {
    // Check if the DataFrame already has the correct columns
    let column_names: Vec<&str> = matched_cases_df
        .get_column_names()
        .iter()
        .map(|s| s.as_str())
        .collect();

    if column_names.contains(&"MATCH_INDEX")
        && column_names.contains(&"PNR")
        && column_names.contains(&"ROLE")
        && column_names.contains(&"INDEX_DATE")
    {
        // Already in the correct format, just return it
        return Ok(matched_cases_df.clone());
    }

    // Check if we have the "matched_controls" format that needs transformation
    if !column_names.contains(&"matched_controls") {
        polars_bail!(ComputeError: "Expected either final format (MATCH_INDEX, PNR, ROLE, INDEX_DATE) or intermediate format with 'matched_controls' column");
    }

    // Step 1: Create records for cases (include all cases, even those without matches)
    let cases_long = matched_cases_df
        .clone()
        .lazy()
        .with_row_index("MATCH_INDEX", Some(1)) // Start match index at 1
        .select([
            col("MATCH_INDEX"),
            col("PNR"),
            lit("case").alias("ROLE"),
            col("SCD_DATE").alias("INDEX_DATE"),
        ])
        .collect()?;

    // Step 2: Create records for controls by exploding the matched_controls list
    let controls_long = matched_cases_df
        .clone()
        .lazy()
        .with_row_index("MATCH_INDEX", Some(1)) // Same match index as cases
        .select([
            col("MATCH_INDEX"),
            col("SCD_DATE").alias("INDEX_DATE"), // Index date from the case
            col("matched_controls"),
        ])
        .filter(col("matched_controls").is_not_null()) // Only cases that have matches
        .explode(by_name(["matched_controls"], true))
        .filter(col("matched_controls").is_not_null())
        .with_columns([
            col("matched_controls").alias("PNR"),
            lit("control").alias("ROLE"),
        ])
        .select([
            col("MATCH_INDEX"),
            col("PNR"),
            col("ROLE"),
            col("INDEX_DATE"),
        ])
        .collect()?;

    // Step 3: Combine cases and controls
    let combined_output = concat(
        [cases_long.lazy(), controls_long.lazy()],
        UnionArgs::default(),
    )?
    .sort(["MATCH_INDEX", "ROLE"], SortMultipleOptions::default()) // Sort by match index, then role (case first)
    .collect()?;

    Ok(combined_output)
}
