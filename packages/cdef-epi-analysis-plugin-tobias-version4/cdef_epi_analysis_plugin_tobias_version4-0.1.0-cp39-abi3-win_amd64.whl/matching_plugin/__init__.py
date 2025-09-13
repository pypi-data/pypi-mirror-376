"""
Epidemiological Analysis Plugin

This plugin provides high-performance epidemiological analysis tools including:
- Case-control matching with proper risk-set sampling methodology
- Temporal data extraction from registry files with dynamic year ranges
- Optimized Rust implementations for large-scale data processing
"""

from __future__ import annotations

import json
from typing import Tuple, Literal

import polars as pl

from matching_plugin._internal import __version__ as __version__  # type: ignore
from matching_plugin._internal import (
    did_aggregate_py as _did_aggregate_rust,  # type: ignore
)
from matching_plugin._internal import did_att_gt_py as _did_att_gt_rust  # type: ignore
from matching_plugin._internal import (
    did_panel_info_py as _did_panel_info_rust,  # type: ignore
)
from matching_plugin._internal import (
    extract_cohabitation_status_py as _extract_cohabitation_rust,
)  # type: ignore
from matching_plugin._internal import (
    extract_ethnicity_temporal_py as _extract_ethnicity_rust,
)  # type: ignore
from matching_plugin._internal import (
    extract_highest_education_level_batched_py as _extract_education_batched_rust,
)  # type: ignore
from matching_plugin._internal import (
    extract_highest_education_level_py as _extract_education_rust,
)  # type: ignore
from matching_plugin._internal import (
    extract_parent_income_timeseries_py as _extract_parent_income_rust,
)  # type: ignore
from matching_plugin._internal import (
    extract_parent_socio13_py as _extract_parent_socio13_rust,
)  # type: ignore
from matching_plugin._internal import (
    extract_temporal_data_batched_py as _extract_temporal_batched_rust,
)  # type: ignore
from matching_plugin._internal import (
    extract_temporal_data_dynamic_year_py as _extract_temporal_rust,
)  # type: ignore
from matching_plugin._internal import (
    format_match_output as _format_match_output_rust,  # type: ignore
)
from matching_plugin._internal import (
    match_scd_cases as _match_scd_cases_rust,  # type: ignore
)

__all__ = [
    "__version__",
    "complete_scd_matching_workflow",
    "create_match_output_format",
    "extract_temporal_data",
    "extract_temporal_data_batched",
    "extract_highest_education_level",
    "extract_highest_education_level_batched",
    "extract_ethnicity_categories",
    "extract_parent_socio13",
    "extract_cohabitation_status",
    "extract_parent_income_timeseries",
    "compute_att_gt",
    "get_panel_info",
    "aggregate_effects",
    "debug_did_cells",
    "build_parent_did_panel",
]


def complete_scd_matching_workflow(
    mfr_data: pl.DataFrame,
    lpr_data: pl.DataFrame,
    vital_data: pl.DataFrame | None = None,
    matching_ratio: int = 5,
    birth_date_window_days: int = 30,
    parent_birth_date_window_days: int = 365,
    match_parent_birth_dates: bool = True,
    match_mother_birth_date_only: bool = False,
    require_both_parents: bool = False,
    match_parity: bool = True,
    match_birth_type: bool = False,
    algorithm: str = "spatial_index",
) -> pl.DataFrame:
    """
    Complete SCD case-control matching workflow with risk-set sampling.

    Combines MFR/LPR data, performs matching, and returns the standard output format.
    Cases are processed chronologically by diagnosis date to avoid immortal time bias.
    Optionally incorporates vital status data for temporal validity.

    Parameters
    ----------
    mfr_data : pl.DataFrame
        Output from process_mfr_data() - eligible population with parent info
    lpr_data : pl.DataFrame
        Output from process_lpr_data() - SCD status for all eligible children
    vital_data : pl.DataFrame, optional
        Output from process_vital_status() - death/emigration events for children and parents
        If provided, ensures individuals and parents are alive/present at matching time
    matching_ratio : int, default 5
        Number of controls to match per case
    birth_date_window_days : int, default 30
        Maximum difference in days between case and control birth dates
    parent_birth_date_window_days : int, default 365
        Maximum difference in days between parent birth dates
    match_parent_birth_dates : bool, default True
        Whether to match on parent birth dates
    match_mother_birth_date_only : bool, default False
        Whether to match only on maternal birth dates
    require_both_parents : bool, default False
        Whether both parents are required for matching
    match_parity : bool, default True
        Whether to match on parity (birth order)
    match_birth_type : bool, default False
        Whether to match on birth type (singleton, doubleton, tripleton, quadleton, multiple)
        Requires 'birth_type' column in input data
    algorithm : str, default "spatial_index"
        Algorithm to use for matching. Options:
        - "spatial_index": Optimized with parallel processing and spatial indexing
        - "partitioned_parallel": Ultra-optimized with advanced data structures (20-60% faster than spatial_index)

    Returns
    -------
    pl.DataFrame
        Output format: MATCH_INDEX, PNR, ROLE, INDEX_DATE
        - MATCH_INDEX: Unique identifier for each case-control group (1:X matching)
        - PNR: Person identifier
        - ROLE: "case" or "control"
        - INDEX_DATE: SCD diagnosis date from the case

        When vital_data is provided:
        - Ensures children and parents are alive/present at matching time
        - Individuals who died or emigrated before case diagnosis cannot serve as controls
        - Chronological processing with proper temporal validity
    """
    # Validate algorithm parameter
    valid_algorithms = ["spatial_index", "partitioned_parallel"]
    if algorithm not in valid_algorithms:
        raise ValueError(
            f"Invalid algorithm '{algorithm}'. Must be one of: {valid_algorithms}"
        )

    algorithm_names = {
        "spatial_index": "optimized with spatial indexing",
        "partitioned_parallel": "ultra-optimized with advanced data structures",
    }

    if vital_data is not None:
        print(
            f"Starting SCD case-control matching with vital status using {algorithm_names[algorithm]}..."
        )
    else:
        print(
            f"Starting SCD case-control matching using {algorithm_names[algorithm]}..."
        )

    # Combine MFR and LPR data
    combined_data = mfr_data.join(lpr_data, on="PNR", how="inner")
    print(f"Combined dataset: {len(combined_data):,} individuals")

    if vital_data is not None:
        print(f"Vital events data: {len(vital_data):,} events")

    # Perform risk-set sampling matching (with or without vital data)
    config = {
        "matching": {
            "birth_date_window_days": birth_date_window_days,
            "parent_birth_date_window_days": parent_birth_date_window_days,
            "match_parent_birth_dates": match_parent_birth_dates,
            "match_mother_birth_date_only": match_mother_birth_date_only,
            "require_both_parents": require_both_parents,
            "match_parity": match_parity,
            "match_birth_type": match_birth_type,
            "matching_ratio": matching_ratio,
        },
        "algorithm": algorithm,
    }

    matched_cases = _match_scd_cases_rust(combined_data, vital_data, json.dumps(config))

    # Transform to requested output format
    output_df = _format_match_output_rust(matched_cases)

    print(f"Matching complete: {len(output_df):,} records")
    print(f"Match groups: {output_df['MATCH_INDEX'].n_unique():,}")
    print(f"Cases: {(output_df['ROLE'] == 'case').sum():,}")
    print(f"Controls: {(output_df['ROLE'] == 'control').sum():,}")

    return output_df


