"""
Epidemiological Analysis Plugin

This plugin provides high-performance epidemiological analysis tools including:
- Case-control matching with proper risk-set sampling methodology
- Temporal data extraction from registry files with dynamic year ranges
- Optimized Rust implementations for large-scale data processing
"""

from __future__ import annotations

import json
from typing import Tuple

import polars as pl

from matching_plugin._internal import __version__ as __version__  # type: ignore
from matching_plugin._internal import format_match_output as _format_match_output_rust  # type: ignore
from matching_plugin._internal import match_scd_cases as _match_scd_cases_rust  # type: ignore
from matching_plugin._internal import (
    extract_temporal_data_dynamic_year_py as _extract_temporal_rust,
)  # type: ignore
from matching_plugin._internal import (
    extract_temporal_data_batched_py as _extract_temporal_batched_rust,
)  # type: ignore
from matching_plugin._internal import (
    extract_highest_education_level_py as _extract_education_rust,
)  # type: ignore
from matching_plugin._internal import (
    extract_highest_education_level_batched_py as _extract_education_batched_rust,
)  # type: ignore
from matching_plugin._internal import (
    extract_ethnicity_temporal_py as _extract_ethnicity_rust,
)  # type: ignore
from matching_plugin._internal import did_att_gt_py as _did_att_gt_rust  # type: ignore
from matching_plugin._internal import did_panel_info_py as _did_panel_info_rust  # type: ignore
from matching_plugin._internal import did_aggregate_py as _did_aggregate_rust  # type: ignore

__all__ = [
    "__version__",
    "complete_scd_matching_workflow",
    "create_match_output_format",
    "extract_temporal_data",
    "extract_temporal_data_batched",
    "extract_highest_education_level",
    "extract_highest_education_level_batched",
    "extract_ethnicity_categories",
    "compute_att_gt",
    "get_panel_info",
    "aggregate_effects",
]


