Polars Plugin Integration Plan for did-core

Decisions (agreed)
- Input shape: Whole Polars `DataFrame` passed to the plugin function (not many separate Series).
- Config passing: A single JSON/struct argument that mirrors `did_core::types::DidConfig`.
- Interop mechanism: In-process Arrow C Data Interface (FFI) between Polars (arrow2) and did-core (arrow 1.x). IPC remains an optional fallback, but not the primary path.

Goals
- Expose key did-core computations (ATT(g,t) and aggregations) as vectorized functions callable from Polars expressions.
- Support both Python Polars and Rust Polars where feasible.
- Avoid data copies by leveraging Arrow C Data Interface between Polars (arrow2) and did-core (arrow).

Candidate APIs to Expose
- att_gt: compute ATT(g,t) for a dataset with schema matching did-core expectations.
- aggregate: given att_gt/influence output, compute overall/group/dynamic/calendar aggregations, optionally with uniform bands.
- diagnostics: get panel info (balanced/unbalanced, repeated cross-sections) for quick checks.

Data Interop Strategy
- did-core operates on `arrow::record_batch::RecordBatch` and related Arrow 1.x types.
- Polars uses `arrow2` internally. Direct types are incompatible but can be bridged using the Arrow C Data Interface (FFI) provided by both `arrow` and `arrow2` crates.
- Zero-copy conversion approach:
  1) From Polars `DataFrame`/`Series` obtain arrow2 arrays.
  2) Export to C-FFI (`arrow2::ffi::export_*`).
  3) Import into Arrow 1 (`arrow::ffi::import_*`) to construct `arrow::ArrayRef` and `arrow::RecordBatch` for did-core.
  4) Compute with did-core.
  5) For results that return tabular data (e.g., att_gt list), build Arrow 1 arrays, export via FFI, import them back to arrow2, then wrap as Polars `Series`/`DataFrame`.
- If FFI proves too brittle, a fallback is to materialize to Parquet in-memory (or temp file) and re-read via did-core; this is slower and should be reserved for a first MVP only.

Plugin Shape (Python and Rust)
- Create a new crate `did-polars-plugin` in this workspace.
- Dependencies: `polars` (with `lazy` and `fmt` features), `did-core`, `arrow` (same version as did-core), `arrow2` (matching Polars), and optionally `polars-plugins` if using Polars’ dynamic plugin mechanism for Python.
- Provide two layers:
  - Low-level: conversion utilities between Polars DataFrame and Arrow RecordBatch via FFI, plus JSON -> config parsing.
  - High-level plugin functions (whole-DataFrame input + single JSON/struct config):
    - `did_att_gt(df: DataFrame, config_json: &str) -> DataFrame`
      - `config_json` is parsed into `DidConfigLike` (serde), then mapped to `did_core::DidConfig`.
    - `did_aggregate(df: DataFrame, result_json: &str, request_json: &str) -> DataFrame` (optional in v1)
      - Alternative: return a `result_json` from `did_att_gt` for later reuse.
    - `did_panel_info(df: DataFrame, config_json: &str) -> DataFrame|Series(Struct)`

Minimal Rust API (callable from Rust Polars)
- Provide functions that take a Polars `DataFrame` + a JSON config string (or struct) and return a Polars `DataFrame` for results.
- Example signatures:
  - `pub fn att_gt_df(df: &polars::prelude::DataFrame, config_json: &str) -> anyhow::Result<DataFrame>`
  - `pub fn aggregate_df(df: &DataFrame, result_json: &str, request_json: &str) -> anyhow::Result<DataFrame>`

Dynamic Plugin for Python Polars (optional, recommended)
- Use the Polars plugin mechanism to compile a `cdylib` exposing plugin functions that can be registered from Python, enabling expressions like:
  - `lf.select(pl.plugin("did_att_gt", df=pl.all().struct.field(..), config_json=json.dumps({...})))`
  - Or: pass the whole frame through the plugin call if the API supports a `DataFrame`-valued argument.
- The exact Python registration API is version-dependent; we will align with the same approach used by your `matching_plugin`.

Config Types for Plugins
- Define lightweight, serde-serializable structs in `did-polars-plugin` that mirror:
  - `did_core::types::DidConfig`
  - `did_core::computation::aggregation::{AggregationType, ConfidenceLevel, AggregationRequest}`