def create_match_output_format(matched_cases_df: pl.DataFrame) -> pl.DataFrame:
    """
    Transform matched cases into the standard output format.

    Parameters
    ----------
    matched_cases_df : pl.DataFrame
        Matched cases DataFrame from the Rust matching functions

    Returns
    -------
    pl.DataFrame
        Standard output format: MATCH_INDEX, PNR, ROLE, INDEX_DATE
        - MATCH_INDEX: Unique identifier for each case-control group
        - PNR: Person identifier
        - ROLE: "case" or "control"
        - INDEX_DATE: SCD diagnosis date from the case (same for all members of match group)
    """
    return _format_match_output_rust(matched_cases_df)


def extract_temporal_data(
    df: pl.DataFrame,
    identifier_col: str,
    index_date_col: str,
    registry_path_pattern: str,
    variable_col: str,
    temporal_range: Tuple[int, int] = (-1, 1),
    additional_cols: list[str] | None = None,
    use_cache: bool = True,
) -> pl.DataFrame:
    """
    Extract temporal data from registry files with dynamic year ranges.

    This function provides high-performance extraction of temporal data from registry
    files based on dynamic year ranges relative to index dates. Uses optimized Rust
    implementation for efficient processing of large datasets.

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe with identifiers and index dates
    identifier_col : str
        Column name for unique identifiers (e.g., "PNR")
    index_date_col : str
        Column name for index dates (e.g., "diagnosis_date")
    registry_path_pattern : str
        Path pattern for registry files supporting glob patterns
        (e.g., "/data/registries/registry_*.parquet")
    variable_col : str
        Column name for the main variable to extract from registry
    temporal_range : Tuple[int, int], default=(-1, 1)
        Range of years relative to index year (start_offset, end_offset)
        - (-1, 1): Extract data from 1 year before to 1 year after index
        - (-2, 0): Extract data from 2 years before to index year
    additional_cols : list[str] | None, default=None
        Additional columns to extract from registry files
    use_cache : bool, default=True
        Whether to cache registry files for repeated calls (improves performance)

    Returns
    -------
    pl.DataFrame
        DataFrame with temporal data joined from registry files containing:
        - Original identifier and index date columns
        - ARET: Registry year for each extracted record
        - RELATIVE_YEAR: Years relative to index year (e.g., -1, 0, 1)
        - Variable columns from registry files

    Examples
    --------
    Extract prescription data around diagnosis dates:

    >>> cases_df = pl.DataFrame({
    ...     "PNR": ["123456", "789012"],
    ...     "diagnosis_date": ["2020-05-15", "2021-08-20"]
    ... })
    >>> prescriptions = extract_temporal_data(
    ...     df=cases_df,
    ...     identifier_col="PNR",
    ...     index_date_col="diagnosis_date",
    ...     registry_path_pattern="/data/prescriptions/lms_*.parquet",
    ...     variable_col="ATC_CODE",
    ...     temporal_range=(-2, 1),  # 2 years before to 1 year after
    ...     additional_cols=["DOSE", "STRENGTH"]
    ... )

    Extract hospital admissions with 1-year window:

    >>> admissions = extract_temporal_data(
    ...     df=cases_df,
    ...     identifier_col="PNR",
    ...     index_date_col="diagnosis_date",
    ...     registry_path_pattern="/data/lpr/lpr_*.ipc",
    ...     variable_col="ICD10_CODE",
    ...     temporal_range=(-1, 1)
    ... )

    Notes
    -----
    - Registry files must contain the identifier column and year information
    - If ARET column is missing, it will be inferred from filename
    - Supports .parquet, .ipc, .feather, and .arrow file formats
    - Files are processed in deterministic sorted order
    - Uses LRU caching for repeated registry file access
    """
    return _extract_temporal_rust(
        df,
        identifier_col,
        index_date_col,
        registry_path_pattern,
        variable_col,
        temporal_range,
        additional_cols,
        use_cache,
    )


