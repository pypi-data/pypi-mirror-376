use serde::Deserialize;

/// Algorithm selection for risk-set matching
#[derive(Deserialize, Debug, Clone, Copy, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum MatchingAlgorithm {
    /// Optimized with parallel processing and spatial indexing
    SpatialIndex,
    /// Partitioned parallel processing with conflict-free allocation
    PartitionedParallel,
}

impl Default for MatchingAlgorithm {
    fn default() -> Self {
        Self::SpatialIndex
    }
}

/// Configuration for case-control matching
#[derive(Deserialize, Debug, Clone, Copy)]
#[allow(clippy::struct_excessive_bools)]
pub struct MatchingConfig {
    /// Maximum difference in days between birth dates
    pub birth_date_window_days: i32,

    /// Maximum difference in days between parent birth dates
    pub parent_birth_date_window_days: i32,

    /// Whether to match on parent birth dates
    pub match_parent_birth_dates: bool,

    /// Whether to match only on maternal birth dates
    pub match_mother_birth_date_only: bool,

    /// Whether both parents are required
    pub require_both_parents: bool,

    /// Whether to match on parity (birth order)
    pub match_parity: bool,

    /// Whether to match on birth type (singleton, doubleton, etc.)
    pub match_birth_type: bool,

    /// Number of controls to match per case
    pub matching_ratio: usize,
}

impl Default for MatchingConfig {
    fn default() -> Self {
        Self {
            birth_date_window_days: 30,
            parent_birth_date_window_days: 365,
            match_parent_birth_dates: true,
            match_mother_birth_date_only: false,
            require_both_parents: false,
            match_parity: true,
            match_birth_type: false,
            matching_ratio: 5,
        }
    }
}

/// Configuration for the integrated MFR/LPR matching workflow
#[derive(Deserialize, Debug, Clone, Default)]
pub struct WorkflowConfig {
    /// Matching configuration
    pub matching: MatchingConfig,
    /// Algorithm selection
    pub algorithm: MatchingAlgorithm,
}
