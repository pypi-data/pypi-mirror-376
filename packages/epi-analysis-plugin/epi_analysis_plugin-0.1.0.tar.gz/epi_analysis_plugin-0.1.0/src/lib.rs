mod config;
mod did_bridge;
mod extractors;
mod matching;
mod output;
mod plugins;
mod temporal_extractor;
mod types;
mod utilities;

use did_core::computation::aggregation::{
    aggregate_by_calendar_time, aggregate_by_event_time, aggregate_by_group, aggregate_simple,
    ci_from_att_se, z_from_confidence, AggregatedEffect,
};
use did_core::prelude::{DidConfig, DidEstimator};
use polars::datatypes::PlSmallStr;
use polars::prelude::NamedFrom;
use polars::series::Series;
use pyo3::prelude::*;
use pyo3_polars::{PolarsAllocator, PyDataFrame};

use crate::config::WorkflowConfig;
use crate::extractors::{education, ethnicity};
use crate::matching::match_cases;
use crate::output::formatter::create_match_output_format;

#[pyfunction]
fn match_scd_cases(
    py_df: PyDataFrame,
    py_vital_df: Option<PyDataFrame>,
    config: &str,
) -> PyResult<PyDataFrame> {
    let df = py_df.into();
    let vital_df = py_vital_df.map(std::convert::Into::into);
    let config: WorkflowConfig = serde_json::from_str(config).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid config: {e}"))
    })?;

    let result = match_cases(&df, vital_df.as_ref(), &config).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Matching failed: {e}"))
    })?;

    Ok(PyDataFrame(result))
}

#[pyfunction]
fn format_match_output(py_df: PyDataFrame) -> PyResult<PyDataFrame> {
    let df = py_df.into();

    let result = create_match_output_format(&df).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Format conversion failed: {e}"))
    })?;

    Ok(PyDataFrame(result))
}

#[pyfunction]
#[pyo3(signature = (py_df, identifier_col, index_date_col, registry_pattern, variable_col, temporal_range=(-1, 1), additional_cols=None, use_cache=true))]
fn extract_temporal_data_dynamic_year_py(
    py_df: PyDataFrame,
    identifier_col: &str,
    index_date_col: &str,
    registry_pattern: &str,
    variable_col: &str,
    temporal_range: (i64, i64),
    additional_cols: Option<Vec<String>>,
    use_cache: bool,
) -> PyResult<PyDataFrame> {
    let df = py_df.into();

    let additional_cols_slice = additional_cols.as_deref();

    let result = temporal_extractor::extract_temporal_data_dynamic_year(
        &df,
        identifier_col,
        index_date_col,
        registry_pattern,
        variable_col,
        temporal_range,
        additional_cols_slice,
        use_cache,
    )
    .map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Temporal extraction failed: {e}"
        ))
    })?;

    Ok(PyDataFrame(result))
}

#[pyfunction]
#[pyo3(signature = (py_df, batch_size, identifier_col, index_date_col, registry_pattern, variable_col, temporal_range=(-1, 1), additional_cols=None, use_cache=true))]
fn extract_temporal_data_batched_py(
    py_df: PyDataFrame,
    batch_size: usize,
    identifier_col: &str,
    index_date_col: &str,
    registry_pattern: &str,
    variable_col: &str,
    temporal_range: (i64, i64),
    additional_cols: Option<Vec<String>>,
    use_cache: bool,
) -> PyResult<PyDataFrame> {
    let df = py_df.into();

    let additional_cols_slice = additional_cols.as_deref();

    let result = temporal_extractor::extract_temporal_data_batched(
        &df,
        batch_size,
        identifier_col,
        index_date_col,
        registry_pattern,
        variable_col,
        temporal_range,
        additional_cols_slice,
        use_cache,
    )
    .map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Batched temporal extraction failed: {e}"
        ))
    })?;

    Ok(PyDataFrame(result))
}

