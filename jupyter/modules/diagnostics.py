import pandas as pd


def log_shape(df: pd.DataFrame, label: str = "") -> None:
    """Print row count and unique student count (id x year)."""
    n_rows = len(df)
    n_students = (
        len(df[["id", "year"]].drop_duplicates()) if {"id", "year"}.issubset(df.columns) else "n/a"
    )
    prefix = f"[{label}] " if label else ""
    print(f"{prefix}Rows: {n_rows}, Unique students: {n_students}")


def log_nulls(df: pd.DataFrame) -> None:
    """Print null counts for columns that have any nulls."""
    null_counts = df.isnull().sum()
    null_counts = null_counts[null_counts > 0]
    if null_counts.empty:
        print("No nulls.")
    else:
        print(null_counts.to_string())