def extract_parent_socio13(
    df: pl.DataFrame,
    identifier_col: str,
    index_date_col: str,
    akm_registry_pattern: str,
    year_offset: int = -1,
) -> pl.DataFrame:
    return _extract_parent_socio13_rust(
        df, identifier_col, index_date_col, akm_registry_pattern, year_offset
    )


def extract_cohabitation_status(
    df: pl.DataFrame,
    identifier_col: str,
    index_date_col: str,
    bef_registry_pattern: str,
    year_offset: int = -1,
) -> pl.DataFrame:
    return _extract_cohabitation_rust(
        df, identifier_col, index_date_col, bef_registry_pattern, year_offset
    )


def extract_parent_income_timeseries(
    df: pl.DataFrame,
    identifier_col: str,
    index_date_col: str,
    ind_registry_pattern: str,
    income_vars: list[str],
    temporal_range: tuple[int, int] = (-10, 10),
) -> pl.DataFrame:
    return _extract_parent_income_rust(
        df,
        identifier_col,
        index_date_col,
        ind_registry_pattern,
        income_vars,
        temporal_range,
    )


def debug_did_cells(
    df: pl.DataFrame,
    config: dict | str,
    limit: int | None = 50,
) -> pl.DataFrame:
    cfg = config if isinstance(config, dict) else json.loads(config)
    gcol = cfg["group_var"] if cfg.get("group_var") else cfg["treatment_var"]
    tcol = cfg["time_var"]
    control_group = cfg.get("control_group", "NotYetTreated")

    tlist = (
        df.select(pl.col(tcol).unique()).to_series().to_list() if df.height > 0 else []
    )
    tlist = sorted([int(x) for x in tlist if x is not None])
    glist = (
        df.select(pl.col(gcol).unique()).to_series().to_list() if df.height > 0 else []
    )
    glist = sorted([int(x) for x in glist if x not in (None, 0)])
    union_vals = sorted(set(glist) | set(tlist))
    idx_map = {v: i + 1 for i, v in enumerate(union_vals)}

    def _idx(val: int | None) -> int | None:
        if val is None:
            return None
        return idx_map.get(int(val))

    df_std = df.with_columns(
        [
            pl.col(gcol).map_elements(_idx, return_dtype=pl.Int64).alias("_g_idx"),
            pl.col(tcol).map_elements(_idx, return_dtype=pl.Int64).alias("_t_idx"),
        ]
    )

    rows: list[dict] = []
    for g in glist:
        g_idx = idx_map[g]
        for t in tlist:
            pret = (g - 1) if t >= g else (t - 1)
            if pret not in tlist:
                continue
            t_idx = idx_map[t]
            pret_idx = idx_map[pret]
            max_idx = max(t_idx, pret_idx)

            dta = df_std.filter(pl.col(tcol).is_in([t, pret]))
            is_treated = pl.col("_g_idx") == g_idx
            if control_group == "NeverTreated":
                is_control = pl.col(gcol) == 0
            else:
                is_control = (pl.col(gcol) == 0) | (
                    (pl.col("_g_idx") > max_idx) & (pl.col("_g_idx") != g_idx)
                )

            treated_post = dta.filter(is_treated & (pl.col(tcol) == t)).height
            treated_pre = dta.filter(is_treated & (pl.col(tcol) == pret)).height
            control_post = dta.filter(is_control & (pl.col(tcol) == t)).height
            control_pre = dta.filter(is_control & (pl.col(tcol) == pret)).height

            rows.append(
                {
                    "group": g,
                    "time": t,
                    "pret": pret,
                    "n_treated_pre": treated_pre,
                    "n_treated_post": treated_post,
                    "n_control_pre": control_pre,
                    "n_control_post": control_post,
                    "has_all_cells": all(
                        x > 0
                        for x in [treated_pre, treated_post, control_pre, control_post]
                    ),
                }
            )

    out = pl.DataFrame(rows)
    if limit is not None and out.height > limit:
        return out.sort(["has_all_cells", "group", "time"]).head(limit)
    return out


# -------------------------------
# Join and schema safety helpers
# -------------------------------


def _assert_unique_keys(
    lf: pl.LazyFrame, keys: list[str], context: str, sample: int = 10
) -> None:
    """Assert that `lf` is unique on `keys`. Raises ValueError with samples if not.

    Materializes only small diagnostics (up to `sample` offending groups).
    """
    offenders = (
        lf.group_by(keys)
        .agg(pl.len().alias("n"))
        .filter(pl.col("n") > 1)
        .limit(sample)
        .collect()
    )
    if offenders.height > 0:
        raise ValueError(
            f"Non-unique right-hand keys for join in {context}. Keys: {keys}. "
            f"Examples (first {sample}):\n{offenders}"
        )