def complete_scd_matching_workflow(
    mfr_data: pl.DataFrame,
    lpr_data: pl.DataFrame,
    vital_data: pl.DataFrame | None = None,
    matching_ratio: int = 5,
    birth_date_window_days: int = 30,
    parent_birth_date_window_days: int = 365,
    match_parent_birth_dates: bool = True,
    match_mother_birth_date_only: bool = False,
    require_both_parents: bool = False,
    match_parity: bool = True,
    match_birth_type: bool = False,
    algorithm: str = "spatial_index",
) -> pl.DataFrame:
    """
    Complete SCD case-control matching workflow with risk-set sampling.

    Combines MFR/LPR data, performs matching, and returns the standard output format.
    Cases are processed chronologically by diagnosis date to avoid immortal time bias.
    Optionally incorporates vital status data for temporal validity.

    Parameters
    ----------
    mfr_data : pl.DataFrame
        Output from process_mfr_data() - eligible population with parent info
    lpr_data : pl.DataFrame
        Output from process_lpr_data() - SCD status for all eligible children
    vital_data : pl.DataFrame, optional
        Output from process_vital_status() - death/emigration events for children and parents
        If provided, ensures individuals and parents are alive/present at matching time
    matching_ratio : int, default 5
        Number of controls to match per case
    birth_date_window_days : int, default 30
        Maximum difference in days between case and control birth dates
    parent_birth_date_window_days : int, default 365
        Maximum difference in days between parent birth dates
    match_parent_birth_dates : bool, default True
        Whether to match on parent birth dates
    match_mother_birth_date_only : bool, default False
        Whether to match only on maternal birth dates
    require_both_parents : bool, default False
        Whether both parents are required for matching
    match_parity : bool, default True
        Whether to match on parity (birth order)
    match_birth_type : bool, default False
        Whether to match on birth type (singleton, doubleton, tripleton, quadleton, multiple)
        Requires 'birth_type' column in input data
    algorithm : str, default "spatial_index"
        Algorithm to use for matching. Options:
        - "spatial_index": Optimized with parallel processing and spatial indexing
        - "partitioned_parallel": Ultra-optimized with advanced data structures (20-60% faster than spatial_index)

    Returns
    -------
    pl.DataFrame
        Output format: MATCH_INDEX, PNR, ROLE, INDEX_DATE
        - MATCH_INDEX: Unique identifier for each case-control group (1:X matching)
        - PNR: Person identifier
        - ROLE: "case" or "control"
        - INDEX_DATE: SCD diagnosis date from the case

        When vital_data is provided:
        - Ensures children and parents are alive/present at matching time
        - Individuals who died or emigrated before case diagnosis cannot serve as controls
        - Chronological processing with proper temporal validity
    """
    # Validate algorithm parameter
    valid_algorithms = ["spatial_index", "partitioned_parallel"]
    if algorithm not in valid_algorithms:
        raise ValueError(
            f"Invalid algorithm '{algorithm}'. Must be one of: {valid_algorithms}"
        )

    algorithm_names = {
        "spatial_index": "optimized with spatial indexing",
        "partitioned_parallel": "ultra-optimized with advanced data structures",
    }

    if vital_data is not None:
        print(
            f"Starting SCD case-control matching with vital status using {algorithm_names[algorithm]}..."
        )
    else:
        print(
            f"Starting SCD case-control matching using {algorithm_names[algorithm]}..."
        )

    # Combine MFR and LPR data
    combined_data = mfr_data.join(lpr_data, on="PNR", how="inner")
    print(f"Combined dataset: {len(combined_data):,} individuals")

    if vital_data is not None:
        print(f"Vital events data: {len(vital_data):,} events")

    # Perform risk-set sampling matching (with or without vital data)
    config = {
        "matching": {
            "birth_date_window_days": birth_date_window_days,
            "parent_birth_date_window_days": parent_birth_date_window_days,
            "match_parent_birth_dates": match_parent_birth_dates,
            "match_mother_birth_date_only": match_mother_birth_date_only,
            "require_both_parents": require_both_parents,
            "match_parity": match_parity,
            "match_birth_type": match_birth_type,
            "matching_ratio": matching_ratio,
        },
        "algorithm": algorithm,
    }

    matched_cases = _match_scd_cases_rust(combined_data, vital_data, json.dumps(config))

    # Transform to requested output format
    output_df = _format_match_output_rust(matched_cases)

    print(f"Matching complete: {len(output_df):,} records")
    print(f"Match groups: {output_df['MATCH_INDEX'].n_unique():,}")
    print(f"Cases: {(output_df['ROLE'] == 'case').sum():,}")
    print(f"Controls: {(output_df['ROLE'] == 'control').sum():,}")

    return output_df


def create_match_output_format(matched_cases_df: pl.DataFrame) -> pl.DataFrame:
    """
    Transform matched cases into the standard output format.

    Parameters
    ----------
    matched_cases_df : pl.DataFrame
        Matched cases DataFrame from the Rust matching functions

    Returns
    -------
    pl.DataFrame
        Standard output format: MATCH_INDEX, PNR, ROLE, INDEX_DATE
        - MATCH_INDEX: Unique identifier for each case-control group
        - PNR: Person identifier
        - ROLE: "case" or "control"
        - INDEX_DATE: SCD diagnosis date from the case (same for all members of match group)
    """
    return _format_match_output_rust(matched_cases_df)