#[pyfunction]
#[pyo3(signature = (py_df, identifier_col, index_date_col, uddf_file_path))]
fn extract_highest_education_level_py(
    py_df: PyDataFrame,
    identifier_col: &str,
    index_date_col: &str,
    uddf_file_path: &str,
) -> PyResult<PyDataFrame> {
    let df = py_df.into();

    let result = education::extract_highest_education_level(
        &df,
        identifier_col,
        index_date_col,
        uddf_file_path,
    )
    .map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Education level extraction failed: {e}"
        ))
    })?;

    Ok(PyDataFrame(result))
}

#[pyfunction]
#[pyo3(signature = (py_df, batch_size, identifier_col, index_date_col, uddf_file_path))]
fn extract_highest_education_level_batched_py(
    py_df: PyDataFrame,
    batch_size: usize,
    identifier_col: &str,
    index_date_col: &str,
    uddf_file_path: &str,
) -> PyResult<PyDataFrame> {
    let df = py_df.into();

    let result = education::extract_highest_education_level_batched(
        &df,
        batch_size,
        identifier_col,
        index_date_col,
        uddf_file_path,
    )
    .map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Batched education level extraction failed: {e}"
        ))
    })?;

    Ok(PyDataFrame(result))
}

// Consolidated ethnicity extraction uses temporal variant exclusively

#[pyfunction]
#[pyo3(signature = (py_df, identifier_col, index_date_col, bef_registry_pattern, temporal_range=(-1, 1)))]
fn extract_ethnicity_temporal_py(
    py_df: PyDataFrame,
    identifier_col: &str,
    index_date_col: &str,
    bef_registry_pattern: &str,
    temporal_range: (i64, i64),
) -> PyResult<PyDataFrame> {
    let df = py_df.into();

    let result = ethnicity::extract_ethnicity_temporal(
        &df,
        identifier_col,
        index_date_col,
        bef_registry_pattern,
        temporal_range,
    )
    .map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Ethnicity temporal extraction failed: {e}"
        ))
    })?;

    Ok(PyDataFrame(result))
}

#[pyfunction]
fn did_att_gt_py(py_df: PyDataFrame, config_json: &str) -> PyResult<PyDataFrame> {
    // Parse configuration to did-core DidConfig
    let cfg: DidConfig = serde_json::from_str(config_json).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid DID config JSON: {e}"))
    })?;

    // Convert Polars -> Arrow RecordBatch (copying MVP)
    let df: polars::prelude::DataFrame = py_df.into();
    let batch = did_bridge::polars_df_to_arrow1_batch(&df).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to convert DataFrame to Arrow batch: {e}"
        ))
    })?;

    // Run did-core estimator
    let est = DidEstimator::from_batch(batch, cfg).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to construct estimator: {e}"
        ))
    })?;
    let res = est.fit().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("DID estimation failed: {e}"))
    })?;

    // Build a Polars DataFrame from att_gt results directly (no Arrow roundtrip)
    let groups: Vec<i64> = res.att_gt.iter().map(|r| r.group).collect();
    let times: Vec<i64> = res.att_gt.iter().map(|r| r.time).collect();
    let atts: Vec<f64> = res.att_gt.iter().map(|r| r.att).collect();
    let ses: Vec<f64> = res.att_gt.iter().map(|r| r.se).collect();
    let t_stats: Vec<f64> = res.att_gt.iter().map(|r| r.t_stat).collect();
    let p_values: Vec<f64> = res.att_gt.iter().map(|r| r.p_value).collect();
    let conf_low: Vec<f64> = res.att_gt.iter().map(|r| r.conf_low).collect();
    let conf_high: Vec<f64> = res.att_gt.iter().map(|r| r.conf_high).collect();

    let out = polars::prelude::DataFrame::new(vec![
        Series::new(PlSmallStr::from_static("group"), groups).into(),
        Series::new(PlSmallStr::from_static("time"), times).into(),
        Series::new(PlSmallStr::from_static("att"), atts).into(),
        Series::new(PlSmallStr::from_static("se"), ses).into(),
        Series::new(PlSmallStr::from_static("t_stat"), t_stats).into(),
        Series::new(PlSmallStr::from_static("p_value"), p_values).into(),
        Series::new(PlSmallStr::from_static("conf_low"), conf_low).into(),
        Series::new(PlSmallStr::from_static("conf_high"), conf_high).into(),
    ])
    .map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to build output DataFrame: {e}"
        ))
    })?;

    Ok(PyDataFrame(out))
}

