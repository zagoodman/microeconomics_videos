"""
Utility functions for assembling LaTeX tables in assemble_tables.ipynb.
"""
import re

import numpy as np
import pandas as pd
from scipy.stats import t


def add_stars(df, beta_col="1beta", stderr_col="2stderr"):
    """
    Adds a 'stars' column to df based on z-critical thresholds (1.645/1.96/2.576).
    Returns df with 'stars' column added (0, 1, 2, or 3).
    """
    df = df.copy()
    df["stars"] = 0
    df.loc[(abs(df[beta_col]) - df[stderr_col] * 1.645) > 0, "stars"] = 1
    df.loc[(abs(df[beta_col]) - df[stderr_col] * 1.96) > 0, "stars"] = 2
    df.loc[(abs(df[beta_col]) - df[stderr_col] * 2.576) > 0, "stars"] = 3
    return df


def stringify_stats(df, roundn, beta_col="1beta", stderr_col="2stderr", mean_col="3mean", n_col="4N"):
    """
    Stringifies beta, stderr, mean, and N columns in place.
    Appends stars to beta. Wraps stderr in parentheses.
    Expects 'stars' column to already exist (call add_stars first).
    """
    df = df.copy()
    df[beta_col] = df[beta_col].apply(lambda x: f"{x:.{roundn}f}") + df["stars"].apply(lambda x: "*" * x)
    df[stderr_col] = df[stderr_col].apply(lambda x: f"({x:.{roundn}f})")
    df[mean_col] = df[mean_col].apply(lambda x: f"{x:.{roundn}f}")
    df[n_col] = df[n_col].apply(lambda x: str(int(x)))
    return df.drop(columns=["stars"])


def convert_to_latex(
    dft,
    column_format,
    caption,
    label,
    note="",
    observations=True,
    longtable=False,
    scalewidth=True,
    stars=True,
    regnote=True,
):
    """
    Takes dataframe dft and spits out tex table given options.

    Arguments
    ---------
    - dft            dataframe ready to become a tex table. Column names are correct.
    - column_format  tabular columns (in tex)
    - caption        title of the table
    - label          tex ref to add to table
    - note           note at the bottom of the table
    - observations   if True, adds a midrule above the observations count
    - longtable      if True, adds longtable environment (default False).
                     Cannot combine longtable and scalewidth.
    - scalewidth     if True, scales the table to fit the tex linewidth
    - stars          if True, wraps * in \\sym{}
    - regnote        if True, appends \\Regnote to note. Ignored if longtable.
    """
    assert isinstance(dft, pd.core.frame.DataFrame)
    for var in [column_format, caption, label, note]:
        assert isinstance(var, str)
    for var in [observations, longtable, scalewidth, stars, regnote]:
        assert isinstance(var, bool)
    assert not (longtable and scalewidth)

    if not longtable:
        t_str = dft.to_latex(index=False, escape=False, column_format=column_format)
        addendum = (
            "\\begin{spacing}{1.0} \n"
            + "\\begin{table} \\centering \\caption{"
            + caption
            + "} \n"
            + "\\label{"
            + label
            + "} \n"
        )
        if scalewidth:
            addendum += "\\resizebox{\\linewidth}{!}{% \n"
        addendum += "\\begin{threeparttable} \n"
        t_str = addendum + t_str

        if regnote:
            addendum = "\\Fignote{" + note + " \\Regnote} \n\\end{threeparttable}"
        else:
            addendum = "\\Fignote{" + note + "} \n\\end{threeparttable}"
        if scalewidth:
            addendum += "}"
        addendum += "\n\\end{table} \n\\end{spacing}"
        t_str = t_str + addendum

    else:
        t_str = dft.to_latex(
            index=False,
            escape=False,
            longtable=True,
            caption=caption,
            label=label,
            column_format=column_format,
        )
        addendum = (
            "\\begin{spacing}{1.0} \n"
            + "\\begin{ThreePartTable} \n"
            + "\\begin{TableNotes} \n"
            + "\\item \\textit{Note}: "
            + note
            + "\n"
            + "\\end{TableNotes} \n"
            + "\\footnotesize \n \\begin{longtable}"
        )
        t_str = t_str.replace("\\begin{longtable}", addendum)
        t_str = t_str.replace("\\endhead", "\\endfirsthead")

        ncols = len(dft.columns)
        startidx = t_str.find("\\endfirsthead")
        addendum = (
            "\\endfirsthead \n"
            + "\\multicolumn{"
            + str(ncols)
            + "}{r}{{Table \\ref{"
            + label
            + "} (continued)}} \\\\"
            + "\n\\toprule \n \\endhead"
        )
        t_str = t_str[:startidx] + addendum + t_str[startidx + 13:]

        startidx = t_str.find("\\endlastfoot")
        t_str = t_str[:startidx] + "\\insertTableNotes \n" + t_str[startidx:]
        t_str += "\n\\end{ThreePartTable} \n\\end{spacing}"

    if stars:
        t_str = t_str.replace("*** ", "\\sym{***} ")
        t_str = t_str.replace("** ", "\\sym{**} ")
        t_str = t_str.replace("* ", "\\sym{*} ")

    if observations:
        idx = [m.start() for m in re.finditer("Observations &", t_str)]
        for pos in idx[::-1]:
            t_str = t_str[:pos] + "\n\\midrule \n" + t_str[pos:]

    return t_str