def extract_temporal_data(
    df: pl.DataFrame,
    identifier_col: str,
    index_date_col: str,
    registry_path_pattern: str,
    variable_col: str,
    temporal_range: Tuple[int, int] = (-1, 1),
    additional_cols: list[str] | None = None,
    use_cache: bool = True,
) -> pl.DataFrame:
    """
    Extract temporal data from registry files with dynamic year ranges.

    This function provides high-performance extraction of temporal data from registry
    files based on dynamic year ranges relative to index dates. Uses optimized Rust
    implementation for efficient processing of large datasets.

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe with identifiers and index dates
    identifier_col : str
        Column name for unique identifiers (e.g., "PNR")
    index_date_col : str
        Column name for index dates (e.g., "diagnosis_date")
    registry_path_pattern : str
        Path pattern for registry files supporting glob patterns
        (e.g., "/data/registries/registry_*.parquet")
    variable_col : str
        Column name for the main variable to extract from registry
    temporal_range : Tuple[int, int], default=(-1, 1)
        Range of years relative to index year (start_offset, end_offset)
        - (-1, 1): Extract data from 1 year before to 1 year after index
        - (-2, 0): Extract data from 2 years before to index year
    additional_cols : list[str] | None, default=None
        Additional columns to extract from registry files
    use_cache : bool, default=True
        Whether to cache registry files for repeated calls (improves performance)

    Returns
    -------
    pl.DataFrame
        DataFrame with temporal data joined from registry files containing:
        - Original identifier and index date columns
        - ARET: Registry year for each extracted record
        - RELATIVE_YEAR: Years relative to index year (e.g., -1, 0, 1)
        - Variable columns from registry files

    Examples
    --------
    Extract prescription data around diagnosis dates:

    >>> cases_df = pl.DataFrame({
    ...     "PNR": ["123456", "789012"],
    ...     "diagnosis_date": ["2020-05-15", "2021-08-20"]
    ... })
    >>> prescriptions = extract_temporal_data(
    ...     df=cases_df,
    ...     identifier_col="PNR",
    ...     index_date_col="diagnosis_date",
    ...     registry_path_pattern="/data/prescriptions/lms_*.parquet",
    ...     variable_col="ATC_CODE",
    ...     temporal_range=(-2, 1),  # 2 years before to 1 year after
    ...     additional_cols=["DOSE", "STRENGTH"]
    ... )

    Extract hospital admissions with 1-year window:

    >>> admissions = extract_temporal_data(
    ...     df=cases_df,
    ...     identifier_col="PNR",
    ...     index_date_col="diagnosis_date",
    ...     registry_path_pattern="/data/lpr/lpr_*.ipc",
    ...     variable_col="ICD10_CODE",
    ...     temporal_range=(-1, 1)
    ... )

    Notes
    -----
    - Registry files must contain the identifier column and year information
    - If ARET column is missing, it will be inferred from filename
    - Supports .parquet, .ipc, .feather, and .arrow file formats
    - Files are processed in deterministic sorted order
    - Uses LRU caching for repeated registry file access
    """
    return _extract_temporal_rust(
        df,
        identifier_col,
        index_date_col,
        registry_path_pattern,
        variable_col,
        temporal_range,
        additional_cols,
        use_cache,
    )


def extract_temporal_data_batched(
    df: pl.DataFrame,
    batch_size: int,
    identifier_col: str,
    index_date_col: str,
    registry_path_pattern: str,
    variable_col: str,
    temporal_range: Tuple[int, int] = (-1, 1),
    additional_cols: list[str] | None = None,
    use_cache: bool = True,
) -> pl.DataFrame:
    """
    Extract temporal data in batches for memory-efficient processing of large datasets.

    This function processes large input DataFrames in smaller batches to manage memory
    usage while maintaining high performance through the Rust implementation.

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe with identifiers and index dates
    batch_size : int
        Number of rows to process per batch (e.g., 5000, 10000)
    identifier_col : str
        Column name for unique identifiers
    index_date_col : str
        Column name for index dates
    registry_path_pattern : str
        Path pattern for registry files (supports globbing)
    variable_col : str
        Column name for the main variable to extract from registry
    temporal_range : Tuple[int, int], default=(-1, 1)
        Range of years relative to index year (start_offset, end_offset)
    additional_cols : list[str] | None, default=None
        Additional columns to extract from registry files
    use_cache : bool, default=True
        Whether to cache registry files (highly recommended for batched processing)

    Returns
    -------
    pl.DataFrame
        Combined results from all batches with same structure as extract_temporal_data()

    Examples
    --------
    Process a large cohort in batches:

    >>> large_cohort = pl.read_parquet("large_cohort.parquet")  # 100,000+ rows
    >>> temporal_data = extract_temporal_data_batched(
    ...     df=large_cohort,
    ...     batch_size=5000,
    ...     identifier_col="PNR",
    ...     index_date_col="index_date",
    ...     registry_path_pattern="/data/registry_*.parquet",
    ...     variable_col="CODE",
    ...     temporal_range=(-1, 1),
    ...     use_cache=True  # Important for batched processing
    ... )

    Notes
    -----
    - Registry files are cached across batches when use_cache=True
    - Batch size should be chosen based on available memory
    - Smaller batches reduce memory usage but may increase processing time
    - Results are identical to non-batched processing
    """
    return _extract_temporal_batched_rust(
        df,
        batch_size,
        identifier_col,
        index_date_col,
        registry_path_pattern,
        variable_col,
        temporal_range,
        additional_cols,
        use_cache,
    )


