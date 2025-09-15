// Core ATT(g,t) estimation
pub mod attgt;

// Result aggregation across groups/time
pub mod aggregation;

// Re-exports for convenience
pub use aggregation::{AggregationRequest, AggregationResult, AggregationType, ConfidenceLevel};
pub use attgt::{compute_att_gt, AttGtComputer};

use crate::computation::aggregation::{
    aggregate_by_calendar_time, aggregate_by_event_time, aggregate_by_group, aggregate_simple,
    z_from_confidence,
};
use crate::DidError;

/// Computation entrypoint and aggregation utilities.
///
/// This module provides high-level APIs to compute ATT(g,t) and to aggregate
/// results across groups, event times, or calendar time.
impl crate::DidResult {
    /// Aggregate ATT(g,t) estimates using a preset aggregation kind.
    ///
    /// # Errors
    /// Returns an error if aggregation fails due to invalid configuration.
    pub fn aggregate(&self, agg_type: &AggregationType) -> Result<AggregationResult, DidError> {
        self.aggregate_with_confidence(agg_type, 0.95)
    }

    /// Aggregate with an explicit confidence level.
    ///
    /// # Errors
    /// Returns an error if aggregation fails due to invalid configuration.
    pub fn aggregate_with_confidence(
        &self,
        agg_type: &AggregationType,
        confidence_level: f64,
    ) -> Result<AggregationResult, DidError> {
        self.aggregate_with_options(agg_type, confidence_level, false)
    }

    /// Aggregate with full options, including uniform confidence bands.
    ///
    /// # Errors
    /// Returns an error if aggregation fails due to invalid configuration.
    pub fn aggregate_with_options(
        &self,
        agg_type: &AggregationType,
        confidence_level: f64,
        use_uniform_bands: bool,
    ) -> Result<AggregationResult, DidError> {
        let req = AggregationRequest {
            kind: *agg_type,
            confidence: ConfidenceLevel::from(confidence_level),
            uniform_bands: use_uniform_bands,
        };
        self.aggregate_request(&req)
    }

    /// Aggregate using an `AggregationRequest`.
    ///
    /// # Errors
    /// Returns an error if aggregation fails due to invalid configuration.
    pub fn aggregate_request(
        &self,
        req: &AggregationRequest,
    ) -> Result<AggregationResult, DidError> {
        let z = match req.confidence {
            ConfidenceLevel::C90 => 1.645,
            ConfidenceLevel::C95 => 1.96,
            ConfidenceLevel::C99 => 2.576,
            ConfidenceLevel::Custom(c) => z_from_confidence(c),
        };

        let (overall_att, se, conf_low, conf_high, aggregated_effects) = match req.kind {
            AggregationType::Simple => {
                let (att, se, _inf) = aggregate_simple(self)?;
                let conf_low = z.mul_add(-se, att);
                let conf_high = z.mul_add(se, att);
                (att, se, conf_low, conf_high, Vec::new())
            },
            AggregationType::Group => {
                let (effects, att, se, low, high) = aggregate_by_group(
                    self,
                    match req.confidence {
                        ConfidenceLevel::Custom(c) => c,
                        ConfidenceLevel::C90 => 0.90,
                        ConfidenceLevel::C95 => 0.95,
                        ConfidenceLevel::C99 => 0.99,
                    },
                    req.uniform_bands,
                )?;
                (att, se, low, high, effects)
            },
            AggregationType::Dynamic => {
                let (effects, att, se, low, high) = aggregate_by_event_time(
                    self,
                    match req.confidence {
                        ConfidenceLevel::Custom(c) => c,
                        ConfidenceLevel::C90 => 0.90,
                        ConfidenceLevel::C95 => 0.95,
                        ConfidenceLevel::C99 => 0.99,
                    },
                    req.uniform_bands,
                )?;
                (att, se, low, high, effects)
            },
            AggregationType::Calendar => {
                let (effects, att, se, low, high) = aggregate_by_calendar_time(
                    self,
                    match req.confidence {
                        ConfidenceLevel::Custom(c) => c,
                        ConfidenceLevel::C90 => 0.90,
                        ConfidenceLevel::C95 => 0.95,
                        ConfidenceLevel::C99 => 0.99,
                    },
                    req.uniform_bands,
                )?;
                (att, se, low, high, effects)
            },
        };

        Ok(AggregationResult {
            overall_att,
            se,
            conf_low,
            conf_high,
            conf_band: None,
            aggregated_effects,
        })
    }
}