def _safe_join_right_unique(
    left: pl.LazyFrame,
    right: pl.LazyFrame,
    on: list[str] | str,
    *,
    how: Literal[
        "inner", "left", "right", "full", "semi", "anti", "cross", "outer"
    ] = "left",
    context: str = "join",
    assert_unique: bool = True,
) -> pl.LazyFrame:
    """Perform a join after ensuring the right is unique on `on`.

    - De-duplicates the right by `on` with keep='first'.
    - Optionally asserts original right is unique (helpful during development).
    - Returns a LazyFrame join.
    """
    on_list = [on] if isinstance(on, str) else list(on)
    if assert_unique:
        _assert_unique_keys(right, on_list, context)
    right_u = right.unique(subset=on_list, keep="first")
    return left.join(right_u, on=on_list, how=how)


def build_parent_did_panel(
    match_df: pl.DataFrame,
    relations_df: pl.DataFrame,
    *,
    ind_registry_pattern: str,
    income_vars: list[str],
    bef_registry_pattern: str | None = None,
    akm_registry_pattern: str | None = None,
    uddf_file_path: str | None = None,
    income_temporal_range: tuple[int, int] = (-10, 10),
) -> pl.DataFrame:
    # Normalize input schemas to canonical names (upper-case) and robust date dtype
    def _normalize_columns(
        df: pl.DataFrame, mapping: dict[str, list[str]]
    ) -> pl.DataFrame:
        rename_map: dict[str, str] = {}
        cols_lower = {c.lower(): c for c in df.columns}
        for canon, aliases in mapping.items():
            for a in aliases:
                src = cols_lower.get(a.lower())
                if src is not None:
                    rename_map[src] = canon
                    break
        return df.rename(rename_map)

    # Accept common lowercase/alternative names from the matching pipeline
    match_syn = {
        "PNR": ["PNR", "pnr", "cpr"],
        "INDEX_DATE": ["INDEX_DATE", "index_date", "diagnosis_date"],
        "ROLE": ["ROLE", "role"],
        # Ignored here but allowed to pass through
        "MATCH_ID": ["MATCH_ID", "match_id"],
    }
    rel_syn = {
        "PNR": ["PNR", "pnr", "cpr"],
        "CPR_MODER": ["CPR_MODER", "cpr_moder", "mother_cpr", "moder_cpr"],
        "CPR_FADER": ["CPR_FADER", "cpr_fader", "father_cpr", "fader_cpr"],
    }

    match_df = _normalize_columns(match_df, match_syn)
    relations_df = _normalize_columns(relations_df, rel_syn)

    # Validate required columns after normalization
    required_match_cols = {"PNR", "INDEX_DATE", "ROLE"}
    missing = required_match_cols - set(match_df.columns)
    if missing:
        raise ValueError(
            "match_df missing required columns after normalization: "
            f"{sorted(missing)}. Present columns: {match_df.columns}"
        )
    required_rel_cols = {"PNR", "CPR_MODER", "CPR_FADER"}
    missing_rel = required_rel_cols - set(relations_df.columns)
    if missing_rel:
        raise ValueError(
            "relations_df missing required columns after normalization: "
            f"{sorted(missing_rel)}. Present columns: {relations_df.columns}"
        )

    # Ensure INDEX_DATE is a proper date/datetime
    if match_df.get_column("INDEX_DATE").dtype in (pl.Utf8, pl.String):
        match_df = match_df.with_columns(
            [
                pl.coalesce(
                    [
                        pl.col("INDEX_DATE").str.to_date(strict=False, format=None),
                        pl.col("INDEX_DATE").str.to_datetime(strict=False, format=None),
                    ]
                ).alias("INDEX_DATE")
            ]
        )
    # If still not temporal, try casting to a Date dtype
    if match_df.get_column("INDEX_DATE").dtype not in (pl.Date, pl.Datetime):
        match_df = match_df.with_columns(
            [pl.col("INDEX_DATE").cast(pl.Date, strict=False).alias("INDEX_DATE")]
        )

    # Ensure a single parent mapping per child to prevent join fanouts
    # Do this lazily and only keep the columns we actually need.
    relations_map = (
        relations_df.lazy()
        .select(["PNR", "CPR_MODER", "CPR_FADER"])  # projection pushdown
        .unique(subset=["PNR"], keep="first")
        .collect()
    )

    # Minimal base input: only PNR and INDEX_DATE, unique pairs.
    base_input = (
        match_df.lazy()
        .select(["PNR", "INDEX_DATE"])  # projection pushdown
        .unique(subset=["PNR", "INDEX_DATE"], keep="first")
        .collect()
    )
    # For Rust extractors that REQUIRE parent CPRs on the input, create a small base with parents
    base = base_input.lazy().join(relations_map.lazy(), on="PNR", how="inner").collect()

    # Income time series for both parents (wide MOR_/FAR_ per child-year)
    income_wide = extract_parent_income_timeseries(
        df=base,
        identifier_col="PNR",
        index_date_col="INDEX_DATE",
        ind_registry_pattern=ind_registry_pattern,
        income_vars=income_vars,
        temporal_range=income_temporal_range,
    )
    # Attach parent IDs to the income panel (using unique relations mapping)
    income_wide = (
        _safe_join_right_unique(
            income_wide.lazy(),
            relations_map.lazy().select(["PNR", "CPR_MODER", "CPR_FADER"]),
            on=["PNR"],
            how="left",
            context="income_wide ⨝ relations_map on PNR",
        )
        .unique(subset=["PNR", "INDEX_DATE", "ARET", "RELATIVE_YEAR"], keep="first")
        .collect()
    )

    # Build long panel by stacking mother and father rows
    long_parts_lf: list[pl.LazyFrame] = []
    # Mother
    mother_cols = {f"MOR_{v}": v for v in income_vars}
    mother_lf = (
        income_wide.lazy()
        .select(
            [
                "PNR",
                "INDEX_DATE",
                pl.col("ARET").alias("year"),
                pl.col("RELATIVE_YEAR").alias("event_time"),
                pl.col("CPR_MODER").alias("parent_pnr"),
                *[pl.col(k).alias(v) for k, v in mother_cols.items()],
            ]
        )
        .with_columns([pl.lit("F").alias("gender")])
        .filter(pl.col("parent_pnr").is_not_null())
    )
    long_parts_lf.append(mother_lf)
    # Father
    father_cols = {f"FAR_{v}": v for v in income_vars}
    father_lf = (
        income_wide.lazy()
        .select(
            [
                "PNR",
                "INDEX_DATE",
                pl.col("ARET").alias("year"),
                pl.col("RELATIVE_YEAR").alias("event_time"),
                pl.col("CPR_FADER").alias("parent_pnr"),
                *[pl.col(k).alias(v) for k, v in father_cols.items()],
            ]
        )
        .with_columns([pl.lit("M").alias("gender")])
        .filter(pl.col("parent_pnr").is_not_null())
    )
    long_parts_lf.append(father_lf)

    panel_lf = pl.concat(long_parts_lf, how="vertical").unique(
        subset=["PNR", "INDEX_DATE", "parent_pnr", "gender", "year", "event_time"],
        keep="first",
    )

    # Defensive: ensure parent_pnr exists (reconstruct from relations_map + gender if missing)
    # parent_pnr is produced above for both mother and father rows; no additional guard needed

    # Join case/control and compute cohort (first.treat) and treated
    panel_lf = _safe_join_right_unique(
        panel_lf,
        match_df.lazy().select(["PNR", "INDEX_DATE", "ROLE"]),
        on=["PNR", "INDEX_DATE"],
        how="left",
        context="panel ⨝ match_df on [PNR, INDEX_DATE]",
    )
    panel_lf = panel_lf.with_columns(
        [
            pl.col("INDEX_DATE").dt.year().alias("index_year"),
            (pl.col("ROLE") == "case").cast(pl.Int8).alias("treated"),
        ]
    )
    panel_lf = panel_lf.with_columns(
        [
            pl.when(pl.col("treated") == 1)
            .then(pl.col("index_year"))
            .otherwise(pl.lit(0))
            .cast(pl.Int64)
            .alias("first.treat"),
        ]
    )

    # Optional baseline covariates (measured at index_year-1)
    if akm_registry_pattern is not None:
        socio = (
            extract_parent_socio13(
                df=base,
                identifier_col="PNR",
                index_date_col="INDEX_DATE",
                akm_registry_pattern=akm_registry_pattern,
                year_offset=-1,
            )
            .unique(subset=["PNR", "INDEX_DATE", "ARET", "RELATIVE_YEAR"], keep="first")
            .join(relations_map, on="PNR", how="left")
        )
        socio_long_lf = pl.concat(
            [
                socio.lazy()
                .select(
                    [
                        "PNR",
                        "INDEX_DATE",
                        pl.col("MOR_SOCIO13_CAT").alias("socio13_cat"),
                        pl.col("CPR_MODER").alias("parent_pnr"),
                    ]
                )
                .with_columns([pl.lit("F").alias("gender")]),
                socio.lazy()
                .select(
                    [
                        "PNR",
                        "INDEX_DATE",
                        pl.col("FAR_SOCIO13_CAT").alias("socio13_cat"),
                        pl.col("CPR_FADER").alias("parent_pnr"),
                    ]
                )
                .with_columns([pl.lit("M").alias("gender")]),
            ],
            how="vertical",
        ).unique(subset=["PNR", "INDEX_DATE", "parent_pnr", "gender"], keep="first")

        panel_lf = panel_lf.join(
            socio_long_lf.select(
                ["PNR", "INDEX_DATE", "parent_pnr", "gender", "socio13_cat"]
            ),
            on=["PNR", "INDEX_DATE", "parent_pnr", "gender"],
            how="left",
        )

    if bef_registry_pattern is not None:
        cohab = (
            extract_cohabitation_status(
                df=base,
                identifier_col="PNR",
                index_date_col="INDEX_DATE",
                bef_registry_pattern=bef_registry_pattern,
                year_offset=-1,
            )
            .unique(subset=["PNR", "INDEX_DATE", "ARET", "RELATIVE_YEAR"], keep="first")
            .join(relations_map, on="PNR", how="left")
        )
        cohab_long_lf = pl.concat(
            [
                cohab.lazy()
                .select(
                    [
                        "PNR",
                        "INDEX_DATE",
                        pl.col("MOR_COHAB_STATUS").alias("cohab_status"),
                        pl.col("CPR_MODER").alias("parent_pnr"),
                    ]
                )
                .with_columns([pl.lit("F").alias("gender")]),
                cohab.lazy()
                .select(
                    [
                        "PNR",
                        "INDEX_DATE",
                        pl.col("FAR_COHAB_STATUS").alias("cohab_status"),
                        pl.col("CPR_FADER").alias("parent_pnr"),
                    ]
                )
                .with_columns([pl.lit("M").alias("gender")]),
            ],
            how="vertical",
        ).unique(subset=["PNR", "INDEX_DATE", "parent_pnr", "gender"], keep="first")

        panel_lf = panel_lf.join(
            cohab_long_lf.select(
                ["PNR", "INDEX_DATE", "parent_pnr", "gender", "cohab_status"]
            ),
            on=["PNR", "INDEX_DATE", "parent_pnr", "gender"],
            how="left",
        )

    # Child ethnicity at baseline (-1) as covariate (same value for both parents)
    if bef_registry_pattern is not None:
        # Reuse de-duplicated child-date pairs with parent CPRs (required by Rust extractor)
        base_unique = (
            _safe_join_right_unique(
                match_df.lazy().select(["PNR", "INDEX_DATE"]),
                relations_map.lazy().select(["PNR", "CPR_MODER", "CPR_FADER"]),
                on=["PNR"],
                how="inner",
                context="ethnicity base ⨝ relations_map on PNR",
            )
            .select(["PNR", "INDEX_DATE", "CPR_MODER", "CPR_FADER"])  # projection
            .unique(maintain_order=True)
            .collect()
        )
        eth = extract_ethnicity_categories(
            df=base_unique,
            identifier_col="PNR",
            index_date_col="INDEX_DATE",
            bef_registry_pattern=bef_registry_pattern,
            temporal_range=(-1, -1),
        )
        # Keep baseline only, attach as child_ethnicity
        eth_lf = (
            eth.lazy()
            .filter(pl.col("RELATIVE_YEAR") == -1)
            .select(
                [
                    "PNR",
                    "INDEX_DATE",
                    pl.col("ethnicity_category").alias("child_ethnicity"),
                ]
            )
        )
        panel_lf = panel_lf.join(eth_lf, on=["PNR", "INDEX_DATE"], how="left")

    # Parent highest education at baseline (-1) as covariate (single extractor call)
    if uddf_file_path is not None:
        mothers_map = (
            _safe_join_right_unique(
                match_df.lazy().select(["PNR", "INDEX_DATE"]),
                relations_map.lazy().select(["PNR", "CPR_MODER"]),
                on=["PNR"],
                how="inner",
                context="education mothers_map ⨝ relations_map on PNR",
            )
            .select(
                [
                    pl.col("PNR").alias("child_pnr"),
                    pl.col("INDEX_DATE"),
                    pl.col("CPR_MODER").alias("parent_pnr"),
                ]
            )
            .filter(pl.col("parent_pnr").is_not_null())
            .with_columns([pl.lit("F").alias("gender")])
            .collect()
        )
        fathers_map = (
            _safe_join_right_unique(
                match_df.lazy().select(["PNR", "INDEX_DATE"]),
                relations_map.lazy().select(["PNR", "CPR_FADER"]),
                on=["PNR"],
                how="inner",
                context="education fathers_map ⨝ relations_map on PNR",
            )
            .select(
                [
                    pl.col("PNR").alias("child_pnr"),
                    pl.col("INDEX_DATE"),
                    pl.col("CPR_FADER").alias("parent_pnr"),
                ]
            )
            .filter(pl.col("parent_pnr").is_not_null())
            .with_columns([pl.lit("M").alias("gender")])
            .collect()
        )
        parents_map = pl.concat([mothers_map, fathers_map], how="vertical").unique(
            subset=["parent_pnr", "INDEX_DATE", "child_pnr", "gender"], keep="first"
        )

        if parents_map.height > 0:
            edu_input = (
                parents_map.lazy()
                .select([pl.col("INDEX_DATE"), pl.col("parent_pnr").alias("PNR")])
                .unique(subset=["PNR", "INDEX_DATE"], keep="first")
                .collect()
            )
            # Assert the education input is one row per (PNR, INDEX_DATE) to avoid fanout
            _assert_unique_keys(
                edu_input.lazy(), ["PNR", "INDEX_DATE"], "education input uniqueness"
            )

            edu_all = extract_highest_education_level(
                df=edu_input,
                identifier_col="PNR",
                index_date_col="INDEX_DATE",
                uddf_file_path=uddf_file_path,
            ).rename({"highest_education_level": "education_level"})

            edu_long_lf = (
                edu_all.lazy()
                .join(
                    parents_map.lazy(),
                    left_on=["PNR", "INDEX_DATE"],
                    right_on=["parent_pnr", "INDEX_DATE"],
                    how="left",
                )
                .select(
                    [
                        pl.col("child_pnr").alias("PNR"),
                        "INDEX_DATE",
                        pl.col("parent_pnr"),
                        "gender",
                        "education_level",
                    ]
                )
                .unique(
                    subset=["PNR", "INDEX_DATE", "parent_pnr", "gender"],
                    keep="first",
                )
            )

            panel_lf = panel_lf.join(
                edu_long_lf,
                on=["PNR", "INDEX_DATE", "parent_pnr", "gender"],
                how="left",
            )

    keep_cols = [
        "PNR",
        "INDEX_DATE",
        "parent_pnr",
        "gender",
        "year",
        "event_time",
        "first.treat",
        "treated",
    ] + income_vars
    if akm_registry_pattern is not None:
        keep_cols.append("socio13_cat")
    if bef_registry_pattern is not None:
        keep_cols.append("cohab_status")
        keep_cols.append("child_ethnicity")
    if uddf_file_path is not None:
        keep_cols.append("education_level")

    # Select only available columns to avoid failures when optional covariates are absent
    available = set(panel_lf.schema)
    panel_lf = panel_lf.select([c for c in keep_cols if c in available])
    # Optional: compress common string columns into categoricals to reduce memory
    cat_cols = [
        c
        for c in [
            "gender",
            "socio13_cat",
            "cohab_status",
            "child_ethnicity",
            "education_level",
        ]
        if c in available
    ]
    if cat_cols:
        panel_lf = panel_lf.with_columns(
            [pl.col(c).cast(pl.Categorical) for c in cat_cols]
        )
    # Final deduplication guard to prevent any residual fanouts
    panel_lf = panel_lf.unique(
        subset=["PNR", "INDEX_DATE", "parent_pnr", "gender", "year", "event_time"],
        keep="first",
    )
    return panel_lf.collect()