def extract_highest_education_level(
    df: pl.DataFrame,
    identifier_col: str,
    index_date_col: str,
    uddf_file_path: str,
) -> pl.DataFrame:
    """
    Extract highest attained education level from UDDF register data.

    This function processes UDDF (education) register data to determine the highest
    education level achieved by each individual at their index date, accounting for
    temporal validity of education records.

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe with identifiers and index dates
    identifier_col : str
        Column name for unique identifiers (e.g., "PNR")
    index_date_col : str
        Column name for index dates (e.g., "diagnosis_date", "index_date")
    uddf_file_path : str
        Path to the UDDF register file (.parquet, .ipc, .feather, or .arrow)
        Must contain columns: identifier, HFAUDD, HF_VFRA, HF_VTIL

    Returns
    -------
    pl.DataFrame
        Original dataframe with added 'highest_education_level' column containing:
        - "short": Primary & lower secondary education (HFAUDD codes 10, 15)
        - "medium": Upper secondary & vocational education (HFAUDD codes 20, 30, 35)
        - "long": Tertiary education (HFAUDD codes 40, 50, 60, 70, 80)
        - "unknown": Missing or unclassified education (HFAUDD code 90)

    Notes
    -----
    Education Level Categorization (based on HFAUDD codes):
    - **Short education (10, 15)**: Primary & lower secondary, preparatory education
    - **Medium education (20, 30, 35)**: General upper secondary, vocational training
    - **Long education (40, 50, 60, 70, 80)**: Academy, bachelor's, master's, PhD programs
    - **Unknown (90)**: Missing, unclassified, or born ≤1920

    Temporal Validity:
    - Only education records valid at the index date are considered
    - Validity determined by: HF_VFRA ≤ index_date ≤ HF_VTIL
    - Missing HF_VFRA/HF_VTIL dates are treated as always valid

    Highest Level Selection:
    - Among temporally valid records, selects the highest education level
    - Excludes unknown/missing records (HFAUDD code 90) from ranking
    - If no valid education records exist, returns "unknown"

    Examples
    --------
    Extract education levels for a cohort at diagnosis:

    >>> cases_df = pl.DataFrame({
    ...     "PNR": ["123456789", "987654321"],
    ...     "diagnosis_date": ["2020-05-15", "2021-08-20"]
    ... })
    >>> education_df = extract_highest_education_level(
    ...     df=cases_df,
    ...     identifier_col="PNR",
    ...     index_date_col="diagnosis_date",
    ...     uddf_file_path="/data/registers/uddf_2021.parquet"
    ... )
    >>> print(education_df)
    │ PNR       │ diagnosis_date │ highest_education_level │
    │ str       │ date           │ str                     │
    ├───────────┼────────────────┼─────────────────────────┤
    │ 123456789 │ 2020-05-15     │ long                    │
    │ 987654321 │ 2021-08-20     │ medium                  │

    The function uses compile-time embedded HFAUDD categorization mapping for efficiency
    and processes ~5,370 different education codes automatically.
    """
    return _extract_education_rust(
        df,
        identifier_col,
        index_date_col,
        uddf_file_path,
    )


