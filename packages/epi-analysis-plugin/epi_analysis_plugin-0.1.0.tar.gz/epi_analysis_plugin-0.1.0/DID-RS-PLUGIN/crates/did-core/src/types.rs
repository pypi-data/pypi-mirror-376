use faer::Mat;
use serde::{Deserialize, Serialize};

use crate::estimators::propensity::LossFunction;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EstimationMethod {
    Dr,
    Ip,
    Reg,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Inference {
    Did,
    Drdid,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BasePeriod {
    Varying,
    Universal,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ControlGroup {
    NeverTreated,
    NotYetTreated,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PanelType {
    /// Balanced panel data (same individuals in all periods)
    BalancedPanel,
    /// Panel data that allows for missing observations
    UnbalancedPanel,
    /// Repeated cross sections (different individuals across periods)
    RepeatedCrossSections,
}

// Core data structures following reference patterns
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DidConfig {
    pub outcome_var: String,
    pub treatment_var: String,
    pub time_var: String,
    pub id_var: String,
    pub group_var: Option<String>,
    pub control_vars: Vec<String>,
    pub cluster_var: Option<String>,
    pub weights_var: Option<String>,
    pub bootstrap_iterations: usize,
    pub confidence_level: f64,
    pub base_period: BasePeriod,
    pub control_group: ControlGroup,
    pub method: EstimationMethod,
    pub inference: Inference,
    pub loss: LossFunction,
    pub panel_type: PanelType,
    pub allow_unbalanced_panel: bool,
    pub rng_seed: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AttGtResult {
    pub group: i64,
    pub time: i64,
    pub att: f64,
    pub se: f64,
    pub t_stat: f64,
    pub p_value: f64,
    pub conf_low: f64,
    pub conf_high: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UnitData {
    /// Individual unit unique identifiers
    pub unit_ids: Vec<i64>,
    /// Group assignment for each unit (corresponds to G in R wif function)
    pub unit_groups: Vec<i64>,
    /// Sampling weights for each unit (corresponds to weights.ind in R wif function)
    pub unit_weights: Vec<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DidResult {
    pub att_gt: Vec<AttGtResult>,
    pub influence_function: Mat<f64>,
    pub n_obs: usize,
    pub n_groups: usize,
    pub n_periods: usize,
    pub method: EstimationMethod,
    pub config: DidConfig,
    /// Group probabilities for exact aggregation (maps group -> probability)
    /// Following R's pg computation: pg <- sapply(originalglist, function(g) mean(weights.ind*(dta[,gname]==g)))
    pub group_probabilities: std::collections::HashMap<i64, f64>,
    /// Individual unit data needed for weight influence function computation
    pub unit_data: UnitData,
}