def extract_temporal_data_batched(
    df: pl.DataFrame,
    batch_size: int,
    identifier_col: str,
    index_date_col: str,
    registry_path_pattern: str,
    variable_col: str,
    temporal_range: Tuple[int, int] = (-1, 1),
    additional_cols: list[str] | None = None,
    use_cache: bool = True,
) -> pl.DataFrame:
    """
    Extract temporal data in batches for memory-efficient processing of large datasets.

    This function processes large input DataFrames in smaller batches to manage memory
    usage while maintaining high performance through the Rust implementation.

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe with identifiers and index dates
    batch_size : int
        Number of rows to process per batch (e.g., 5000, 10000)
    identifier_col : str
        Column name for unique identifiers
    index_date_col : str
        Column name for index dates
    registry_path_pattern : str
        Path pattern for registry files (supports globbing)
    variable_col : str
        Column name for the main variable to extract from registry
    temporal_range : Tuple[int, int], default=(-1, 1)
        Range of years relative to index year (start_offset, end_offset)
    additional_cols : list[str] | None, default=None
        Additional columns to extract from registry files
    use_cache : bool, default=True
        Whether to cache registry files (highly recommended for batched processing)

    Returns
    -------
    pl.DataFrame
        Combined results from all batches with same structure as extract_temporal_data()

    Examples
    --------
    Process a large cohort in batches:

    >>> large_cohort = pl.read_parquet("large_cohort.parquet")  # 100,000+ rows
    >>> temporal_data = extract_temporal_data_batched(
    ...     df=large_cohort,
    ...     batch_size=5000,
    ...     identifier_col="PNR",
    ...     index_date_col="index_date",
    ...     registry_path_pattern="/data/registry_*.parquet",
    ...     variable_col="CODE",
    ...     temporal_range=(-1, 1),
    ...     use_cache=True  # Important for batched processing
    ... )

    Notes
    -----
    - Registry files are cached across batches when use_cache=True
    - Batch size should be chosen based on available memory
    - Smaller batches reduce memory usage but may increase processing time
    - Results are identical to non-batched processing
    """
    return _extract_temporal_batched_rust(
        df,
        batch_size,
        identifier_col,
        index_date_col,
        registry_path_pattern,
        variable_col,
        temporal_range,
        additional_cols,
        use_cache,
    )


