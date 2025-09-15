//! Data preprocessing
use std::collections::{HashMap, HashSet};
use std::sync::Arc;

use arrow::array::{Array, BooleanArray, Float64Array, Int64Array, Int64Builder};
use arrow::compute::filter;
use arrow::datatypes::{DataType, Field, Schema};
use arrow::record_batch::RecordBatch;

use crate::types::PanelType;
use crate::{DidConfig, DidError};

#[derive(Clone, Copy)]
pub struct DataView<'a> {
    pub id: &'a Int64Array,
    pub time: &'a Int64Array,
    pub group: &'a Int64Array,
}

impl<'a> DataView<'a> {
    pub fn try_new(batch: &'a RecordBatch, config: &DidConfig) -> Result<Self, DidError> {
        let id = batch
            .column_by_name(&config.id_var)
            .ok_or_else(|| {
                DidError::Specification(format!("id column '{}' not found", config.id_var))
            })?
            .as_any()
            .downcast_ref::<Int64Array>()
            .ok_or_else(|| DidError::Specification("id column must be Int64".into()))?;
        let time = batch
            .column_by_name(&config.time_var)
            .ok_or_else(|| {
                DidError::Specification(format!("time column '{}' not found", config.time_var))
            })?
            .as_any()
            .downcast_ref::<Int64Array>()
            .ok_or_else(|| DidError::Specification("time column must be Int64".into()))?;
        let gname = config
            .group_var
            .as_ref()
            .ok_or_else(|| DidError::Specification("group_var must be specified".to_string()))?;
        let group = batch
            .column_by_name(gname)
            .ok_or_else(|| DidError::Specification(format!("group column '{gname}' not found")))?
            .as_any()
            .downcast_ref::<Int64Array>()
            .ok_or_else(|| DidError::Specification("group column must be Int64".into()))?;
        Ok(Self { id, time, group })
    }
}

#[derive(Debug, Clone)]
pub struct PreprocessedData {
    // owned batch; use view() for typed accessors
    pub data: RecordBatch,
    pub tlist: Vec<i64>,
    pub glist: Vec<i64>,
    pub panel_type: PanelType,
    pub is_balanced: bool,
    pub n_unique_ids: usize,
}

#[allow(clippy::cast_possible_truncation)]
fn convert_column_to_i64(data: &mut RecordBatch, column_name: &str) -> Result<(), DidError> {
    let column = data
        .column_by_name(column_name)
        .ok_or_else(|| DidError::Specification(format!("Column '{column_name}' not found")))?;

    let i64_array = if let Some(f64_array) = column.as_any().downcast_ref::<Float64Array>() {
        let mut builder = Int64Builder::with_capacity(f64_array.len());
        for value in f64_array {
            builder.append_option(value.map(|v| v as i64));
        }
        builder.finish()
    } else if let Some(i64_array) = column.as_any().downcast_ref::<Int64Array>() {
        i64_array.clone()
    } else {
        return Err(DidError::Specification(format!(
            "Column '{column_name}' must be of type Float64 or Int64"
        )));
    };

    let i64_field = Field::new(column_name, DataType::Int64, true);
    let mut new_fields = data.schema().fields().to_vec();
    let mut new_columns = data.columns().to_vec();
    let column_index = data.schema().index_of(column_name)?;
    new_fields[column_index] = i64_field.into();
    new_columns[column_index] = Arc::new(i64_array);
    let new_schema = Arc::new(Schema::new(new_fields));
    *data = RecordBatch::try_new(new_schema, new_columns)?;
    Ok(())
}

