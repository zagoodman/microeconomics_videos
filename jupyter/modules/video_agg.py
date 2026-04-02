"""
video_agg.py — Video aggregation helpers for assemble_data pipeline.

Provides functions for adding exam-period flags and aggregating video-level
data to the student and student-week levels.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Function 1: add_exam_period_flags
# ---------------------------------------------------------------------------


def add_exam_period_flags(dfv: pd.DataFrame, exam_dates: dict) -> pd.DataFrame:
    """Add exam-period flag columns to the video-level dataframe.

    Parameters
    ----------
    dfv:
        Video-level dataframe.  Must contain columns: firstview (datetime),
        year (int), incentivized (numeric).
    exam_dates:
        Nested dict mapping year -> {"mid1": datetime, "mid2": datetime,
        "final": datetime}.  See constants.EXAM_DATES.

    Returns
    -------
    Copy of dfv with the following columns added or modified:

    - b4_mid1        : int 0/1 — firstview <= mid1 cutoff for that year
    - b4_mid2        : int 0/1 — firstview <= mid2 cutoff for that year
    - b4_final       : int 0/1 — firstview <= final cutoff for that year
    - incent_counts  : int 0/1 — NOT b4_mid1 AND b4_final AND incentivized>=1
    - incentivized   : rebinarized to int(incentivized >= 1)
    - firstflag      : 1 if this row is the first view of this video by this
                       student-year (min firstview per id/year/videoid group)
    - pre_mid1       : int 0/1 — same as b4_mid1
    - mid1_to_mid2   : int 0/1 — NOT b4_mid1 AND b4_mid2
    - post_mid2      : int 0/1 — NOT b4_mid2 AND b4_final
    """
    dfv = dfv.copy()

    # ------------------------------------------------------------------
    # firstflag: 1 when this row has the minimum firstview for the
    # id/year/videoid group (i.e., first time this student watched this video)
    # ------------------------------------------------------------------
    dfv["firstflag"] = (
        dfv.groupby(["id", "year", "videoid"]).firstview.transform("min") == dfv.firstview
    ).astype(int)

    # ------------------------------------------------------------------
    # Before-exam flags — built from exam_dates dict so the function is
    # not hard-coded to specific years.
    # ------------------------------------------------------------------
    b4_mid1 = pd.Series(False, index=dfv.index)
    b4_mid2 = pd.Series(False, index=dfv.index)
    b4_final = pd.Series(False, index=dfv.index)

    for year, dates in exam_dates.items():
        mask = dfv["year"] == year
        b4_mid1 = b4_mid1 | (mask & (dfv["firstview"] <= dates["mid1"]))
        b4_mid2 = b4_mid2 | (mask & (dfv["firstview"] <= dates["mid2"]))
        b4_final = b4_final | (mask & (dfv["firstview"] <= dates["final"]))

    dfv["b4_mid1"] = b4_mid1.astype(int)
    dfv["b4_mid2"] = b4_mid2.astype(int)
    dfv["b4_final"] = b4_final.astype(int)

    # ------------------------------------------------------------------
    # incent_counts: watched after mid1, before/on final, and incentivized
    # ------------------------------------------------------------------
    dfv["incent_counts"] = np.array(~b4_mid1 & b4_final & (dfv["incentivized"] >= 1), dtype="int")

    # Rebinarize incentivized to 0/1
    dfv["incentivized"] = np.array(dfv["incentivized"] >= 1, dtype="int")

    # ------------------------------------------------------------------
    # Period-category columns used by build_weekly_video_panel
    # If pre_mid1 / mid1_to_mid2 / post_mid2 already exist in the raw
    # data, keep them (they may use a different definition). Only create
    # them when absent.
    # ------------------------------------------------------------------
    if "pre_mid1" not in dfv.columns:
        dfv["pre_mid1"] = dfv["b4_mid1"].astype(int)
    if "mid1_to_mid2" not in dfv.columns:
        dfv["mid1_to_mid2"] = (~b4_mid1 & b4_mid2).astype(int)
    if "post_mid2" not in dfv.columns:
        dfv["post_mid2"] = (~b4_mid2 & b4_final).astype(int)

    return dfv


# ---------------------------------------------------------------------------
# Function 2: aggregate_duration
# ---------------------------------------------------------------------------


def aggregate_duration(
    dfv: pd.DataFrame,
    group_cols: list[str],
    period_flags: list[str] | None = None,
    to_hours: bool = False,
    suffix: str = "",
) -> pd.DataFrame:
    """Aggregate video duration at the student level.

    Returns both total (sum of all rows) and unique (sum of per-video maxima)
    duration, optionally broken out by exam-period flag columns.

    Parameters
    ----------
    dfv:
        Video-level dataframe.  Must contain 'duration' and 'videoid'.
    group_cols:
        Columns to group by (e.g. ['id', 'year']).
    period_flags:
        If provided, a list of binary (0/1) flag column names.  Duration is
        computed separately for each flag.  If None, overall duration is
        computed.
    to_hours:
        If True, divide all duration columns by 3600.
    suffix:
        String appended to every output column name.

    Returns
    -------
    DataFrame with group_cols + duration columns.
    """
    result = dfv[group_cols].drop_duplicates().copy()

    if period_flags is not None:
        # Build flag-multiplied duration columns all at once
        tmp = dfv.copy()
        flag_dur_cols = []
        for f in period_flags:
            col = f"duration_{f}{suffix}"
            tmp[col] = tmp["duration"] * tmp[f]
            flag_dur_cols.append(col)

        # Total: sum per group
        agg_total = tmp.groupby(group_cols)[flag_dur_cols].sum().reset_index()
        result = result.merge(agg_total, on=group_cols, how="left")

        # Unique: max per (group + videoid), then sum per group
        unique_dur_cols = [f"duration_{f}_u{suffix}" for f in period_flags]
        agg_unique = (
            tmp.groupby([*group_cols, "videoid"])[flag_dur_cols]
            .max()
            .reset_index()
            .groupby(group_cols)[flag_dur_cols]
            .sum()
            .reset_index()
        )
        agg_unique.columns = group_cols + unique_dur_cols
        result = result.merge(agg_unique, on=group_cols, how="left")

    else:
        total_col = f"duration{suffix}"
        unique_col = f"duration_u{suffix}"

        # Total: sum per group
        agg_total = dfv.groupby(group_cols)["duration"].sum().reset_index()
        agg_total.columns = [*group_cols, total_col]
        result = result.merge(agg_total, on=group_cols, how="left")

        # Unique: max duration per (group + videoid), then sum per group
        agg_unique = (
            dfv.groupby([*group_cols, "videoid"])["duration"]
            .max()
            .reset_index()
            .groupby(group_cols)["duration"]
            .sum()
            .reset_index()
        )
        agg_unique.columns = [*group_cols, unique_col]
        result = result.merge(agg_unique, on=group_cols, how="left")

    if to_hours:
        dur_cols = [c for c in result.columns if c not in group_cols]
        for c in dur_cols:
            result[c] = result[c] / 3600

    return result


# ---------------------------------------------------------------------------
# Function 3: aggregate_counts
# ---------------------------------------------------------------------------


def aggregate_counts(
    dfv: pd.DataFrame,
    group_cols: list[str],
    count_flags: list[str],
    suffix: str = "",
) -> pd.DataFrame:
    """Aggregate video view counts at the student level.

    For each flag column ``f`` in *count_flags*:

    - total  : sum of ``f`` per group  →  ``videos_{f}{suffix}``
    - unique : nunique of videoid where ``f``==1 per group
               →  ``videos_{f}_u{suffix}``

    Parameters
    ----------
    dfv:
        Video-level dataframe.  Must contain 'videoid' and all columns in
        count_flags.
    group_cols:
        Columns to group by (e.g. ['id', 'year']).
    count_flags:
        List of binary flag column names to aggregate.
    suffix:
        String appended to every output column name.

    Returns
    -------
    DataFrame with group_cols + count columns.
    """
    result = dfv[group_cols].drop_duplicates().copy()

    # Total counts
    total_cols = [f"videos_{f}{suffix}" for f in count_flags]
    agg_total = dfv.groupby(group_cols)[count_flags].sum().reset_index()
    agg_total.columns = group_cols + total_cols
    result = result.merge(agg_total, on=group_cols, how="left")

    # Unique counts — nunique of videoid where flag == 1
    tmp = dfv.copy()
    unique_cols = [f"videos_{f}_u{suffix}" for f in count_flags]
    for f in count_flags:
        tmp[f] = tmp.loc[tmp[f] == 1, "videoid"]

    agg_unique = tmp.groupby(group_cols)[count_flags].nunique().reset_index()
    agg_unique.columns = group_cols + unique_cols
    result = result.merge(agg_unique, on=group_cols, how="left")

    return result


# ---------------------------------------------------------------------------
# Function 4: build_weekly_video_panel
# ---------------------------------------------------------------------------


def build_weekly_video_panel(
    dfv: pd.DataFrame,
    df_arm: pd.DataFrame,
) -> pd.DataFrame:
    """Build a student-week-level panel of video-watching activity.

    Replicates the week-level aggregation logic in assemble_data.ipynb
    (lines ~384-461).

    Parameters
    ----------
    dfv:
        Video-level dataframe.  Must contain: firstview (datetime or NaT),
        relevant_100a, duration, pre_mid1, mid1_to_mid2, post_mid2, id, year.
        arm and finalscore may already be present (they are kept if so).
    df_arm:
        DataFrame with [id, year, arm, finalscore] — used to outer-merge so
        that students who never watched any video are still represented.

    Returns
    -------
    DataFrame indexed at (id, year, weekoy) level with columns:
        id, year, arm, weekoy, finalscore,
        videos, duration, videos_pre_mid1, videos_mid1_to_mid2, videos_post_mid2,
        videosu, durationu, videos_pre_mid1u, videos_mid1_to_mid2u, videos_post_mid2u
    All count/duration columns are int with NaN filled to 0.
    """
    keepvars = ["id", "year", "arm", "finalscore"]

    # ------------------------------------------------------------------
    # Step 1 & 2: weekoy and outer merge to include zero-watching students
    # ------------------------------------------------------------------
    dfv = dfv.copy()

    # Drop arm/finalscore if already present (they were merged onto dfv
    # earlier for aggregation; the authoritative source is df_arm).
    for col in ["arm", "finalscore"]:
        if col in dfv.columns:
            dfv = dfv.drop(columns=[col])

    # weekoy: ISO week number minus 43 so week 0 = experiment start week
    dfv["weekoy"] = (
        dfv.loc[dfv["firstview"].notnull(), "firstview"].apply(lambda x: x.isocalendar()[1]) - 43
    )

    # Outer merge — students with no video watching come from df_arm
    dfv = dfv.merge(df_arm[keepvars], on=["id", "year"], how="outer")

    # ------------------------------------------------------------------
    # Step 3 & 4: full cross-product index of (id, year, weekoy)
    # ------------------------------------------------------------------
    mergevars = ["id", "year", "arm", "weekoy"]

    all_weeks = dfv.loc[dfv["weekoy"].notnull(), "weekoy"].unique()
    muidx = pd.MultiIndex.from_product(
        [
            dfv["id"].drop_duplicates(),
            dfv["year"].drop_duplicates(),
            all_weeks,
        ]
    )
    dfdw = pd.DataFrame(index=muidx).reset_index()
    dfdw.columns = ["id", "year", "weekoy"]

    # Merge arm and finalscore onto the full index (inner so only valid id/year pairs)
    dfdw = dfdw.merge(
        dfv[["id", "year", "arm", "finalscore"]].drop_duplicates(),
        on=["id", "year"],
        how="inner",
    )
    dfdw.sort_values(mergevars, inplace=True)

    # ------------------------------------------------------------------
    # Step 5: filter to relevant_100a == 1 videos only
    # ------------------------------------------------------------------
    dfr = dfv.loc[dfv["relevant_100a"] == 1].copy()

    # ------------------------------------------------------------------
    # Step 6: aggregate total videos, duration, and period-category counts
    # ------------------------------------------------------------------
    period_cols = ["pre_mid1", "mid1_to_mid2", "post_mid2"]
    agg_cols = ["relevant_100a", "duration", *period_cols]

    dfaggw = dfr.groupby(mergevars)[agg_cols].sum().reset_index()
    dfaggw.columns = [
        *mergevars,
        "videos",
        "duration",
        "videos_pre_mid1",
        "videos_mid1_to_mid2",
        "videos_post_mid2",
    ]
    dfdw = dfdw.merge(dfaggw, on=mergevars, how="left")

    # ------------------------------------------------------------------
    # Step 7: unique (first-time-watched) versions
    # ------------------------------------------------------------------
    dfaggwd = dfr.sort_values(["id", "year", "firstview"]).drop_duplicates(
        ["id", "year", "arm", "videoid"]
    )
    dfaggwd = dfaggwd.groupby(mergevars)[agg_cols].sum().reset_index()
    dfaggwd.columns = [
        *mergevars,
        "videosu",
        "durationu",
        "videos_pre_mid1u",
        "videos_mid1_to_mid2u",
        "videos_post_mid2u",
    ]
    dfdw = dfdw.merge(dfaggwd, on=mergevars, how="left")

    # ------------------------------------------------------------------
    # Step 8: fill NaN → 0 and cast to int for all count/duration columns
    # ------------------------------------------------------------------
    value_cols = dfdw.columns[5:]  # everything after id, year, arm, weekoy, finalscore
    for c in value_cols:
        dfdw[c] = dfdw[c].apply(lambda x: int(x) if x == x else 0)

    return dfdw