def extract_highest_education_level(
    df: pl.DataFrame,
    identifier_col: str,
    index_date_col: str,
    uddf_file_path: str,
) -> pl.DataFrame:
    """
    Extract highest attained education level from UDDF register data.

    This function processes UDDF (education) register data to determine the highest
    education level achieved by each individual at their index date, accounting for
    temporal validity of education records.

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe with identifiers and index dates
    identifier_col : str
        Column name for unique identifiers (e.g., "PNR")
    index_date_col : str
        Column name for index dates (e.g., "diagnosis_date", "index_date")
    uddf_file_path : str
        Path to the UDDF register file (.parquet, .ipc, .feather, or .arrow)
        Must contain columns: identifier, HFAUDD, HF_VFRA, HF_VTIL

    Returns
    -------
    pl.DataFrame
        Original dataframe with added 'highest_education_level' column containing:
        - "short": Primary & lower secondary education (HFAUDD codes 10, 15)
        - "medium": Upper secondary & vocational education (HFAUDD codes 20, 30, 35)
        - "long": Tertiary education (HFAUDD codes 40, 50, 60, 70, 80)
        - "unknown": Missing or unclassified education (HFAUDD code 90)

    Notes
    -----
    Education Level Categorization (based on HFAUDD codes):
    - **Short education (10, 15)**: Primary & lower secondary, preparatory education
    - **Medium education (20, 30, 35)**: General upper secondary, vocational training
    - **Long education (40, 50, 60, 70, 80)**: Academy, bachelor's, master's, PhD programs
    - **Unknown (90)**: Missing, unclassified, or born ≤1920

    Temporal Validity:
    - Only education records valid at the index date are considered
    - Validity determined by: HF_VFRA ≤ index_date ≤ HF_VTIL
    - Missing HF_VFRA/HF_VTIL dates are treated as always valid

    Highest Level Selection:
    - Among temporally valid records, selects the highest education level
    - Excludes unknown/missing records (HFAUDD code 90) from ranking
    - If no valid education records exist, returns "unknown"

    Examples
    --------
    Extract education levels for a cohort at diagnosis:

    >>> cases_df = pl.DataFrame({
    ...     "PNR": ["123456789", "987654321"],
    ...     "diagnosis_date": ["2020-05-15", "2021-08-20"]
    ... })
    >>> education_df = extract_highest_education_level(
    ...     df=cases_df,
    ...     identifier_col="PNR",
    ...     index_date_col="diagnosis_date",
    ...     uddf_file_path="/data/registers/uddf_2021.parquet"
    ... )
    >>> print(education_df)
    │ PNR       │ diagnosis_date │ highest_education_level │
    │ str       │ date           │ str                     │
    ├───────────┼────────────────┼─────────────────────────┤
    │ 123456789 │ 2020-05-15     │ long                    │
    │ 987654321 │ 2021-08-20     │ medium                  │

    The function uses compile-time embedded HFAUDD categorization mapping for efficiency
    and processes ~5,370 different education codes automatically.
    """
    return _extract_education_rust(
        df,
        identifier_col,
        index_date_col,
        uddf_file_path,
    )


