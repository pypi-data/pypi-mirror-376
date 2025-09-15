// Aggregation types and configuration
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum AggregationType {
    Simple,
    Group,
    Dynamic,
    Calendar,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum ConfidenceLevel {
    /// 90% confidence
    C90,
    /// 95% confidence (default)
    C95,
    /// 99% confidence
    C99,
    /// Custom confidence level in (0,1)
    Custom(f64),
}

impl Default for ConfidenceLevel {
    fn default() -> Self {
        Self::C95
    }
}

impl From<f64> for ConfidenceLevel {
    fn from(v: f64) -> Self {
        match v {
            x if (x - 0.90).abs() < 1e-9 => Self::C90,
            x if (x - 0.95).abs() < 1e-9 => Self::C95,
            x if (x - 0.99).abs() < 1e-9 => Self::C99,
            x => Self::Custom(x),
        }
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct AggregationRequest {
    pub kind: AggregationType,
    pub confidence: ConfidenceLevel,
    pub uniform_bands: bool,
}

impl Default for AggregationRequest {
    fn default() -> Self {
        Self {
            kind: AggregationType::Simple,
            confidence: ConfidenceLevel::default(),
            uniform_bands: false,
        }
    }
}

impl AggregationRequest {
    #[must_use]
    pub fn new(kind: AggregationType) -> Self {
        Self {
            kind,
            ..Default::default()
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregatedEffect {
    pub group: Option<i64>,
    pub time: Option<i64>,
    pub event_time: Option<i64>,
    pub att: f64,
    pub se: f64,
    pub conf_low: f64,
    pub conf_high: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregationResult {
    pub overall_att: f64,
    pub se: f64,
    pub conf_low: f64,
    pub conf_high: f64,
    pub conf_band: Option<(Vec<f64>, Vec<f64>)>,
    pub aggregated_effects: Vec<AggregatedEffect>,
}

// Aggregation implementations
pub mod bootstrap;
pub mod calendar;
pub mod ci;
pub mod dynamic;
pub mod group;
pub mod helper;
pub mod se;
pub mod simple;
pub mod weights;
pub mod weights_util;

// Function re-exports
// Utility re-exports
pub use bootstrap::*;
pub use calendar::compute_calendar_aggregation_exact as aggregate_by_calendar_time;
pub use ci::*;
pub use dynamic::compute_dynamic_aggregation_exact as aggregate_by_event_time;
pub use group::compute_group_aggregation_exact as aggregate_by_group;
pub use helper::z_from_confidence;
pub use se::*;
pub use simple::compute_simple_aggregation as aggregate_simple;
pub use weights::*;
pub use weights_util::*;
