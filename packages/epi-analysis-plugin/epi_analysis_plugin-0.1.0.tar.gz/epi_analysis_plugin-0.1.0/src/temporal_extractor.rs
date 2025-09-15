use std::num::NonZeroUsize;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use anyhow::{anyhow, Result};
use parking_lot::RwLock;
use polars::prelude::*;
use regex::Regex;

// LRU cache for loaded registries
static REGISTRY_CACHE: std::sync::LazyLock<RwLock<lru::LruCache<String, Arc<DataFrame>>>> =
    std::sync::LazyLock::new(|| RwLock::new(lru::LruCache::new(NonZeroUsize::new(8).unwrap())));

/// Extract temporal data with dynamic year ranges - main public function
pub fn extract_temporal_data_dynamic_year(
    df: &DataFrame,
    identifier_col: &str,
    index_date_col: &str,
    registry_pattern: &str,
    variable_col: &str,
    temporal_range: (i64, i64),
    additional_cols: Option<&[String]>,
    use_cache: bool,
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

    // Create target years dataframe
    let df_targets = create_target_years(df, identifier_col, index_date_col, temporal_range)?;

    // Load registry files
    let registry = load_registry_glob(registry_pattern, use_cache)?;

    // Validate required columns in registry
    let mut required_registry_cols = vec![identifier_col, "ARET", variable_col];
    if let Some(additional) = additional_cols {
        required_registry_cols.extend(additional.iter().map(std::string::String::as_str));
    }

    for col_name in &required_registry_cols {
        let col_str = PlSmallStr::from(*col_name);
        if !registry.get_column_names().contains(&&col_str) {
            return Err(anyhow!("Registry missing required column: {}", col_name));
        }
    }

    // Select only needed columns from registry
    let mut select_cols = vec![identifier_col, "ARET", variable_col];
    if let Some(additional) = additional_cols {
        select_cols.extend(additional.iter().map(std::string::String::as_str));
    }

    let registry_selected = registry.select(select_cols)?;

    // Filter registry efficiently
    let registry_filtered = filter_registry(&registry_selected, &df_targets, identifier_col)?;

    // Join and return results
    let result = join_temporal_data(&df_targets, &registry_filtered, identifier_col)?;

    Ok(result)
}

/// Extract year from filename using regex
pub fn extract_year_from_filename(file_name: &str) -> Result<i32> {
    static YEAR_RE: std::sync::LazyLock<Regex> =
        std::sync::LazyLock::new(|| Regex::new(r"(19|20)\d{2}").unwrap());

    if let Some(m) = YEAR_RE.find(file_name) {
        let year_str = &file_name[m.start()..m.end()];
        let year: i32 = year_str.parse()?;
        Ok(year)
    } else {
        Err(anyhow!(
            "Could not extract year from filename: {}",
            file_name
        ))
    }
}

/// Load a single registry file into a `DataFrame`
pub fn load_registry_file(path: &Path) -> Result<DataFrame> {
    let ext = path
        .extension()
        .and_then(|s| s.to_str())
        .unwrap_or("")
        .to_lowercase();

    let file_year =
        extract_year_from_filename(path.file_name().and_then(|s| s.to_str()).unwrap_or(""))?;

    let mut df = match ext.as_str() {
        "parquet" => LazyFrame::scan_parquet(
            PlPath::from_str(path.to_str().unwrap()),
            ScanArgsParquet::default(),
        )?
        .collect()?,
        "ipc" | "feather" | "arrow" => LazyFrame::scan_ipc(
            PlPath::from_str(path.to_str().unwrap()),
            ScanArgsIpc::default(),
        )?
        .collect()?,
        other => return Err(anyhow!("Unsupported extension: {}", other)),
    };

    // Add ARET column if missing
    let aret_col = PlSmallStr::from_static("ARET");
    if !df.get_column_names().contains(&&aret_col) {
        df = df
            .lazy()
            .with_columns([lit(file_year).alias("ARET")])
            .collect()?;
    }

    Ok(df)
}

/// Load registry files matching a glob pattern
pub fn load_registry_glob(pattern: &str, use_cache: bool) -> Result<DataFrame> {
    if use_cache {
        let cached = {
            let mut cache = REGISTRY_CACHE.write();
            cache.get(pattern).cloned()
        };
        if let Some(cached) = cached {
            return Ok(cached.as_ref().clone());
        }
    }

    let mut paths: Vec<PathBuf> = glob::glob(pattern)?
        .filter_map(std::result::Result::ok)
        .collect();

    if paths.is_empty() {
        return Err(anyhow!("No files matched pattern: {}", pattern));
    }

    paths.sort(); // Deterministic order

    let mut dfs = Vec::with_capacity(paths.len());
    for path in &paths {
        let df = load_registry_file(path)?;
        dfs.push(df);
    }

    let lazy_dfs: Vec<LazyFrame> = dfs
        .into_iter()
        .map(polars::prelude::IntoLazy::lazy)
        .collect();
    let concatenated = concat(&lazy_dfs, UnionArgs::default())?.collect()?;

    if use_cache {
        REGISTRY_CACHE
            .write()
            .put(pattern.to_string(), Arc::new(concatenated.clone()));
    }

    Ok(concatenated)
}