def extract_highest_education_level_batched(
    df: pl.DataFrame,
    batch_size: int,
    identifier_col: str,
    index_date_col: str,
    uddf_file_path: str,
) -> pl.DataFrame:
    """
    Extract highest education levels in batches for memory-efficient processing.

    This function processes large input DataFrames in smaller batches to manage memory
    usage while maintaining the same functionality as extract_highest_education_level.

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe with identifiers and index dates
    batch_size : int
        Number of rows to process per batch (e.g., 5000, 10000)
    identifier_col : str
        Column name for unique identifiers
    index_date_col : str
        Column name for index dates
    uddf_file_path : str
        Path to the UDDF register file

    Returns
    -------
    pl.DataFrame
        Combined results from all batches with same structure as extract_highest_education_level()

    Examples
    --------
    Process a large cohort in batches:

    >>> large_cohort = pl.read_parquet("large_cohort.parquet")  # 100,000+ rows
    >>> education_levels = extract_highest_education_level_batched(
    ...     df=large_cohort,
    ...     batch_size=10000,
    ...     identifier_col="PNR",
    ...     index_date_col="index_date",
    ...     uddf_file_path="/data/uddf_register.parquet"
    ... )

    Notes
    -----
    - Batch size should be chosen based on available memory
    - Smaller batches reduce memory usage but may increase processing time
    - Results are identical to non-batched processing
    - UDDF register file is loaded once per batch for efficiency
    """
    return _extract_education_batched_rust(
        df,
        batch_size,
        identifier_col,
        index_date_col,
        uddf_file_path,
    )


