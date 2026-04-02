from pathlib import Path

import pandas as pd

from modules.constants import (
    COLUMN_RENAME_MAP,
    ZERO_FILL_COLS_CONCURRENT,
    ZERO_FILL_COLS_FOLLOWING,
)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase column names and rename via COLUMN_RENAME_MAP, keeping only known columns."""
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns=COLUMN_RENAME_MAP)
    known = set(COLUMN_RENAME_MAP.values()) | {"id", "year"}
    return df[[c for c in df.columns if c in known]]


def load_precourse_gpa(data_dir: str) -> pd.DataFrame:
    """Load and stack FA18/FA19 pre-course GPA files. Returns id, year, term_pregpa, prev_cumgpa."""
    data_dir = Path(data_dir)
    dfd = pd.read_excel(data_dir / "Econ-Goodman-Su20-Pre Course GPA-FA18.xlsx")
    dfd = pd.concat(
        [dfd, pd.read_excel(data_dir / "Econ-Goodman-Su20-Pre Course GPA-FA19.xlsx")],
        axis=0,
    )
    dfd.columns = [x.lower() for x in dfd.columns]
    dfd = standardize_columns(dfd)
    dfd.loc[dfd["term"] == "FA18", "year"] = 2018
    dfd.loc[dfd["term"] == "FA19", "year"] = 2019
    dfd = dfd[["id", "year", "term_pregpa", "prev_cumgpa"]]
    return dfd


def load_student_demographics(data_dir: str) -> pd.DataFrame:
    """Load student-level demographics. Returns id, year, ethnicity, gender (m/f/u), transfer (0/1), apptype."""
    data_dir = Path(data_dir)
    df = pd.read_excel(data_dir / "Econ-Goodman-Su20-Student-level.xlsx")
    df.rename(str.lower, axis=1, inplace=True)
    df = standardize_columns(df)
    import numpy as np

    df["transfer"] = np.array(df["apptype"] == "Transfer Student", dtype="int")
    df.loc[df["gender"] == "Men (Cis & Trans)", "gender"] = "m"
    df.loc[df["gender"] == "Women (Cis & Trans)", "gender"] = "f"
    df.loc[df["gender"] == "Data Unavailable", "gender"] = "u"
    df = df[["id", "year", "ethnicity", "gender", "transfer", "apptype"]]
    return df


def load_quarter_gpa(data_dir: str, term: str) -> pd.DataFrame:
    """Load student-quarter-level GPA/units for concurrent (FA18/FA19) or following (WI19/WI20) term.
    Pivots wide and applies appropriate zero-fills. term must be 'concurrent' or 'following'."""
    if term not in ("concurrent", "following"):
        raise ValueError("term must be 'concurrent' or 'following'")

    data_dir = Path(data_dir)
    df = pd.read_excel(data_dir / "Econ-Goodman-Su20-Student-quarter-level_FA18-W.xlsx")
    df.columns = [x.lower() for x in df.columns]
    df = standardize_columns(df)

    df2 = pd.read_excel(data_dir / "Econ-Goodman-Su20-Student-quarter-level_FA19-W.xlsx")
    df2.columns = [x.lower() for x in df2.columns]
    df2 = standardize_columns(df2)

    df = pd.concat([df, df2], axis=0)

    if term == "concurrent":
        term_filter = ["FA18", "FA19"]
        zero_fill_cols = ZERO_FILL_COLS_CONCURRENT
    else:
        term_filter = ["WI19", "WI20"]
        zero_fill_cols = ZERO_FILL_COLS_FOLLOWING

    df = df.loc[df["term_courses"].isin(term_filter)]
    df = df[["id", "year", "measure", "values"]]

    # reshape wide
    df = df.pivot_table(index=["id", "year"], columns="measure", values="values").reset_index()
    df = standardize_columns(df)

    # apply zero-fills
    for x in zero_fill_cols:
        if x in df.columns:
            df.loc[df[x].isnull(), x] = 0

    return df


def load_treatment_outcomes(data_dir: str) -> pd.DataFrame:
    """Load de-identified treatment/outcome data, rename DeID→id, deduplicate."""
    data_dir = Path(data_dir)
    df = pd.read_excel(data_dir / "DeID_all_pid-year-level_data with description.xlsx")
    df.rename(columns={"DeID": "id"}, inplace=True)
    df["id"] = df["id"].astype(str)
    df = df.drop_duplicates()
    return df


def load_video_data(data_dir: str, course: str = "100a") -> pd.DataFrame:
    """Load video-level data for 100a or 100b.
    - Parses first.view/last.view as datetime → firstview/lastview
    - Computes duration = minutes*60 + seconds (in seconds)
    - For 100b: merges video_lengths.xlsx to get duration
    - Drops raw/unnecessary columns
    - Renames DeID → id
    """
    data_dir = Path(data_dir)

    if course == "100a":
        dfv = pd.read_csv(data_dir / "DeID_video-level_data.csv")
        dfv = dfv.loc[dfv["videoid"].notnull()]
        dfv.loc[dfv["syllabus_week"].isnull(), "syllabus_week"] = -1

        # int columns (columns 7 through second-to-last)
        for v in dfv.columns[7:-1]:
            dfv[v] = dfv[v].apply(lambda x: int(x))

        # date columns
        dfv["lastview"] = pd.to_datetime(dfv["last.view"])
        dfv["firstview"] = pd.to_datetime(dfv["first.view"])

        # compute duration in seconds
        dfv["duration"] = dfv["minutes"] * 60 + dfv["seconds"]

        # drop unnecessary columns
        dfv.drop(["first.view", "last.view", "videocode", "length_mins"], axis=1, inplace=True)

        # rename id column
        dfv.rename(columns={"DeID": "id"}, inplace=True)

    elif course == "100b":
        dfv = pd.read_csv(data_dir / "DeID_video-level_data_100b.csv")
        dfv = dfv.loc[dfv["videoid"].notnull()]

        # keep only necessary vars
        dfv = dfv[["DeID", "year", "visit.id", "first.view", "last.view", "videoid"]]

        # merge duration from video_lengths.xlsx
        lengths = pd.read_excel(data_dir / "video_lengths.xlsx")
        lengths = lengths[["videoid", "minutes", "seconds"]]
        lengths["duration"] = lengths["minutes"] * 60 + lengths["seconds"]
        dfv = dfv.merge(lengths[["videoid", "duration"]], on="videoid", how="left")

        # date columns
        dfv["lastview"] = pd.to_datetime(dfv["last.view"])
        dfv["firstview"] = pd.to_datetime(dfv["first.view"])

        # drop raw date columns
        dfv.drop(["first.view", "last.view"], axis=1, inplace=True)

        # rename id column
        dfv.rename(columns={"DeID": "id"}, inplace=True)

    else:
        raise ValueError("course must be '100a' or '100b'")

    return dfv
