pub mod core;
pub mod partitioned_parallel;
pub mod shared;
pub mod spatial_index;
pub mod utils;

use polars::prelude::*;

use crate::config::{MatchingAlgorithm, WorkflowConfig};

/// Unified matching function that dispatches to the selected algorithm
pub fn match_cases(
    mfr_lpr_df: &DataFrame,
    vital_events_df: Option<&DataFrame>,
    config: &WorkflowConfig,
) -> PolarsResult<DataFrame> {
    match config.algorithm {
        MatchingAlgorithm::SpatialIndex => {
            spatial_index::match_cases_spatial_index(mfr_lpr_df, vital_events_df, config)
        },
        MatchingAlgorithm::PartitionedParallel => {
            partitioned_parallel::match_cases_partitioned_parallel(
                mfr_lpr_df,
                vital_events_df,
                config,
            )
        },
    }
}