#[pyfunction]
fn did_panel_info_py(py_df: PyDataFrame, config_json: &str) -> PyResult<PyDataFrame> {
    let cfg: DidConfig = serde_json::from_str(config_json).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid DID config JSON: {e}"))
    })?;

    let df: polars::prelude::DataFrame = py_df.into();
    let batch = did_bridge::polars_df_to_arrow1_batch(&df).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to convert DataFrame to Arrow batch: {e}"
        ))
    })?;

    let est = DidEstimator::from_batch(batch, cfg).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to construct estimator: {e}"
        ))
    })?;
    let (panel_type, is_balanced, n_periods) = est.get_panel_info().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Panel info failed: {e}"))
    })?;

    let panel_type_str = match panel_type {
        did_core::types::PanelType::BalancedPanel => "BalancedPanel",
        did_core::types::PanelType::UnbalancedPanel => "UnbalancedPanel",
        did_core::types::PanelType::RepeatedCrossSections => "RepeatedCrossSections",
    };

    let out = polars::prelude::DataFrame::new(vec![
        Series::new(PlSmallStr::from_static("panel_type"), vec![panel_type_str]).into(),
        Series::new(PlSmallStr::from_static("is_balanced"), vec![is_balanced]).into(),
        Series::new(PlSmallStr::from_static("n_periods"), vec![n_periods as i64]).into(),
    ])
    .map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to build panel info DataFrame: {e}"
        ))
    })?;

    Ok(PyDataFrame(out))
}

