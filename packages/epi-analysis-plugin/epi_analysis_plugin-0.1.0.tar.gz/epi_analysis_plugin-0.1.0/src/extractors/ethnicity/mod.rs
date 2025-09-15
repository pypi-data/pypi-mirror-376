use std::borrow::Cow;

use anyhow::{anyhow, Result};
use polars::prelude::*;

pub mod categorization;

use crate::extractors::ethnicity::categorization::{
    create_opr_land_lookup, ie_type_to_status, EthnicityCategory, ImmigrationStatus, OriginCategory,
};
use crate::temporal_extractor::{create_target_years, load_registry_glob};

/// Extract ethnicity categories from BEF register data with temporal validity
pub fn extract_ethnicity_temporal(
    df: &DataFrame,
    identifier_col: &str,
    index_date_col: &str,
    bef_registry_pattern: &str,
    temporal_range: (i64, i64),
) -> Result<DataFrame> {
    // Validate inputs
    if df.height() == 0 {
        return Err(anyhow!("Input dataframe is empty"));
    }
    let required_cols = vec![identifier_col, index_date_col, "CPR_MODER", "CPR_FADER"];
    for col_name in &required_cols {
        let col_str = PlSmallStr::from(*col_name);
        if !df.get_column_names().contains(&&col_str) {
            return Err(anyhow!("Required column '{}' not found", col_name));
        }
    }

    // Create target years dataframe
    let df_targets = create_target_years(df, identifier_col, index_date_col, temporal_range)?;

    // Load BEF registry files using glob pattern
    let bef_df = load_registry_glob(bef_registry_pattern, false)?;

    // Validate BEF columns (per-individual rows)
    let required_bef_cols = vec![
        identifier_col, // CPR/PNR
        "OPR_LAND",     // origin country code
        "IE_TYPE",      // immigration status (child rows)
        "ARET",         // Year column
    ];
    for col_name in &required_bef_cols {
        let col_str = PlSmallStr::from(*col_name);
        if !bef_df.get_column_names().contains(&&col_str) {
            return Err(anyhow!(
                "BEF registry missing required column: {}",
                col_name
            ));
        }
    }

    // Prepare BEF views: child rows and parent lookups (parent CPRs come from input df)
    let bef_child = bef_df.clone().lazy().select([
        col(identifier_col),
        col("ARET"),
        col("OPR_LAND"),
        col("IE_TYPE"),
    ]);

    let bef_mother = bef_df.clone().lazy().select([
        col(identifier_col).alias("CPR_MODER"),
        col("ARET"),
        col("OPR_LAND").alias("MOR_OPR_LAND"),
    ]);

    let bef_father = bef_df.lazy().select([
        col(identifier_col).alias("CPR_FADER"),
        col("ARET"),
        col("OPR_LAND").alias("FAR_OPR_LAND"),
    ]);

    // Attach parent CPRs from input df to targets so we can join to parents in BEF
    let df_targets_ext = df_targets
        .lazy()
        .join(
            df.clone()
                .lazy()
                .select([col(identifier_col), col("CPR_MODER"), col("CPR_FADER")]),
            [col(identifier_col)],
            [col(identifier_col)],
            JoinArgs::new(JoinType::Left),
        )
        .collect()?;

    // Join target years → child rows → mother/father OPR via their CPRs for the same year
    let joined_df = df_targets_ext
        .lazy()
        .join(
            bef_child,
            [col(identifier_col), col("ARET")],
            [col(identifier_col), col("ARET")],
            JoinArgs::new(JoinType::Left),
        )
        .join(
            bef_mother,
            [col("CPR_MODER"), col("ARET")],
            [col("CPR_MODER"), col("ARET")],
            JoinArgs::new(JoinType::Left),
        )
        .join(
            bef_father,
            [col("CPR_FADER"), col("ARET")],
            [col("CPR_FADER"), col("ARET")],
            JoinArgs::new(JoinType::Left),
        )
        .collect()?;

    // Create OPR_LAND lookup table
    let opr_land_lookup = create_opr_land_lookup()?;

    // Helper closure for mapping OPR_LAND codes to origin categories
    let opr_land_to_origin = {
        let opr_land_lookup = opr_land_lookup;
        move |col: Column| {
            let s = col.as_materialized_series();
            let ca = s.str()?; // or s.str()? depending on version
            let out = ca.apply(|opt_val| {
                opt_val.map(|val| {
                    let category = opr_land_lookup.get(val).unwrap_or(&OriginCategory::Unknown);
                    match category {
                        OriginCategory::Danish => Cow::Borrowed("Danish"),
                        OriginCategory::Western => Cow::Borrowed("Western"),
                        OriginCategory::NonWestern => Cow::Borrowed("NonWestern"),
                        OriginCategory::Unknown => Cow::Borrowed("Unknown"),
                    }
                })
            });
            Ok(Some(out.into_column()))
        }
    };

    // Helper closure for mapping IE_TYPE to immigration status
    let ie_type_to_status_str = move |col: Column| {
        let s = col.as_materialized_series();
        let ca = s.i32()?; // Int32Chunked

        let out: StringChunked = ca
            .into_iter()
            .map(|opt_val| {
                opt_val.map(|val| match ie_type_to_status(Some(val)) {
                    ImmigrationStatus::Danish => Cow::Borrowed("Danish"),
                    ImmigrationStatus::Immigrant => Cow::Borrowed("Immigrant"),
                    ImmigrationStatus::Descendant => Cow::Borrowed("Descendant"),
                    ImmigrationStatus::Unknown => Cow::Borrowed("Unknown"),
                })
            })
            .collect();

        Ok(Some(out.into_column()))
    };

    // Apply categorization logic
    let result_df = joined_df
        .lazy()
        // Cast IE_TYPE robustly to Int32 to handle i64/utf8 inputs
        .with_columns([col("IE_TYPE").cast(DataType::Int32).alias("IE_TYPE_I32")])
        .with_columns([
            col("OPR_LAND")
                .apply(
                    opr_land_to_origin.clone(),
                    GetOutput::from_type(DataType::String),
                )
                .alias("individual_origin"),
            col("MOR_OPR_LAND")
                .apply(
                    opr_land_to_origin.clone(),
                    GetOutput::from_type(DataType::String),
                )
                .alias("mother_origin"),
            col("FAR_OPR_LAND")
                .apply(opr_land_to_origin, GetOutput::from_type(DataType::String))
                .alias("father_origin"),
            col("IE_TYPE_I32")
                .apply(
                    ie_type_to_status_str,
                    GetOutput::from_type(DataType::String),
                )
                .alias("immigration_status"),
        ])
        .with_column(
            when(col("individual_origin").eq(lit("Danish")))
                .then(
                    when(
                        col("mother_origin")
                            .eq(lit("Danish"))
                            .and(col("father_origin").eq(lit("Danish"))),
                    )
                    .then(lit(EthnicityCategory::Danish.as_str()))
                    .otherwise(lit(EthnicityCategory::MixedBackground.as_str())),
                )
                .when(col("individual_origin").eq(lit("Western")))
                .then(
                    when(col("immigration_status").eq(lit("Immigrant")))
                        .then(lit(EthnicityCategory::WesternImmigrant.as_str()))
                        .when(col("immigration_status").eq(lit("Descendant")))
                        .then(lit(EthnicityCategory::WesternDescendant.as_str()))
                        .otherwise(lit(EthnicityCategory::Unknown.as_str())),
                )
                .when(col("individual_origin").eq(lit("NonWestern")))
                .then(
                    when(col("immigration_status").eq(lit("Immigrant")))
                        .then(lit(EthnicityCategory::NonWesternImmigrant.as_str()))
                        .when(col("immigration_status").eq(lit("Descendant")))
                        .then(lit(EthnicityCategory::NonWesternDescendant.as_str()))
                        .otherwise(lit(EthnicityCategory::Unknown.as_str())),
                )
                .otherwise(lit(EthnicityCategory::Unknown.as_str()))
                .alias("ethnicity_category"),
        )
        .select([
            col(identifier_col),
            col(index_date_col),
            col("ARET"),
            col("RELATIVE_YEAR"),
            col("ethnicity_category"),
        ])
        .sort(
            [identifier_col, "RELATIVE_YEAR"],
            SortMultipleOptions::default(),
        )
        .collect()?;

    Ok(result_df)
}
