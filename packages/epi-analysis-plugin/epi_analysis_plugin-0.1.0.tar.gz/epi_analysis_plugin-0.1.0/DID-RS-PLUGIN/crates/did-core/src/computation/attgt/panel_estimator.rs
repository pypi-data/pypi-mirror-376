use arrow::array::{ArrayRef, BooleanArray, Float64Array, Int64Array};
use arrow::record_batch::RecordBatch;
use faer::Mat;

use super::estimate::AttGtEstimate;
use crate::estimators::did::panel::drdid::DRDID;
use crate::DidError;

pub fn compute_single_att_gt_panel(
    this: &crate::computation::attgt::AttGtComputer,
    _group: i64,
    _time: i64,
    data_2x2: &RecordBatch,
) -> Result<AttGtEstimate, DidError> {
    let treatment_array = data_2x2
        .column_by_name("D")
        .ok_or_else(|| DidError::Specification("Column 'D' not found in 2x2 batch".into()))?
        .as_any()
        .downcast_ref::<Int64Array>()
        .ok_or_else(|| DidError::Specification("Column 'D' must be Int64".into()))?;
    let outcome_array = data_2x2
        .column_by_name("delta_y")
        .ok_or_else(|| DidError::Specification("Column 'delta_y' not found in 2x2 batch".into()))?
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| DidError::Specification("Column 'delta_y' must be Float64".into()))?;

    let control_cols = &data_2x2.columns()[2..];
    let x = build_covariate_matrix(data_2x2.num_rows(), control_cols);
    let x_reg = x.clone();

    let drdid = DRDID::new(
        &x,
        Mat::from_fn(treatment_array.len(), 1, |i, _| {
            treatment_array.value(i) as f64
        }),
        x_reg,
        Mat::from_fn(outcome_array.len(), 1, |i, _| outcome_array.value(i)),
        this.config.loss,
    );

    // If unconditional (no control_vars), use did simple IF on cohort subset
    if this.config.control_vars.is_empty() {
        let n = data_2x2.num_rows();
        let dy: Vec<f64> = (0..n).map(|i| outcome_array.value(i)).collect();
        let d: Vec<f64> = (0..n).map(|i| treatment_array.value(i) as f64).collect();
        let w: Vec<f64> = vec![1.0; n];
        let p: f64 = (0..n).map(|i| d[i] * w[i]).sum::<f64>() / (n as f64);
        let mut num0 = 0.0;
        let mut den0 = 0.0;
        for i in 0..n {
            if d[i] == 0.0 {
                num0 += w[i] * dy[i];
                den0 += w[i];
            }
        }
        let mu0 = if den0 == 0.0 { 0.0 } else { num0 / den0 };
        let mut inf = Mat::zeros(n, 1);
        for i in 0..n {
            let term = (d[i] / p) - ((1.0 - d[i]) / (1.0 - p));
            *inf.get_mut(i, 0) = term * (dy[i] - mu0);
        }
        // ATT from DRDID for point estimate
        let (att, _) = drdid.estimate()?;
        return Ok(AttGtEstimate { att, inf, n1: n });
    }

    let (att, inf) = drdid.estimate()?;
    Ok(AttGtEstimate {
        att,
        inf,
        n1: data_2x2.num_rows(),
    })
}

fn build_covariate_matrix(n_rows: usize, control_cols: &[ArrayRef]) -> Mat<f64> {
    let mut x = Mat::zeros(n_rows, 1 + control_cols.len());
    for i in 0..n_rows {
        *x.get_mut(i, 0) = 1.0;
        for (j, col) in control_cols.iter().enumerate() {
            let v = col.as_any().downcast_ref::<Float64Array>().map_or_else(
                || {
                    col.as_any().downcast_ref::<BooleanArray>().map_or_else(
                        || {
                            col.as_any()
                                .downcast_ref::<Int64Array>()
                                .map_or(0.0, |ia| ia.value(i) as f64)
                        },
                        |ba| if ba.value(i) { 1.0 } else { 0.0 },
                    )
                },
                |fa| fa.value(i),
            );
            *x.get_mut(i, j + 1) = v;
        }
    }
    x
}