def extract_ethnicity_categories(
    df: pl.DataFrame,
    identifier_col: str,
    index_date_col: str,
    bef_registry_pattern: str,
    temporal_range: tuple[int, int] = (-1, 1),
) -> pl.DataFrame:
    """
    Extract SEPLINE-compliant ethnicity categories from BEF with parental lookups.

    For each individual/year window around the index date, this function:
    - Looks up the child's BEF row to get `OPR_LAND`, `IE_TYPE`, and parent CPRs
    - Looks up the mother's/father's BEF rows (by CPR) for the same `ARET` to get their `OPR_LAND`
    - Maps `OPR_LAND` to Danish/Western/Non-Western categories via compiled mapping
    - Applies SEPLINE rules using parent origins and `IE_TYPE`

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe with identifiers and index dates
    identifier_col : str
        Column name for identifiers (CPR/PNR)
    index_date_col : str
        Column name for index dates
    bef_registry_pattern : str
        Glob pattern to BEF files (e.g., "/data/bef_*.parquet")
    temporal_range : tuple[int, int], default (-1, 1)
        Year offsets around index year to search (inclusive)

    Returns
    -------
    pl.DataFrame
        Columns: identifier_col, index_date_col, ARET, RELATIVE_YEAR, ethnicity_category
    """
    return _extract_ethnicity_rust(
        df,
        identifier_col,
        index_date_col,
        bef_registry_pattern,
        temporal_range,
    )


def compute_att_gt(df: pl.DataFrame, config: dict | str) -> pl.DataFrame:
    """
    Compute ATT(g,t) using did-core on a Polars DataFrame.

    Parameters
    ----------
    df : pl.DataFrame
        Input data with columns matching did-core configuration
    config : dict | str
        JSON config or dict serializable to did-core's DidConfig

    Returns
    -------
    pl.DataFrame
        Columns: group, time, att, se, t_stat, p_value, conf_low, conf_high
    """
    cfg_json = config if isinstance(config, str) else json.dumps(config)
    return _did_att_gt_rust(df, cfg_json)


def get_panel_info(df: pl.DataFrame, config: dict | str) -> pl.DataFrame:
    """
    Return panel diagnostics based on did-core preprocessing.

    Returns columns: panel_type, is_balanced, n_periods
    """
    cfg_json = config if isinstance(config, str) else json.dumps(config)
    return _did_panel_info_rust(df, cfg_json)


def aggregate_effects(
    df: pl.DataFrame,
    config: dict | str,
    kind: str = "simple",
    confidence: float = 0.95,
    uniform_bands: bool = False,
) -> pl.DataFrame:
    """
    Aggregate ATT(g,t) from did-core using the original DataFrame and config.

    Parameters
    ----------
    df : pl.DataFrame
        Input data with columns matching did-core configuration.
    config : dict | str
        JSON config or dict serializable to did-core's DidConfig.
    kind : str
        One of: "simple", "group", "dynamic" (aka "event"), "calendar".
    confidence : float
        Confidence level for bands (e.g., 0.95).
    uniform_bands : bool
        Use uniform bands where supported.

    Returns
    -------
    pl.DataFrame
        Columns: group, time, event_time, att, se, conf_low, conf_high, is_overall
    """
    cfg_json = config if isinstance(config, str) else json.dumps(config)
    return _did_aggregate_rust(df, cfg_json, kind, confidence, uniform_bands)