def combine_notes(notelist):
    """
    Joins a list of note strings with single spaces.
    """
    assert isinstance(notelist, list)
    assert all(isinstance(x, str) for x in notelist)
    assert len(notelist) > 1
    return " ".join(notelist)


def insert_panel(table, colnum, letter, title, var, first=True):
    """
    Inserts a panel header in front of `var` in `table`.

    If `first`, inserts before the first occurrence; otherwise before the last
    (and prepends a \\midrule).
    """
    assert isinstance(colnum, int)
    assert all(isinstance(v, str) for v in [table, letter, title, var])

    if first:
        idx = table.find(var + " &")
        insert = (
            "\n\\multicolumn{"
            + str(colnum)
            + "}{l}"
            + "{\\textbf{Panel "
            + letter
            + "}: "
            + title
            + "} \\\\ \n"
        )
    else:
        idx = table.rfind(var + " &")
        insert = (
            "\n\\midrule \n\\multicolumn{"
            + str(colnum)
            + "}{l}"
            + "{\\textbf{Panel "
            + letter
            + "}: "
            + title
            + "} \\\\ \n"
        )

    assert idx > -1, f"Error: {var} not found in table."
    return table[:idx] + insert + table[idx:]


def add_indents(table, varlist):
    """
    Wraps each variable in varlist with \\customlinespace \\indentrow{} in table.
    """
    assert isinstance(table, str)
    assert isinstance(varlist, list)
    assert all(isinstance(v, str) for v in varlist)

    for v in varlist:
        idx = [m.start() for m in re.finditer(re.escape(v) + " &", table)]
        for i in idx[::-1]:
            if v[0] == "\\":
                i -= 1
            table = table[:i] + "\n\\customlinespace \\indentrow{" + v + "}" + table[i + len(v):]

    return table


def get_p_value(meant, meanc, stderrt, stderrc, Nt, Nc):
    """
    Returns a two-sided p-value using Welch's t-test (pooled df approximation).
    Used for balance table significance tests.
    """
    tcrit = abs(meant - meanc) / np.sqrt(stderrt**2 + stderrc**2)
    d_o_f = Nt + Nc - 2
    return t.sf(tcrit, d_o_f) * 2


def star_p(x):
    """
    Returns p-value as a string with significance stars appended.
    Used for balance table formatting.
    """
    stars = "" if x > 0.1 else "*" if x > 0.05 else "**" if x > 0.01 else "***"
    return f"{x:.3f}{stars}"