def extract_highest_education_level_batched(
    df: pl.DataFrame,
    batch_size: int,
    identifier_col: str,
    index_date_col: str,
    uddf_file_path: str,
) -> pl.DataFrame:
    """
    Extract highest education levels in batches for memory-efficient processing.

    This function processes large input DataFrames in smaller batches to manage memory
    usage while maintaining the same functionality as extract_highest_education_level.

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe with identifiers and index dates
    batch_size : int
        Number of rows to process per batch (e.g., 5000, 10000)
    identifier_col : str
        Column name for unique identifiers
    index_date_col : str
        Column name for index dates
    uddf_file_path : str
        Path to the UDDF register file

    Returns
    -------
    pl.DataFrame
        Combined results from all batches with same structure as extract_highest_education_level()

    Examples
    --------
    Process a large cohort in batches:

    >>> large_cohort = pl.read_parquet("large_cohort.parquet")  # 100,000+ rows
    >>> education_levels = extract_highest_education_level_batched(
    ...     df=large_cohort,
    ...     batch_size=10000,
    ...     identifier_col="PNR",
    ...     index_date_col="index_date",
    ...     uddf_file_path="/data/uddf_register.parquet"
    ... )

    Notes
    -----
    - Batch size should be chosen based on available memory
    - Smaller batches reduce memory usage but may increase processing time
    - Results are identical to non-batched processing
    - UDDF register file is loaded once per batch for efficiency
    """
    return _extract_education_batched_rust(
        df,
        batch_size,
        identifier_col,
        index_date_col,
        uddf_file_path,
    )


def extract_ethnicity_categories(
    df: pl.DataFrame,
    identifier_col: str,
    index_date_col: str,
    bef_registry_pattern: str,
    temporal_range: tuple[int, int] = (-1, 1),
) -> pl.DataFrame:
    """
    Extract SEPLINE-compliant ethnicity categories from BEF with parental lookups.

    For each individual/year window around the index date, this function:
    - Looks up the child's BEF row to get `OPR_LAND`, `IE_TYPE`, and parent CPRs
    - Looks up the mother's/father's BEF rows (by CPR) for the same `ARET` to get their `OPR_LAND`
    - Maps `OPR_LAND` to Danish/Western/Non-Western categories via compiled mapping
    - Applies SEPLINE rules using parent origins and `IE_TYPE`

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe with identifiers and index dates
    identifier_col : str
        Column name for identifiers (CPR/PNR)
    index_date_col : str
        Column name for index dates
    bef_registry_pattern : str
        Glob pattern to BEF files (e.g., "/data/bef_*.parquet")
    temporal_range : tuple[int, int], default (-1, 1)
        Year offsets around index year to search (inclusive)

    Returns
    -------
    pl.DataFrame
        Columns: identifier_col, index_date_col, ARET, RELATIVE_YEAR, ethnicity_category
    """
    return _extract_ethnicity_rust(
        df,
        identifier_col,
        index_date_col,
        bef_registry_pattern,
        temporal_range,
    )


def compute_att_gt(df: pl.DataFrame, config: dict | str) -> pl.DataFrame:
    """
    Compute ATT(g,t) using did-core on a Polars DataFrame.

    Parameters
    ----------
    df : pl.DataFrame
        Input data with columns matching did-core configuration
    config : dict | str
        JSON config or dict serializable to did-core's DidConfig

    Returns
    -------
    pl.DataFrame
        Columns: group, time, att, se, t_stat, p_value, conf_low, conf_high
    """
    cfg_json = config if isinstance(config, str) else json.dumps(config)
    return _did_att_gt_rust(df, cfg_json)


def get_panel_info(df: pl.DataFrame, config: dict | str) -> pl.DataFrame:
    """
    Return panel diagnostics based on did-core preprocessing.

    Returns columns: panel_type, is_balanced, n_periods
    """
    cfg_json = config if isinstance(config, str) else json.dumps(config)
    return _did_panel_info_rust(df, cfg_json)


def aggregate_effects(
    df: pl.DataFrame,
    config: dict | str,
    kind: str = "simple",
    confidence: float = 0.95,
    uniform_bands: bool = False,
) -> pl.DataFrame:
    """
    Aggregate ATT(g,t) from did-core using the original DataFrame and config.

    Parameters
    ----------
    df : pl.DataFrame
        Input data with columns matching did-core configuration.
    config : dict | str
        JSON config or dict serializable to did-core's DidConfig.
    kind : str
        One of: "simple", "group", "dynamic" (aka "event"), "calendar".
    confidence : float
        Confidence level for bands (e.g., 0.95).
    uniform_bands : bool
        Use uniform bands where supported.

    Returns
    -------
    pl.DataFrame
        Columns: group, time, event_time, att, se, conf_low, conf_high, is_overall
    """
    cfg_json = config if isinstance(config, str) else json.dumps(config)
    return _did_aggregate_rust(df, cfg_json, kind, confidence, uniform_bands)