/// Create target years dataframe with expanded temporal ranges
pub fn create_target_years(
    df: &DataFrame,
    identifier_col: &str,
    index_date_col: &str,
    temporal_range: (i64, i64),
) -> Result<DataFrame> {
    let (start_offset, end_offset) = temporal_range;

    if start_offset > end_offset {
        return Err(anyhow!("Invalid temporal range: start_offset > end_offset"));
    }

    // Ensure columns exist
    let id_col_str = PlSmallStr::from(identifier_col);
    let date_col_str = PlSmallStr::from(index_date_col);
    if !df.get_column_names().contains(&&id_col_str) {
        return Err(anyhow!("Identifier column '{}' not found", identifier_col));
    }
    if !df.get_column_names().contains(&&date_col_str) {
        return Err(anyhow!("Index date column '{}' not found", index_date_col));
    }

    let result = df
        .clone()
        .lazy()
        .with_columns([col(index_date_col).dt().year().alias("index_year")])
        .with_columns([
            (col("index_year") + lit(start_offset)).alias("start_year"),
            (col("index_year") + lit(end_offset)).alias("end_year"),
        ])
        .with_columns([int_ranges(
            col("start_year"),
            col("end_year") + lit(1),
            lit(1),
            DataType::Int32,
        )
        .alias("years_range")])
        .explode(by_name(["years_range"], true))
        .with_columns([
            col("years_range").alias("ARET"),
            (col("years_range") - col("index_year")).alias("RELATIVE_YEAR"),
        ])
        .select([
            col(identifier_col),
            col(index_date_col),
            col("ARET"),
            col("RELATIVE_YEAR"),
        ])
        .unique(None, UniqueKeepStrategy::First)
        .collect()?;

    Ok(result)
}

/// Filter registry to relevant identifiers and years (independently) — fully lazy
pub fn filter_registry(
    registry: &DataFrame,
    df_targets: &DataFrame,
    identifier_col: &str,
) -> PolarsResult<DataFrame> {
    let lf_registry = registry.clone().lazy();
    let lf_targets = df_targets.clone().lazy();

    // Use semi-join for efficient filtering instead of is_in with literals
    let filtered = lf_registry
        .join(
            lf_targets
                .select([col(identifier_col), col("ARET")])
                .unique(None, UniqueKeepStrategy::First),
            [col(identifier_col), col("ARET")],
            [col(identifier_col), col("ARET")],
            JoinArgs::new(JoinType::Semi),
        )
        .collect()?;

    Ok(filtered)
}

/// Join target dataframe with filtered registry
pub fn join_temporal_data(
    df_targets: &DataFrame,
    registry_filtered: &DataFrame,
    identifier_col: &str,
) -> Result<DataFrame> {
    let result = df_targets
        .clone()
        .lazy()
        .join(
            registry_filtered.clone().lazy(),
            [col(identifier_col), col("ARET")],
            [col(identifier_col), col("ARET")],
            JoinArgs::new(JoinType::Left),
        )
        .sort(
            [identifier_col, "RELATIVE_YEAR"],
            SortMultipleOptions::default(),
        )
        .collect()?;

    Ok(result)
}

/// Batch processing for large datasets
pub fn extract_temporal_data_batched(
    df: &DataFrame,
    batch_size: usize,
    identifier_col: &str,
    index_date_col: &str,
    registry_pattern: &str,
    variable_col: &str,
    temporal_range: (i64, i64),
    additional_cols: Option<&[String]>,
    use_cache: bool,
) -> Result<DataFrame> {
    if df.height() <= batch_size {
        return extract_temporal_data_dynamic_year(
            df,
            identifier_col,
            index_date_col,
            registry_pattern,
            variable_col,
            temporal_range,
            additional_cols,
            use_cache,
        );
    }

    let mut results = Vec::new();
    let total_rows = df.height();

    for i in (0..total_rows).step_by(batch_size) {
        let end = std::cmp::min(i + batch_size, total_rows);
        let batch = df.slice(i as i64, end - i);

        let batch_result = extract_temporal_data_dynamic_year(
            &batch,
            identifier_col,
            index_date_col,
            registry_pattern,
            variable_col,
            temporal_range,
            additional_cols,
            use_cache,
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
