//! Shared functionality for matching algorithms
use polars::prelude::*;
use rustc_hash::FxHashMap;

/// Process vital events data into a lookup map
pub fn process_vital_events(
    vital_events_df: Option<&DataFrame>,
) -> PolarsResult<FxHashMap<String, i32>> {
    let mut vital_events_map = FxHashMap::default();

    if let Some(vital_df) = vital_events_df {
        println!("Processing {} vital events...", vital_df.height());

        let vital_pnrs = vital_df.column("PNR")?.str()?;
        let vital_dates = vital_df.column("EVENT_DATE")?.date()?;
        let vital_events = vital_df.column("EVENT")?.str()?;
        let vital_roles = vital_df.column("ROLE")?.str()?;

        for i in 0..vital_pnrs.len() {
            if let (Some(pnr), Some(event_date), Some(event), Some(role)) = (
                vital_pnrs.get(i),
                vital_dates.phys.get(i),
                vital_events.get(i),
                vital_roles.get(i),
            ) {
                let key = format!("{pnr}:{event}:{role}");
                vital_events_map.insert(key, event_date);
            }
        }
        println!("Indexed {} vital events", vital_events_map.len());
    }

    Ok(vital_events_map)
}

/// Build result `DataFrame` from matched results
pub fn build_result_dataframe(
    all_individuals: &DataFrame,
    matched_results: Vec<(String, Vec<String>)>,
) -> PolarsResult<DataFrame> {
    let mut result_case_pnrs = Vec::new();
    let mut result_matched_controls = Vec::new();
    let mut result_n_matched = Vec::new();

    for (case_pnr, matched_controls) in matched_results {
        result_case_pnrs.push(Some(case_pnr));
        result_n_matched.push(u32::try_from(matched_controls.len()).unwrap_or(u32::MAX));

        if matched_controls.is_empty() {
            result_matched_controls.push(None);
        } else {
            result_matched_controls.push(Some(matched_controls));
        }
    }

    // Convert to Polars DataFrame
    let matched_controls_series: ListChunked = result_matched_controls
        .into_iter()
        .map(|opt_vec| {
            opt_vec.map(|vec| {
                let strings: Vec<Option<&str>> = vec.iter().map(|s| Some(s.as_str())).collect();
                Series::new(PlSmallStr::from_static(""), strings)
            })
        })
        .collect();

    let result_df = DataFrame::new(vec![
        Series::new(PlSmallStr::from_static("case_pnr"), result_case_pnrs).into(),
        matched_controls_series
            .into_series()
            .with_name(PlSmallStr::from_static("matched_controls"))
            .into(),
        Series::new(PlSmallStr::from_static("n_matched"), result_n_matched).into(),
    ])?;

    // Join back with original case information
    let cases_only = all_individuals
        .clone()
        .lazy()
        .filter(col("SCD_STATUS").eq(lit("SCD")))
        .collect()?;

    let cases_with_matches = cases_only
        .lazy()
        .join(
            result_df.lazy(),
            [col("PNR")],
            [col("case_pnr")],
            JoinArgs::new(JoinType::Left),
        )
        .collect()?;

    Ok(cases_with_matches)
}