impl PreprocessedData {
    pub fn view(&self, config: &DidConfig) -> Result<DataView<'_>, DidError> {
        DataView::try_new(&self.data, config)
    }
    /// Creates a new `PreprocessedData` instance from a `RecordBatch` and a `DidConfig`.
    ///
    /// This function preprocesses the data according to the provided configuration, including
    /// converting columns to the correct types, determining the panel structure, and filtering
    /// the data.
    ///
    /// # Errors
    ///
    /// This function returns an error if the configuration is invalid or the data is malformed.
    #[allow(clippy::missing_panics_doc)]
    pub fn from_config(mut data: RecordBatch, config: &DidConfig) -> Result<Self, DidError> {
        let gname = config
            .group_var
            .as_ref()
            .ok_or_else(|| DidError::Specification("group_var must be specified".to_string()))?;
        let tname = &config.time_var;
        let idname = &config.id_var;

        convert_column_to_i64(&mut data, gname)?;
        convert_column_to_i64(&mut data, tname)?;
        convert_column_to_i64(&mut data, idname)?;

        // Get basic info about the data structure
        let id_array = data
            .column_by_name(idname)
            .unwrap()
            .as_any()
            .downcast_ref::<Int64Array>()
            .unwrap();
        let time_array = data
            .column_by_name(tname)
            .unwrap()
            .as_any()
            .downcast_ref::<Int64Array>()
            .unwrap();
        let _group_array = data
            .column_by_name(gname)
            .unwrap()
            .as_any()
            .downcast_ref::<Int64Array>()
            .unwrap();

        // Get unique IDs and times
        let unique_ids: HashSet<i64> = id_array.values().iter().copied().collect();
        let n_unique_ids = unique_ids.len();

        let mut tlist: Vec<i64> = time_array
            .values()
            .iter()
            .copied()
            .collect::<HashSet<_>>()
            .into_iter()
            .collect();
        tlist.sort_unstable();

        // Determine panel structure based on configuration and data
        let (panel_type, is_balanced) =
            Self::determine_panel_structure(&data, config, &unique_ids, &tlist)?;

        // Handle different panel types
        let processed_data = match panel_type {
            PanelType::RepeatedCrossSections => {
                Self::process_repeated_cross_sections(data, config, &tlist)?
            },
            PanelType::UnbalancedPanel => Self::process_unbalanced_panel(data, config, &tlist)?,
            PanelType::BalancedPanel => Self::process_balanced_panel(data, config, &tlist)?,
        };

        // Final tlist and glist after processing
        let time_array = processed_data
            .column_by_name(tname)
            .unwrap()
            .as_any()
            .downcast_ref::<Int64Array>()
            .unwrap();
        let final_tlist: Vec<i64> = time_array
            .values()
            .iter()
            .copied()
            .collect::<HashSet<_>>()
            .into_iter()
            .collect();

        let group_array = processed_data
            .column_by_name(gname)
            .unwrap()
            .as_any()
            .downcast_ref::<Int64Array>()
            .unwrap();
        let glist: Vec<i64> = group_array
            .values()
            .iter()
            .filter(|&&g| g != 0)
            .copied()
            .collect::<HashSet<_>>()
            .into_iter()
            .collect();

        Ok(Self {
            data: processed_data,
            tlist: final_tlist,
            glist,
            panel_type,
            is_balanced,
            n_unique_ids,
        })
    }

    /// Determine the panel structure based on configuration and data characteristics
    fn determine_panel_structure(
        data: &RecordBatch,
        config: &DidConfig,
        unique_ids: &HashSet<i64>,
        tlist: &[i64],
    ) -> Result<(PanelType, bool), DidError> {
        match config.panel_type {
            // If explicitly set to repeated cross sections, use that
            PanelType::RepeatedCrossSections => Ok((PanelType::RepeatedCrossSections, false)),

            // If explicitly set to balanced panel, check if data is actually balanced
            PanelType::BalancedPanel => {
                let is_balanced = Self::check_if_balanced(data, config, unique_ids, tlist);
                if is_balanced {
                    Ok((PanelType::BalancedPanel, true))
                } else if config.allow_unbalanced_panel {
                    // Convert to repeated cross sections following R's approach
                    Ok((PanelType::RepeatedCrossSections, false))
                } else {
                    Err(DidError::Specification(
                        "Data is not balanced but allow_unbalanced_panel=false. Set allow_unbalanced_panel=true or use panel_type=RepeatedCrossSections".to_string()
                    ))
                }
            },

            // If unbalanced panel, check balance and decide
            PanelType::UnbalancedPanel => {
                let is_balanced = Self::check_if_balanced(data, config, unique_ids, tlist);
                if is_balanced {
                    Ok((PanelType::BalancedPanel, true))
                } else {
                    // Keep as unbalanced panel to test SE behavior
                    Ok((PanelType::UnbalancedPanel, false))
                }
            },
        }
    }

    /// Check if the panel data is balanced (all individuals appear in all time periods)
    fn check_if_balanced(
        data: &RecordBatch,
        config: &DidConfig,
        unique_ids: &HashSet<i64>,
        tlist: &[i64],
    ) -> bool {
        let expected_observations = unique_ids.len() * tlist.len();
        let actual_observations = data.num_rows();

        // Simple check: if we have fewer observations than expected, it's unbalanced
        if actual_observations < expected_observations {
            return false;
        }

        // More thorough check: verify each ID appears in each time period
        let id_array = data
            .column_by_name(&config.id_var)
            .unwrap()
            .as_any()
            .downcast_ref::<Int64Array>()
            .unwrap();
        let time_array = data
            .column_by_name(&config.time_var)
            .unwrap()
            .as_any()
            .downcast_ref::<Int64Array>()
            .unwrap();

        let mut id_time_combinations = HashSet::new();
        for i in 0..data.num_rows() {
            let id = id_array.value(i);
            let time = time_array.value(i);
            id_time_combinations.insert((id, time));
        }

        // Check if every ID appears in every time period
        for &id in unique_ids {
            for &time in tlist {
                if !id_time_combinations.contains(&(id, time)) {
                    return false;
                }
            }
        }

        true
    }

    /// Process data as repeated cross sections (recommended approach for your study)
    fn process_repeated_cross_sections(
        mut data: RecordBatch,
        config: &DidConfig,
        tlist: &[i64],
    ) -> Result<RecordBatch, DidError> {
        // For repeated cross sections, we keep all available observations
        // and don't require individuals to appear in all time periods

        // Drop groups treated in the first period (following R's approach)
        let first_period = *tlist.first().unwrap();
        let group_array = data
            .column_by_name(config.group_var.as_ref().unwrap())
            .unwrap()
            .as_any()
            .downcast_ref::<Int64Array>()
            .unwrap();

        let to_keep: Vec<bool> = group_array
            .iter()
            .map(|g| g.is_some_and(|g_val| g_val > first_period || g_val == 0))
            .collect();

        let filter_array = BooleanArray::from(to_keep);
        let filtered_columns = data
            .columns()
            .iter()
            .map(|col| filter(col, &filter_array))
            .collect::<Result<Vec<_>, _>>()?;

        data = RecordBatch::try_new(data.schema(), filtered_columns)?;

        // Remove any rows with missing outcome data (but keep zero values)
        let outcome_array = data
            .column_by_name(&config.outcome_var)
            .unwrap()
            .as_any()
            .downcast_ref::<Float64Array>()
            .unwrap();

        let to_keep: Vec<bool> = (0..data.num_rows())
            .map(|i| !outcome_array.is_null(i))
            .collect();

        let filter_array = BooleanArray::from(to_keep);
        let filtered_columns = data
            .columns()
            .iter()
            .map(|col| filter(col, &filter_array))
            .collect::<Result<Vec<_>, _>>()?;

        RecordBatch::try_new(data.schema(), filtered_columns).map_err(DidError::from)
    }

    /// Process unbalanced panel data (converts to repeated cross sections following R)
    fn process_unbalanced_panel(
        data: RecordBatch,
        config: &DidConfig,
        tlist: &[i64],
    ) -> Result<RecordBatch, DidError> {
        // Following R's pre_process_did.R approach: treat unbalanced panels as repeated cross sections
        Self::process_repeated_cross_sections(data, config, tlist)
    }

    /// Process balanced panel data (requires all individuals in all periods)
    fn process_balanced_panel(
        mut data: RecordBatch,
        config: &DidConfig,
        tlist: &[i64],
    ) -> Result<RecordBatch, DidError> {
        // For balanced panels, we need to ensure we have complete cases
        // Remove individuals who don't appear in all time periods

        let id_array = data
            .column_by_name(&config.id_var)
            .unwrap()
            .as_any()
            .downcast_ref::<Int64Array>()
            .unwrap();
        let _time_array = data
            .column_by_name(&config.time_var)
            .unwrap()
            .as_any()
            .downcast_ref::<Int64Array>()
            .unwrap();

        // Count observations per individual
        let mut id_counts: HashMap<i64, usize> = HashMap::new();
        for i in 0..data.num_rows() {
            let id = id_array.value(i);
            *id_counts.entry(id).or_insert(0) += 1;
        }

        let expected_periods = tlist.len();
        let complete_ids: HashSet<i64> = id_counts
            .into_iter()
            .filter_map(|(id, count)| {
                if count == expected_periods {
                    Some(id)
                } else {
                    None
                }
            })
            .collect();

        // Filter to keep only complete cases
        let to_keep: Vec<bool> = (0..data.num_rows())
            .map(|i| {
                let id = id_array.value(i);
                complete_ids.contains(&id)
            })
            .collect();

        let filter_array = BooleanArray::from(to_keep);
        let filtered_columns = data
            .columns()
            .iter()
            .map(|col| filter(col, &filter_array))
            .collect::<Result<Vec<_>, _>>()?;

        data = RecordBatch::try_new(data.schema(), filtered_columns)?;

        // Apply same filtering as repeated cross sections for treated groups
        Self::process_repeated_cross_sections(data, config, tlist)
    }

    /// Validates that all required variables are present in the data.
    ///
    /// # Errors
    ///
    /// This function returns an error if a required variable is not found in the data.
    pub fn validate_args(&self, config: &DidConfig) -> Result<(), DidError> {
        let schema = self.data.schema();
        let required_vars = vec![
            &config.outcome_var,
            &config.treatment_var,
            &config.time_var,
            &config.id_var,
        ];
        for var in required_vars {
            if schema.field_with_name(var).is_err() {
                return Err(DidError::Specification(format!(
                    "Variable '{var}' not found in data"
                )));
            }
        }
        if let Some(group_var) = &config.group_var {
            if schema.field_with_name(group_var).is_err() {
                return Err(DidError::Specification(format!(
                    "Variable '{group_var}' not found in data"
                )));
            }
        }
        if let Some(cluster_var) = &config.cluster_var {
            if schema.field_with_name(cluster_var).is_err() {
                return Err(DidError::Specification(format!(
                    "Variable '{cluster_var}' not found in data"
                )));
            }
        }
        for var in &config.control_vars {
            if schema.field_with_name(var).is_err() {
                return Err(DidError::Specification(format!(
                    "Variable '{var}' not found in data"
                )));
            }
        }
        Ok(())
    }

    /// Standardizes the data.
    ///
    /// This is a placeholder and does not currently do anything.
    ///
    /// # Errors
    ///
    /// This function does not currently return any errors.
    pub const fn standardize_data(&mut self, _config: &DidConfig) -> Result<(), DidError> {
        // TODO: Implement this if needed
        Ok(())
    }

    /// Get panel information for diagnostics
    #[must_use]
    pub fn get_panel_info(&self) -> (PanelType, bool, usize) {
        (self.panel_type.clone(), self.is_balanced, self.n_unique_ids)
    }
}