#[pyfunction]
#[pyo3(signature = (py_df, config_json, kind="simple", confidence=0.95, uniform_bands=false))]
fn did_aggregate_py(
    py_df: PyDataFrame,
    config_json: &str,
    kind: &str,
    confidence: f64,
    uniform_bands: bool,
) -> PyResult<PyDataFrame> {
    let cfg: DidConfig = serde_json::from_str(config_json).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid DID config JSON: {e}"))
    })?;

    let df: polars::prelude::DataFrame = py_df.into();
    let batch = did_bridge::polars_df_to_arrow1_batch(&df).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to convert DataFrame to Arrow batch: {e}"
        ))
    })?;

    let est = DidEstimator::from_batch(batch, cfg).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to construct estimator: {e}"
        ))
    })?;
    let did = est.fit().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("DID estimation failed: {e}"))
    })?;

    let kind_lc = kind.to_ascii_lowercase();
    let z = z_from_confidence(confidence);

    let mut group_col: Vec<Option<i64>> = Vec::new();
    let mut time_col: Vec<Option<i64>> = Vec::new();
    let mut et_col: Vec<Option<i64>> = Vec::new();
    let mut att_col: Vec<f64> = Vec::new();
    let mut se_col: Vec<f64> = Vec::new();
    let mut low_col: Vec<f64> = Vec::new();
    let mut high_col: Vec<f64> = Vec::new();
    let mut overall_col: Vec<bool> = Vec::new();

    match kind_lc.as_str() {
        "simple" => {
            let (att, se, _inf) = aggregate_simple(&did).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Simple aggregation failed: {e}"
                ))
            })?;
            let (low, high) = ci_from_att_se(att, se, z);
            group_col.push(None);
            time_col.push(None);
            et_col.push(None);
            att_col.push(att);
            se_col.push(se);
            low_col.push(low);
            high_col.push(high);
            overall_col.push(true);
        },
        "group" => {
            let (effects, overall_att, overall_se, overall_low, overall_high) =
                aggregate_by_group(&did, confidence, uniform_bands).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                        "Group aggregation failed: {e}"
                    ))
                })?;
            for AggregatedEffect {
                group,
                time,
                event_time,
                att,
                se,
                conf_low,
                conf_high,
            } in effects
            {
                group_col.push(group);
                time_col.push(time);
                et_col.push(event_time);
                att_col.push(att);
                se_col.push(se);
                low_col.push(conf_low);
                high_col.push(conf_high);
                overall_col.push(false);
            }
            group_col.push(None);
            time_col.push(None);
            et_col.push(None);
            att_col.push(overall_att);
            se_col.push(overall_se);
            low_col.push(overall_low);
            high_col.push(overall_high);
            overall_col.push(true);
        },
        "dynamic" | "event" => {
            let (effects, overall_att, overall_se, overall_low, overall_high) =
                aggregate_by_event_time(&did, confidence, uniform_bands).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                        "Dynamic aggregation failed: {e}"
                    ))
                })?;
            for AggregatedEffect {
                group,
                time,
                event_time,
                att,
                se,
                conf_low,
                conf_high,
            } in effects
            {
                group_col.push(group);
                time_col.push(time);
                et_col.push(event_time);
                att_col.push(att);
                se_col.push(se);
                low_col.push(conf_low);
                high_col.push(conf_high);
                overall_col.push(false);
            }
            group_col.push(None);
            time_col.push(None);
            et_col.push(None);
            att_col.push(overall_att);
            se_col.push(overall_se);
            low_col.push(overall_low);
            high_col.push(overall_high);
            overall_col.push(true);
        },
        "calendar" | "time" => {
            let (effects, overall_att, overall_se, overall_low, overall_high) =
                aggregate_by_calendar_time(&did, confidence, uniform_bands).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                        "Calendar aggregation failed: {e}"
                    ))
                })?;
            for AggregatedEffect {
                group,
                time,
                event_time,
                att,
                se,
                conf_low,
                conf_high,
            } in effects
            {
                group_col.push(group);
                time_col.push(time);
                et_col.push(event_time);
                att_col.push(att);
                se_col.push(se);
                low_col.push(conf_low);
                high_col.push(conf_high);
                overall_col.push(false);
            }
            group_col.push(None);
            time_col.push(None);
            et_col.push(None);
            att_col.push(overall_att);
            se_col.push(overall_se);
            low_col.push(overall_low);
            high_col.push(overall_high);
            overall_col.push(true);
        },
        other => {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Unknown aggregation kind: {other}. Expected one of: simple, group, dynamic, calendar"
            )));
        },
    }

    let out = polars::prelude::DataFrame::new(vec![
        Series::new(PlSmallStr::from_static("group"), group_col).into(),
        Series::new(PlSmallStr::from_static("time"), time_col).into(),
        Series::new(PlSmallStr::from_static("event_time"), et_col).into(),
        Series::new(PlSmallStr::from_static("att"), att_col).into(),
        Series::new(PlSmallStr::from_static("se"), se_col).into(),
        Series::new(PlSmallStr::from_static("conf_low"), low_col).into(),
        Series::new(PlSmallStr::from_static("conf_high"), high_col).into(),
        Series::new(PlSmallStr::from_static("is_overall"), overall_col).into(),
    ])
    .map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to build aggregation output DataFrame: {e}"
        ))
    })?;

    Ok(PyDataFrame(out))
}

#[pymodule]
fn _internal(_py: Python, m: &Bound<PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_function(wrap_pyfunction!(match_scd_cases, m)?)?;
    m.add_function(wrap_pyfunction!(format_match_output, m)?)?;
    m.add_function(wrap_pyfunction!(extract_temporal_data_dynamic_year_py, m)?)?;
    m.add_function(wrap_pyfunction!(extract_temporal_data_batched_py, m)?)?;
    m.add_function(wrap_pyfunction!(extract_highest_education_level_py, m)?)?;
    m.add_function(wrap_pyfunction!(
        extract_highest_education_level_batched_py,
        m
    )?)?;
    // Consolidated ethnicity: expose only the temporal extractor
    m.add_function(wrap_pyfunction!(extract_ethnicity_temporal_py, m)?)?;
    // DID API
    m.add_function(wrap_pyfunction!(did_att_gt_py, m)?)?;
    m.add_function(wrap_pyfunction!(did_panel_info_py, m)?)?;
    m.add_function(wrap_pyfunction!(did_aggregate_py, m)?)?;
    Ok(())
}

#[global_allocator]
static ALLOC: PolarsAllocator = PolarsAllocator::new();
