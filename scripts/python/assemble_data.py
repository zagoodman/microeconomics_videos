from pathlib import Path

import numpy as np

from modules.constants import (
    EXAM_DATES,
    MERGE_KEYS,
    ZERO_FILL_COLS_CONCURRENT,
    ZERO_FILL_COLS_FOLLOWING,
)
from modules.diagnostics import log_nulls, log_shape
from modules.loaders import (
    load_precourse_gpa,
    load_quarter_gpa,
    load_student_demographics,
    load_treatment_outcomes,
    load_video_data,
)
from modules.video_agg import (
    add_credit_flag,
    add_exam_period_flags,
    aggregate_counts,
    aggregate_duration,
    build_weekly_video_panel,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = str(ROOT / "data" / "raw")
DATA_GEN = str(ROOT / "data" / "generated")

# --- Demographics ---

df_dem = load_student_demographics(DATA_RAW).merge(
    load_precourse_gpa(DATA_RAW), on=MERGE_KEYS, how="outer"
)

df_dem_concurrent = df_dem.merge(
    load_quarter_gpa(DATA_RAW, term="concurrent"), on=MERGE_KEYS, how="outer"
)
for c in ZERO_FILL_COLS_CONCURRENT:
    if c in df_dem_concurrent.columns:
        df_dem_concurrent[c] = df_dem_concurrent[c].fillna(0)

df_dem_following = df_dem.merge(
    load_quarter_gpa(DATA_RAW, term="following"), on=MERGE_KEYS, how="outer"
)
for c in ZERO_FILL_COLS_FOLLOWING:
    if c in df_dem_following.columns:
        df_dem_following[c] = df_dem_following[c].fillna(0)

log_shape(df_dem_concurrent, "dem_concurrent")
log_nulls(df_dem_concurrent)

df_dem_concurrent.to_csv(f"{DATA_GEN}/student_demographics_fall.csv", index=False)
df_dem_following.to_csv(f"{DATA_GEN}/student_demographics_winter.csv", index=False)

# --- Treatment outcomes (df_main base) ---

df_main = load_treatment_outcomes(DATA_RAW)
df_main["arm"] = df_main["toberandomized"] + df_main["treated"]
# Zero-fill attendance columns (missing = did not attend)
for c in [f"attend{i}" for i in range(1, 8)]:
    if c in df_main.columns:
        df_main[c] = df_main[c].fillna(0)
log_shape(df_main, "treatment_outcomes")
log_nulls(df_main)

# --- 100A video aggregates ---

dfv = load_video_data(DATA_RAW, course="100a")
dfv = add_exam_period_flags(dfv, EXAM_DATES)

# Merge arm and finalscore onto dfv so build_weekly_video_panel can use them
dfv = dfv.merge(df_main[[*MERGE_KEYS, "arm", "finalscore"]], on=MERGE_KEYS, how="left")

# Exploratory info
dftmp = dfv[["syllabus_week", "incentivized", "videoid"]].drop_duplicates()
print(f"Relevant videos: {dftmp.syllabus_week.notnull().sum()}")
print(f"Incentivized videos: {(dftmp.incentivized > 0).sum()}")
print("\nRelevant videos by syllabus week:")
print(dftmp.syllabus_week.value_counts().sort_index())
print("\nStudents per year:")
print(dfv[["id", "year"]].drop_duplicates().year.value_counts())

# Relevant-only for aggregation
dfr = dfv.query("relevant_100a > 0").copy()
print(
    f"Irrelevant videos: {(dfv.relevant_100a == 0).sum()} ({(dfv.relevant_100a == 0).mean():.1%})"
)

# Duration aggregates
dur_100a = aggregate_duration(
    dfr,
    MERGE_KEYS,
    period_flags=["b4_mid1", "b4_mid2", "b4_final"],
    to_hours=True,
).rename(
    columns={
        "duration_b4_mid1": "duration_mid1",
        "duration_b4_mid1_u": "duration_mid1_u",
        "duration_b4_mid2": "duration_mid2",
        "duration_b4_mid2_u": "duration_mid2_u",
        "duration_b4_final": "duration_final",
        "duration_b4_final_u": "duration_final_u",
    }
)

# Count aggregates
cnt_100a = aggregate_counts(
    dfr,
    MERGE_KEYS,
    count_flags=["b4_mid1", "b4_mid2", "b4_final", "incentivized", "incent_counts"],
).rename(
    columns={
        "videos_b4_mid1": "videos_mid1",
        "videos_b4_mid1_u": "videos_mid1_u",
        "videos_b4_mid2": "videos_mid2",
        "videos_b4_mid2_u": "videos_mid2_u",
        "videos_b4_final": "videos_final",
        "videos_b4_final_u": "videos_final_u",
    }
)

video_agg_100a = dur_100a.merge(cnt_100a, on=MERGE_KEYS)
df_main = df_main.merge(video_agg_100a, on=MERGE_KEYS, how="left")

# Fill zeros for students with no video watching
for c in video_agg_100a.columns[2:]:
    df_main[c] = df_main[c].fillna(0)
# Cast count cols to int
for c in cnt_100a.columns[2:]:
    df_main[c] = df_main[c].astype(int)

log_shape(df_main, "after 100a merge")

# --- 100A video aggregates restricted to credit-eligible opens (referee point 4) ---
# A video open earns credit only if the student did not open another video before this one
# could have been watched in full at 2x speed (see modules.video_agg.add_credit_flag). Applied to all arms.

dfv = add_credit_flag(dfv)
print(f"Share of all opens earning credit: {dfv.credit.mean():.3f}")
print("\nShare of relevant opens earning credit, by arm and period:")
_tmp = dfv.query("relevant_100a > 0").copy()
_tmp["period"] = np.select(
    [_tmp.b4_mid1 == 1, _tmp.b4_mid2 == 1, _tmp.b4_final == 1],
    ["pre_mid1", "mid1_to_mid2", "mid2_to_final"],
    "after_final",
)
print(_tmp.groupby(["arm", "period"]).credit.mean().unstack().round(3))

dfr_cr = dfv.query("relevant_100a > 0").copy()
cr_flags = []
for f in ["b4_mid1", "b4_mid2", "b4_final"]:
    dfr_cr[f"{f}_cr"] = dfr_cr[f] * dfr_cr["credit"]
    cr_flags.append(f"{f}_cr")

cr_rename = {}
for e in ["mid1", "mid2", "final"]:
    cr_rename[f"duration_b4_{e}_cr"] = f"duration_{e}_cr"
    cr_rename[f"duration_b4_{e}_cr_u"] = f"duration_{e}_cr_u"
    cr_rename[f"videos_b4_{e}_cr"] = f"videos_{e}_cr"
    cr_rename[f"videos_b4_{e}_cr_u"] = f"videos_{e}_cr_u"

dur_cr = aggregate_duration(dfr_cr, MERGE_KEYS, period_flags=cr_flags, to_hours=True)
cnt_cr = aggregate_counts(dfr_cr, MERGE_KEYS, count_flags=cr_flags)
video_agg_cr = dur_cr.merge(cnt_cr, on=MERGE_KEYS).rename(columns=cr_rename)
df_main = df_main.merge(video_agg_cr, on=MERGE_KEYS, how="left")
for c in video_agg_cr.columns[2:]:
    df_main[c] = df_main[c].fillna(0)
for c in [c for c in video_agg_cr.columns[2:] if c.startswith("videos_")]:
    df_main[c] = df_main[c].astype(int)

print("\nMean video measures (all opens vs credit-eligible), randomized students:")
_cols = ["videos_mid2_u", "videos_mid2_cr_u", "videos_final_u", "videos_final_cr_u"]
print(df_main.loc[df_main.arm > 0].groupby("arm")[_cols].mean().round(2))
log_shape(df_main, "after credit merge")

# --- 100B video aggregates ---

dfv_b = load_video_data(DATA_RAW, course="100b")

# Drop stale 100B video columns from the raw treatment file before merging new aggregates
drop_100b = [
    "videos_b",
    "relevant_b",
    "videos_u_b",
    "relevant_u_b",
    "duration_all_b",
    "duration_rel_b",
    "duration_u_b",
]
df_main = df_main.drop(columns=[c for c in drop_100b if c in df_main.columns])

# Duration: aggregate_duration with no period_flags produces duration{suffix} and duration_u{suffix}
# suffix="_b" -> columns: duration_b, duration_u_b
dur_100b = aggregate_duration(dfv_b, MERGE_KEYS, to_hours=True, suffix="_b")
# Rename duration_u_b -> duration_b_u to match expected column names
dur_100b = dur_100b.rename(columns={"duration_u_b": "duration_b_u"})

# Counts: add cnt=1, use aggregate_counts with suffix="_b"
# produces videos_cnt_b and videos_cnt_u_b; rename to videos_b and videos_b_u
dfv_b_cnt = dfv_b.copy()
dfv_b_cnt["cnt"] = 1
cnt_100b = aggregate_counts(dfv_b_cnt, MERGE_KEYS, count_flags=["cnt"], suffix="_b")
cnt_100b = cnt_100b.rename(columns={"videos_cnt_b": "videos_b", "videos_cnt_u_b": "videos_b_u"})

video_agg_100b = dur_100b.merge(cnt_100b, on=MERGE_KEYS)
df_main = df_main.merge(video_agg_100b, on=MERGE_KEYS, how="left")
for c in dur_100b.columns[2:]:
    df_main[c] = df_main[c].fillna(0)
for c in cnt_100b.columns[2:]:
    df_main[c] = df_main[c].fillna(0).astype(int)

log_shape(df_main, "after 100b merge")

# --- Export df_main ---

# Drop stale columns carried over from raw treatment file before export
# arm is excluded from the CSV but retained in df_main for the weekly panel
drop_stale = [
    "arm",
    "relevant",
    "relevant_u",
    "videos",
    "videos_u",
    "duration_all",
    "duration_rel",
    "duration_u",
    "videos_b4_mid1_rel",
    "videos_b4_mid1_relu",
    "videos_b4_mid2_rel",
    "videos_b4_mid2_relu",
]
export_cols = [c for c in df_main.columns if c not in drop_stale]
df_main[export_cols].to_csv(f"{DATA_GEN}/student_analysis_sample.csv", index=False)
log_shape(df_main, "student_analysis_sample")
log_nulls(df_main)
df_main.head()

# --- Weekly video panel ---

df_arm = df_main[[*MERGE_KEYS, "arm", "finalscore"]].copy()
df_weekly = build_weekly_video_panel(dfv, df_arm)

print(df_weekly.isnull().sum())
print(len(df_weekly.loc[df_weekly.finalscore.isnull()].id.value_counts()))

df_weekly.to_csv(f"{DATA_GEN}/weekly_video_panel.csv", index=False)
