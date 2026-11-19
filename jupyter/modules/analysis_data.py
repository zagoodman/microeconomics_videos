"""
analysis_data.py — Python port of the Stata data-prep programs in analyze_data.ipynb
(clean_data, get_std_units, merge_dem, clean_dem). Used by referee_analysis.ipynb so the
Python estimates are computed on exactly the sample and variable definitions Stata uses.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Mirrors the Stata global $ctrl_vars (PDS candidate controls).
CTRL_VARS = [
    "mathquizstd",
    "mathquiz_unobs",
    "videos_mid1_u",
    "duration_mid1_u",
    "pset_pre",
    "transfer",
    "prev_cumgpa",
    "prev_cumgpa_unobs",
    "female",
    "asian",
    "latx",
    "white",
]

ARM_LABELS = {0: "Above median", 1: "Control", 2: "Incentive"}


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Port of Stata `clean_data`."""
    df = df.copy()
    df["arm"] = df["treated"] + df["toberandomized"]
    df = df.drop(columns=["toberandomized"])
    df = df.loc[df["mid1score"].notnull()].copy()
    df["y2019"] = (df["year"] == 2019).astype(int)
    df["pairyear"] = df["year"] * 1000 + df["pair"]
    for v, name in [
        ("assigned_grade", "bothpairs_assigned_grade"),
        ("mid2score", "bothpairs_mid2"),
        ("finalscore", "bothpairs_final"),
    ]:
        obs = df[v].notnull().astype(int)
        df[name] = (obs.groupby([df["pair"], df["year"]]).transform("sum") >= 2).astype(int)
    df["mathquiz_unobs"] = df["mathquiz"].isnull().astype(int)
    df["mathquiz"] = df["mathquiz"].fillna(0)
    return df


def get_std_units(df: pd.DataFrame) -> pd.DataFrame:
    """Port of Stata `get_std_units`: scores in Control-arm SD units, by year."""
    df = df.copy()
    df["mid1scorestd"] = np.nan
    for y in (2018, 2019):
        m = df["year"] == y
        maxscore = df.loc[m & (df["arm"] >= 1), "mid1score"].max()
        sd = df.loc[m & (df["arm"] == 1), "mid1score"].std()
        df.loc[m, "mid1scorestd"] = (df.loc[m, "mid1score"] - maxscore) / sd
    for v in ["mathquiz", "mid2score", "finalscore", "mid1_100b", "mid2_100b", "final_100b"]:
        if v not in df.columns:
            continue
        df[f"{v}std"] = np.nan
        for y in (2018, 2019):
            m = df["year"] == y
            ctrl = df.loc[m & (df["arm"] == 1), v]
            df.loc[m, f"{v}std"] = (df.loc[m, v] - ctrl.mean()) / ctrl.std()
    return df


def merge_dem(df: pd.DataFrame, dem: pd.DataFrame) -> pd.DataFrame:
    """Port of Stata `merge_dem` (1:1 merge on id, year; keeps all rows like Stata)."""
    return df.merge(dem, on=["id", "year"], how="outer", suffixes=("", "_dem"))


def clean_dem(df: pd.DataFrame) -> pd.DataFrame:
    """Port of the parts of Stata `clean_dem` needed for controls."""
    df = df.copy()
    df["male"] = (df["gender"] == "m").astype(int)
    df["female"] = (df["gender"] == "f").astype(int)
    eth = df["ethnicity"]
    chinese = eth == "Chinese/Chinese-American"
    oasian = eth == "All Other Asian/Asian-American"
    viet = eth == "Vietnamese"
    df["latx"] = (eth == "Chicanx/Latinx").astype(int)
    df["white"] = (eth == "White/Caucasian").astype(int)
    df["asian"] = (chinese | oasian | viet).astype(int)
    df["prev_cumgpa_unobs"] = df["prev_cumgpa"].isnull().astype(int)
    df["prev_cumgpa"] = df["prev_cumgpa"].fillna(0)
    return df


def load_analysis_frame(data_gen: str) -> pd.DataFrame:
    """Equivalent of Stata: get_idyearlevel; get_std_units; merge_dem; clean_dem."""
    df = pd.read_csv(f"{data_gen}/student_analysis_sample.csv", dtype={"id": str})
    df = clean_data(df)
    df = get_std_units(df)
    dem = pd.read_csv(f"{data_gen}/student_demographics_fall.csv", dtype={"id": str})
    df = merge_dem(df, dem)
    df = clean_dem(df)
    # rows that came only from the demographics file have no arm; Stata keeps them but
    # every analysis conditions on arm, so drop them here.
    return df.loc[df["arm"].notnull()].copy()