- Primary function signatures accept `config_json: &str` (serde_json) for easy cross-language passing.
- Keep enums and field names aligned with did-core; translate to did-core types internally.

Implementation Steps
1) Crate scaffolding `crates/did-polars-plugin` (library; add `cdylib` crate-type for Python plugin).
2) Add conversion utilities:
   - `polars_df_to_arrow_batch(df: &DataFrame) -> anyhow::Result<arrow::record_batch::RecordBatch>` via arrow2 <-> arrow FFI.
   - `arrow_batch_to_polars_df(batch: &arrow::record_batch::RecordBatch) -> anyhow::Result<DataFrame>` for returning tabular results.
   - JSON parsing: `DidConfigLike` and `AggregationRequestLike` with `serde` and `TryFrom` into did-core types.
3) Implement `att_gt_df` (whole DataFrame + JSON config):
   - Build `RecordBatch` from input `DataFrame`.
   - Parse `config_json` to `DidConfigLike` and construct `DidConfig`.
   - Call `DidEstimator::from_batch(...).fit()`.
   - Convert `att_gt: Vec<AttGtResult>` into a Polars `DataFrame` with columns `[group, time, att, se, t_stat, p_value, conf_low, conf_high]`.
   - Optionally include a serialized `result_json` for later aggregation calls.
4) Implement `aggregate_df` (optional v2):
   - Accept `result_json` from a prior `att_gt_df` call and `request_json` for aggregation options.
   - Rehydrate `DidResult` and call did-core’s aggregation APIs; return aggregated effects as a DataFrame.
5) Implement `panel_info_df`:
   - Use `DidEstimator::get_panel_info()` and return fields in a single-row `DataFrame` or a `Struct` series.
6) Add plugin export bindings for Python (if desired):
   - Implement wrapper functions using Polars plugin macros mirroring your `matching_plugin` approach.

Type and Null Handling
- Ensure input columns match expected types: outcome numeric (Float64), treatment binary (Int64/Boolean), time and id integer, controls numeric/bool as applicable.
- Add casts inside the plugin to coerce to compatible types; emit descriptive errors for mismatches.
- Respect null handling consistent with did-core’s preprocessing/validation.

Performance Considerations
- Favor zero-copy FFI conversions to avoid data duplication.
- Reuse thread pools from rayon where possible; Polars also parallelizes, so avoid nested parallel regions where it hurts.
- For large influence matrices, consider returning summaries or chunked outputs on the Python side.

Testing Strategy
- Unit-test conversion utilities with small synthetic frames.
- Golden tests comparing plugin output to direct did-core calls on the same Arrow `RecordBatch`.
- If R comparisons exist, keep the existing tests in `tests/core/validation` as cross-reference; do not duplicate them in the plugin crate.

Open Questions / Risks
- Arrow vs arrow2 FFI: version compatibility must be pinned; mismatches can cause subtle issues.
- Aggregation APIs often need the full `DidResult` (group probabilities, influence). Decide whether plugin returns a handle/ticket to reuse internal state, or materialize all needed pieces for later aggregation.
- Polars plugin Python API varies by version; confirm the register/call pattern for the target environment.

MVP Recommendation
- Start with a Rust-only API (`att_gt_df`, `panel_info_df`) callable from Rust Polars.
- Add Python plugin exports once core interop is stable.

Example (conceptual, Rust)
```rust
pub fn att_gt_df(df: &polars::prelude::DataFrame, cfg: DidConfigLike) -> anyhow::Result<DataFrame> {
    let batch = polars_df_to_arrow_batch(df)?;
    let core_cfg: did_core::DidConfig = cfg.into();
    let est = did_core::DidEstimator::from_batch(batch, core_cfg)?;
    let res = est.fit()?;
    // Convert res.att_gt (Vec<AttGtResult>) to Polars DataFrame
    Ok(attgt_vec_to_polars_df(&res.att_gt)?)
}
```

Next Steps
- Approve creation of `crates/did-polars-plugin` with conversion utilities and `att_gt_df` implementation.
- Confirm target Polars version(s) and whether Python plugin export is desired in the first iteration.
