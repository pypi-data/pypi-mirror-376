use std::collections::{HashMap, HashSet};
use std::sync::Arc;

use arrow::array::{
    Array, ArrayBuilder, ArrayRef, BooleanArray, BooleanBuilder, Float64Array, Float64Builder,
    Int64Array, Int64Builder, StringArray,
};
use arrow::datatypes::{DataType, Field, Schema};
use arrow::record_batch::RecordBatch;

use crate::computation::attgt::AttGtComputer;
use crate::types::ControlGroup;
use crate::DidError;

#[derive(Copy, Clone)]
pub struct ComparisonParams<'a> {
    pub g: i64,
    pub t: i64,
    pub pret: i64,
    pub group_array: &'a Int64Array,
    pub time_array: &'a Int64Array,
    pub id_array: &'a Int64Array,
    pub id_to_idx: &'a HashMap<i64, usize>,
}

pub fn setup_2x2_comparison(
    this: &AttGtComputer,
    params: ComparisonParams<'_>,
) -> Result<(RecordBatch, Vec<usize>), DidError> {
    let is_treated = |g_val: i64| g_val == params.g;
    let is_control = |g_val: i64| match this.config.control_group {
        ControlGroup::NeverTreated => g_val == 0,
        ControlGroup::NotYetTreated => g_val > params.t || g_val == 0,
    };

    let outcome_array = this
        .data
        .data
        .column_by_name(&this.config.outcome_var)
        .ok_or_else(|| {
            DidError::Specification(format!(
                "Outcome column '{}' not found",
                this.config.outcome_var
            ))
        })?
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| DidError::Specification("Outcome column must be Float64".into()))?;

    let mut wide_data: HashMap<i64, (f64, f64, bool)> = HashMap::new();

    for i in 0..this.data.data.num_rows() {
        let id = params.id_array.value(i);
        let time = params.time_array.value(i);
        let group = params.group_array.value(i);
        let y = outcome_array.value(i);

        if !(is_treated(group) || is_control(group)) || (time != params.pret && time != params.t) {
            continue;
        }

        let entry = wide_data
            .entry(id)
            .or_insert_with(|| (f64::NAN, f64::NAN, is_treated(group)));

        if time == params.pret {
            entry.0 = y;
        } else {
            entry.1 = y;
        }
    }

    let (mut control_var_builders, control_var_fields, string_categories) =
        prepare_control_builders(this);

    let mut delta_y = Float64Builder::new();
    let mut d = Int64Builder::new();
    let mut original_indices = Vec::new();

    let mut sorted_ids: Vec<i64> = wide_data.keys().copied().collect();
    sorted_ids.sort_unstable();

    for id in sorted_ids {
        if let Some((y0, y1, is_treated)) = wide_data.get(&id) {
            if y0.is_nan() || y1.is_nan() {
                continue;
            }

            delta_y.append_value(y1 - y0);
            d.append_value(i64::from(*is_treated));

            if let Some(&orig_idx) = params.id_to_idx.get(&id) {
                original_indices.push(orig_idx);
                append_control_row(
                    this,
                    orig_idx,
                    &mut control_var_builders,
                    &string_categories,
                );
            }
        }
    }

    let mut schema_fields = vec![
        Field::new("delta_y", DataType::Float64, false),
        Field::new("D", DataType::Int64, false),
    ];
    schema_fields.extend(control_var_fields);
    let schema = Arc::new(Schema::new(schema_fields));

    let mut arrays: Vec<ArrayRef> = vec![Arc::new(delta_y.finish()), Arc::new(d.finish())];
    for mut builder in control_var_builders {
        arrays.push(builder.finish());
    }

    let batch = RecordBatch::try_new(schema, arrays)?;
    Ok((batch, original_indices))
}

type ControlBuilders = Vec<Box<dyn ArrayBuilder>>;
type ControlFields = Vec<Field>;
type StringCategories = HashMap<String, Vec<String>>;

fn prepare_control_builders(
    this: &AttGtComputer,
) -> (ControlBuilders, ControlFields, StringCategories) {
    let mut builders: Vec<Box<dyn ArrayBuilder>> = Vec::new();
    let mut fields = Vec::new();
    let mut string_cats: HashMap<String, Vec<String>> = HashMap::new();

    for var in &this.config.control_vars {
        if let Some(col) = this.data.data.column_by_name(var) {
            if col.as_any().is::<StringArray>() {
                let string_array = col.as_any().downcast_ref::<StringArray>().unwrap();
                let mut categories = HashSet::new();
                for i in 0..string_array.len() {
                    if !string_array.is_null(i) {
                        categories.insert(string_array.value(i).to_owned());
                    }
                }
                let mut sorted: Vec<String> = categories.into_iter().collect();
                sorted.sort();
                // drop last category to avoid dummy trap
                for cat in sorted.iter().take(sorted.len().saturating_sub(1)) {
                    let field_name = format!("{var}_{cat}");
                    fields.push(Field::new(&field_name, DataType::Boolean, false));
                    builders.push(Box::new(BooleanBuilder::new()));
                }
                string_cats.insert(var.clone(), sorted);
            } else {
                fields.push(Field::new(var, DataType::Float64, false));
                builders.push(Box::new(Float64Builder::new()));
            }
        }
    }
    (builders, fields, string_cats)
}

fn append_control_row(
    this: &AttGtComputer,
    original_idx: usize,
    builders: &mut [Box<dyn ArrayBuilder>],
    string_cats: &HashMap<String, Vec<String>>,
) {
    let mut bidx = 0;
    for var in &this.config.control_vars {
        if let Some(col) = this.data.data.column_by_name(var) {
            if let Some(categories) = string_cats.get(var) {
                let arr = col.as_any().downcast_ref::<StringArray>().unwrap();
                let val = if arr.is_null(original_idx) {
                    None
                } else {
                    Some(arr.value(original_idx))
                };
                for cat in categories.iter().take(categories.len().saturating_sub(1)) {
                    let b = builders[bidx]
                        .as_any_mut()
                        .downcast_mut::<BooleanBuilder>()
                        .unwrap();
                    b.append_value(val.is_some_and(|v| v == cat));
                    bidx += 1;
                }
            } else {
                let b = builders[bidx]
                    .as_any_mut()
                    .downcast_mut::<Float64Builder>()
                    .unwrap();
                if let Some(fa) = col.as_any().downcast_ref::<Float64Array>() {
                    b.append_value(fa.value(original_idx));
                } else if let Some(ia) = col.as_any().downcast_ref::<Int64Array>() {
                    b.append_value(ia.value(original_idx) as f64);
                } else if let Some(ba) = col.as_any().downcast_ref::<BooleanArray>() {
                    b.append_value(if ba.value(original_idx) { 1.0 } else { 0.0 });
                } else {
                    b.append_value(0.0);
                }
                bidx += 1;
            }
        }
    }
}
