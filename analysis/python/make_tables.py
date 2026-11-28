"""Generate all LaTeX tables (main paper + referee-requested tables).

Reads coefficient and summary CSVs from ``data/generated/`` (written by ``analysis/stata/``
and ``analysis/r/semenova_bounds.R``) and writes publication-ready ``.tex`` tables to
``tex/tables/``.

Usage:
    uv run python analysis/python/make_tables.py                # all tables
    uv run python analysis/python/make_tables.py --only main    # main paper tables only
    uv run python analysis/python/make_tables.py --only referee # referee revision tables only
"""

import argparse
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

from modules.table_utils import (
    add_indents,
    add_stars,
    combine_notes,
    convert_to_latex,
    fmt_beta,
    get_p_value,
    insert_panel,
    star_p,
    stringify_stats,
    write_tex,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_GEN = str(ROOT / "data" / "generated")
TEX = str(ROOT / "tex" / "tables")
YEARS = [2018, 2019]


def build_main_tables():
    """Build main-text and appendix tables from Stata/R outputs."""
    df = pd.read_csv(f"{DATA_GEN}/pds_coeffs.csv")
    print(df.dtypes)
    print(df.isnull().sum())
    df.head()

    dff = pd.read_csv(f"{DATA_GEN}/itt_coeffs.csv")
    print(dff.dtypes)
    print(dff.isnull().sum())
    dff.head()

    dflate = pd.read_csv(f"{DATA_GEN}/lates_coeffs.csv")
    print(dflate.dtypes)
    print(dflate.isnull().sum())
    dflate.head()

    dfiv = pd.read_csv(f"{DATA_GEN}/pds_iv_coeffs.csv")
    print(dfiv.dtypes)
    print(dfiv.isnull().sum())
    dfiv.head()

    # ### Variable descriptions

    # eligible control variables
    ctrl_dict = {
        "Midterm 1 score": "Score on the first midterm",
        "Year = 2019": "1 if course taken in 2019, 0 otherwise",
        "Cumulative GPA": "Cumulative GPA from prior term, 0 if not observed",
        "No cum. GPA": "1 if Cumulative GPA unobserved, 0 otherwise",
        "Math quiz score": "Score on a quiz assessing prerequisite math skills",
        "Tutoring visits": "Number of group tutoring lab visits as of the first midterm",
        "Videos watched": "Number unique videos watched as of the first midterm",
        "Hours videos": "Hours of unique videos watched as of the first midterm",
        "Asian": "1 if ethnicity is Asian, 0 otherwise",
        "Latinx": "1 if ethnicity is Latinx, 0 otherwise",
        "White": "1 if ethnicity is White, 0 otherwise",
        "Female": "1 if female, 0 otherwise",
        "Transfer": "1 if transfer student, 0 otherwise",
    }

    # variable names
    name_dict = {
        "attendance": "Attendance checks",
        "duration_final": "Hours videos by Final",
        "duration_final_u": "Hours unique videos by Final",
        "duration_mid2": "Hours videos by Mid. 2",
        "duration_mid2_u": "Hours unique videos by Mid. 2",
        "duration_b": "Hours of videos",
        "duration_b_u": "Hours unique videos",
        "final_100b": "Final exam score",
        "finalbscorestd": "Final exam score",
        "finalscorestd": "Final exam score",
        "gpa_econ_sans100a": "Econ classes ex. Micro A",
        "gpa_letter": "All classes",
        "gpa_letter_sans100a": "Excluding Micro A",
        "gpa_letter_sansecon": "Excluding econ classes",
        "letter_option": "Letter grade in Micro A",
        "mid1bscorestd": "Midterm 1 score",
        "mid2bscorestd": "Midterm 2 score",
        "mid2scorestd": "Midterm 2 score",
        "nclass_letter": "Num. classes taken for letter",
        "nclass_np": "Num. classes not passed",
        "nclass_p": "Num. classes passed",
        "nclass_pnp": "Num. classes taken P/NP",
        "nclass_w": "Num. classes withdrawn",
        "pass100b": "Pass Micro B",
        "pclass_letter": r"\% classes taken for letter",
        "pclass_pnp": r"\% classes taken P/NP",
        "piazza_answers": "Discussion board answers",
        "piazza_daysonline": "Discussion board days online",
        "piazza_questions": "Discussion board questions asked",
        "piazza_views": "Discussion board views",
        "pset_post": "Tutoring visits",
        "took100b": "Took Micro B",
        "units_letter": "Num. units taken for letter grade",
        "units_pnp": "Num. units taken P/NP",
        "units_w": "Num. units withdrawn",
        "videos_final": "Num. videos before Final",
        "videos_final_u": "Num. unique videos before Final",
        "videos_mid2": "Num. videos before Mid. 2",
        "videos_mid2_u": "Num. unique videos before Mid. 2",
        "videos_b": "Num. of videos",
        "videos_b_u": "Num. unique videos",
        "winter_gpa_econ_sans100a": "Term GPA, econ courses ex. Micro B, winter",
        "winter_gpa_letter": "Term GPA",
        "winter_gpa_letter_sans100a": "Term GPA, ex. Micro B",
        "winter_gpa_letter_sansecon": "Term GPA, ex. econ courses",
        "winter_nclass_letter": "Num. classes taken for letter",
        "winter_nclass_np": "Num. classes not passed",
        "winter_nclass_p": "Num. classes passed",
        "winter_nclass_pnp": "Num. classes taken P/NP",
        "winter_nclass_w": "Num. classes withdrawn",
        "winter_pclass_letter": r"\% classes taken for letter",
        "winter_pclass_pnp": r"\% classes taken P/NP",
        "winter_units_letter": "Num. units taken for letter grade",
        "winter_units_pnp": "Num. units taken P/NP",
        "winter_units_w": "Num. units withdrawn",
        "asian": "Asian",
        "duration_mid1": "Hours videos",
        "duration_mid1_u": "Hours videos, unique",
        "female": "Female",
        "latx": "Latinx",
        "male": "Male",
        "mathquizstd": "Math quiz score",
        "mid1scorestd": "Midterm 1 score",
        "othereth": "Other ethnicity",
        "prev_cumgpa": "Cumulative GPA",
        "prev_cumgpa_unobs": "No cum. GPA",
        "pset_pre": "Tutoring visits",
        "transfer": "Transfer",
        "white": "White",
        "videos_mid1": "Videos watched",
        "videos_mid1_u": "Videos, unique",
        "y2019": "Year = 2019",
    }

    # outcomes reported in each paper table, keyed by the table's LaTeX label (in paper order)
    table_outcomes = {
        "firststage_table": [
            "videos_mid2", "videos_mid2_u", "duration_mid2", "duration_mid2_u",
            "videos_final", "videos_final_u", "duration_final", "duration_final_u",
        ],
        "secondstage_table": ["mid2scorestd", "finalscorestd"],
        "spillover_grades": [
            "gpa_letter", "gpa_letter_sans100a", "gpa_letter_sansecon", "gpa_econ_sans100a",
            "nclass_p", "nclass_np", "nclass_w", "letter_option", "pclass_letter", "pclass_pnp",
        ],
        "spillover_studying": [
            "attendance", "piazza_views", "piazza_daysonline", "piazza_questions",
            "piazza_answers", "pset_post",
        ],
        "spillover_100b": ["took100b", "winter_nclass_p", "winter_nclass_np", "winter_nclass_w"],
        "microb_results": [
            "videos_b", "videos_b_u", "duration_b", "duration_b_u",
            "mid1bscorestd", "mid2bscorestd", "finalbscorestd",
        ],
    }
    table_dict = {v: label for label, vs in table_outcomes.items() for v in vs}
    table_order = {label: i for i, label in enumerate(table_outcomes)}

    # ### Common captions

    # list named strings to be included in the captions of multiple tables.


    # notes on model specification

    note_ittspec = "This table reports coefficients on $Incentive_i$ from Equation \\ref{eq:itt_spec}."

    note_bothspec = (
        "This table reports coefficients on $Incentive_i$ from Equation \\ref{eq:itt_spec} "
        + "(Reduced Form, \\textit{RF}) and $\\hat{Video_i}$ from Equation \\ref{eq:secondstage_spec} "
        + "(Two-Stage Least Squares, \\textit{2SLS})."
    )

    note_4models = (
        "Model (1) contains linear controls for midterm 1 score and year; (2) is "
        + "the difference in means and standard errors calculated using the repeated sampling "
        + "framework of Neyman (1923); (3) and (4) use the post-double-selection (PDS) procedure of "
        + "\\textcite{bch2014a} to select control variables then estimate treatment effects and "
        + "standard errors. The control variables selected using PDS are listed in Appendix Table "
        + "\\ref{tab:controlvars_selected_itt}. Models (2) and (4) include only students whose matched "
        + "pair did not attrite from the experiment."
    )


    # notes on reported control mean

    note_ctrlmean = (
        "\\textit{Control Mean} is the mean for the "
        + "Control students included in models (1) and (3), which is nearly identical "
        + "to the mean for the Control students included in models (2) and (4)."
    )


    # notes on units

    note_scorestd = "Test scores are measured in standard deviation units."

    note_gpa = (
        "GPA is measured on a 4.0 scale and is only affected by courses taken for a letter grade. "
        + "Courses taken for Pass/No Pass (P/NP) have no bearing on GPA, nor do withdrawn courses."
    )

    note_attend = "There were seven \\textit{Attendance checks} during the quarter."

    note_pset = "\\textit{Tutoring visits} includes those after the first midterm."

    # ### Common funtions

    def get_dfb(roundn):
        """
        Combines pds_coeffs (df) and itt_coeffs (dff), formats for table output.
        dfb contains all variables; shape_dfb() selects the desired subset.
        """
        dfb = pd.concat([
            df.copy().drop(columns=["ctrls"]),
            dff.loc[dff["model"].isin(["Neyman", "itt"])].copy(),
        ])
        dfb.rename(columns={"treatbeta": "1beta", "stderr": "2stderr", "meanctrl": "3mean", "N": "4N"}, inplace=True)
        dfb = stringify_stats(add_stars(dfb), roundn)

        # reshape long then wide (models as columns)
        dfb = dfb.melt(id_vars=["depvar", "model"]).sort_values(["depvar", "model", "variable"])
        dfb.rename(columns={"variable": "stat"}, inplace=True)
        dfb = dfb.pivot(index=["depvar", "stat"], columns="model").reset_index()
        dfb.columns = dfb.columns.droplevel(0)
        dfb.columns = ["depvar", "stat", "FEs", "Neyman", "ITT", "All"]
        dfb = dfb[["depvar", "stat", "ITT", "Neyman", "All", "FEs"]]

        dfb["og"] = dfb.depvar.copy()
        dfb["depvar"] = dfb.depvar.apply(lambda x: name_dict.get(x))

        means = dfb.loc[dfb.stat == "3mean", ["og", "ITT"]].rename(columns={"ITT": "ctrlmean"})
        return means.merge(dfb, on="og", how="inner")


    def shape_dfb(varlist, N_list=[""]):
        """
        Restricts dfb to varlist, shapes it, and returns a df ready for latex conversion.
        N_list: variables for which a per-variable Observations row is printed.
        """
        dfsub = dfb.loc[dfb.og.isin(varlist)].copy()
        dfsub = (
            dfsub.loc[dfsub.stat != "3mean"]
            .sort_values(["depvar", "stat"], ascending=[False, True])
            .reset_index(drop=True)
        )

        sorterIndex = dict(zip(varlist, range(len(varlist))))
        dfsub["rank"] = dfsub["og"].map(sorterIndex)
        dfsub = dfsub.sort_values(["rank", "stat"]).reset_index(drop=True)

        dfsub = dfsub.loc[
            (dfsub.stat != "4N")
            | (dfsub.index == max(dfsub.index))
            | ((dfsub.stat == "4N") & (dfsub.og.isin(N_list)))
        ]
        dfsub.loc[dfsub.stat == "4N", "depvar"] = "Observations"

        dfsub["ctrlmean"] = dfsub.ctrlmean.mask(dfsub.ctrlmean.duplicated(), "")
        dfsub.loc[dfsub.depvar != "Observations", "depvar"] = dfsub.loc[
            dfsub.depvar != "Observations"
        ].depvar.mask(dfsub.depvar.duplicated(), "")
        dfsub = dfsub.drop(columns=["stat", "og", "rank"])
        dfsub = dfsub[["depvar", "ctrlmean", "ITT", "Neyman", "All", "FEs"]]

        dfsub = dfsub.reset_index(drop=True)
        dfsub.loc[len(dfsub)] = ["Treatment assignment controls", "", "Yes", "No",  "Yes", "Yes"]
        dfsub.loc[len(dfsub)] = ["Demographic controls",          "", "No",  "No",  "Yes", "Yes"]
        dfsub.loc[len(dfsub)] = ["Pair fixed effects",            "", "No",  "No",  "No",  "Yes"]

        dfsub.rename(columns={"depvar": "", "ctrlmean": "Control Mean",
                               "ITT": "(1)", "Neyman": "(2)", "All": "(3)", "FEs": "(4)"}, inplace=True)
        return dfsub

    # get_p_value and star_p are imported from table_utils

    # ## Covariate balance
    #
    # Create table showing balance across treatment arms on observables

    # Read in data

    dfbal = pd.read_csv(f"{DATA_GEN}/balance_table_data.csv")
    pvals = (
        dfbal[dfbal["arm"] == 2].set_index(["exam", "depvar", "bothpairs"])["pvalue"]
        if "pvalue" in dfbal.columns
        else None
    )
    if "pvalue" in dfbal.columns:
        dfbal = dfbal.drop(columns=["pvalue"])

    # stack mean, stderr, N
    dfbal = dfbal.melt(["exam", "depvar", "arm", "bothpairs"], var_name="stat", value_name="value")
    dfbal["stat"] = dfbal["stat"].replace({"mean": "1mean", "stderr": "2stderr", "N": "3N"})

    # widen using combinations of arm-bothpairs within exam-depvar
    dfbal["combo"] = (dfbal.bothpairs + 1) * 10 + dfbal.arm
    dfbal = dfbal.drop(columns=["arm", "bothpairs"])
    dfbal = dfbal.set_index(["exam", "depvar", "stat", "combo"]).unstack().reset_index()
    dfbal.columns = dfbal.columns.droplevel(0)
    col_list = [
        "above_med_all",
        "ctrl_all",
        "treat_all",
        "above_med_takers",
        "ctrl_takers",
        "treat_takers",
        "ctrl_both",
        "treat_both",
    ]
    dfbal.columns = [
        "exam",
        "depvar",
        "stat",
    ] + col_list

    # sort depvar by 'sorter'
    sorter = [
        "mid1scorestd",
        "y2019",
        "prev_cumgpa",
        "prev_cumgpa_unobs",
        "mathquizstd",
        "pset_pre",
        "videos_mid1",
        "videos_mid1_u",
        "duration_mid1",
        "duration_mid1_u",
        "asian",
        "latx",
        "white",
        "othereth",
        "female",
        "male",
        "transfer",
    ]
    # Create the dictionary that defines the order for sorting
    sorterIndex = dict(zip(sorter, range(len(sorter))))
    # Generate a rank column
    dfbal["depvar_rk"] = dfbal.depvar.map(sorterIndex)
    # sort
    dfbal.sort_values(["exam", "depvar_rk", "stat"], ascending=[False, True, True], inplace=True)

    # insert p-value columns
    dfbal.insert(6, "p_all", np.nan)
    dfbal.insert(10, "p_takers", np.nan)
    dfbal.insert(13, "p_both", np.nan)

    samples = ["all", "takers", "both"]
    sample_bp = {"all": -1, "takers": 0, "both": 1}

    for i in range(int(len(dfbal) / 3)):
        rown = i * 3
        exam_i = dfbal.loc[rown, "exam"]
        depvar_i = dfbal.loc[rown, "depvar"]
        for k in samples:
            if pvals is not None:
                dfbal.loc[rown, "p_" + k] = pvals.loc[(exam_i, depvar_i, sample_bp[k])]
            else:
                meant = dfbal.loc[rown, "treat_" + k]
                meanc = dfbal.loc[rown, "ctrl_" + k]
                stderrt = dfbal.loc[rown + 1, "treat_" + k]
                stderrc = dfbal.loc[rown + 1, "ctrl_" + k]
                Nt = dfbal.loc[rown + 2, "treat_" + k]
                Nc = dfbal.loc[rown + 2, "ctrl_" + k]
                dfbal.loc[rown, "p_" + k] = get_p_value(meant, meanc, stderrt, stderrc, Nt, Nc)

    # get stars
    for k in samples:
        col = "p_" + k
        dfbal[col] = dfbal.apply(lambda x, c=col: star_p(x[c]) if x["stat"] == "1mean" else "", 1)

    # Remove all N's except last one for each exam
    keepidx = dfbal.groupby("exam", as_index=False).stat.nth(-1).index
    dfbal = dfbal.loc[(dfbal.stat != "3N") | (dfbal.index.isin(keepidx))]

    # Rename depvars and duplicates
    dfbal["og"] = dfbal["depvar"].copy()
    dfbal["depvar"] = dfbal.depvar.apply(lambda x: name_dict.get(x))
    # dfbal['depvar'] = dfbal.depvar.apply(lambda x: '\\indentrow{' + name_dict.get(x) + '}')
    dropidx = dfbal.groupby(["exam", "depvar"], as_index=False).stat.nth(1).index
    dfbal.loc[dropidx, "depvar"] = ""
    dfbal.loc[dfbal.stat == "3N", "depvar"] = "Observations"

    # stringify stat values
    dfbal[col_list] = dfbal[col_list].astype(object)
    for v in col_list:
        dfbal.loc[dfbal.stat == "1mean", v] = dfbal.loc[dfbal.stat == "1mean", v].apply(
            lambda x: f"{x:.3f}"
        )
        dfbal.loc[dfbal.stat == "2stderr", v] = dfbal.loc[dfbal.stat == "2stderr", v].apply(
            lambda x: f"({x:.3f})"
        )
        dfbal.loc[dfbal.stat == "3N", v] = dfbal.loc[dfbal.stat == "3N", v].apply(
            lambda x: str(int(x))
        )


    # remove unnecessary cols, colnames
    dfbal = dfbal.drop(columns=["og", "stat", "depvar_rk"])
    dfbal = dfbal.rename(
        columns={
            "depvar": "Variable",
            "above_med_all": "Above Median",
            "ctrl_all": "Control",
            "treat_all": "Incentive",
            "above_med_takers": "Above Median",
            "ctrl_takers": "Control",
            "treat_takers": "Incentive",
            "ctrl_both": "Control",
            "treat_both": "Incentive",
            "p_takers": "(3) - (2)",
            "p_all": "(3) - (2)",
            "p_both": "(5) - (4)",
        }
    )

    # convert only the sample of those who took the exams to tex

    btable_taker = dfbal.iloc[:, np.r_[0:2, 6:10]].copy()
    cols = btable_taker.columns[1:]
    btable_taker = pd.concat(
        [
            btable_taker.loc[btable_taker.exam == "mid2", cols].reset_index(drop=True),
            btable_taker.loc[btable_taker.exam == "final", cols].reset_index(drop=True),
        ],
        axis=1,
    ).iloc[:, np.r_[0:5, 6:10]]
    btable_taker.columns = btable_taker.columns[:-1].tolist() + ["(6) - (5)"]

    # convert to latex

    column_format = "m{0.25\\linewidth} *{8}{>{\\centering\\arraybackslash}m{0.095\\linewidth}}"
    caption = "Balance Test, Exam Taker Sample"
    label = "balance_table_takers"
    note = (
        "This table includes all students who completed the second midterm and final exams. "
        + "Descriptions of each variable can be found in Appendix Table \\ref{tab:controlvars_desc}. "
        + "\\textit{Female} and \\textit{Male} are coded zero for nine students who do not report "
        + "a gender. \\textit{P-values} are reported for the Welch's t-test of equal means between "
        + "the \\textit{Control} and \\textit{Incentive} arms."
    )

    k = convert_to_latex(btable_taker, column_format, caption, label, note)

    # Add additional column labels
    k = k.replace(
        "\\toprule",
        "\\toprule \n & \\multicolumn{3}{c}{Midterm 2 Sample} & P-values & "
        + "\\multicolumn{3}{c}{Final Exam Sample}  & P-values  \\\\ \n"
        + "\\cmidrule(lr){2-4}\\cmidrule(lr){6-8} \n",
        1,
    )

    # space out variables
    for v in [x for x in dfbal.Variable.unique() if x not in ["", "Observations"]]:
        k = k.replace(v + " &", "\\customlinespace " + v + " &")

    # write to tex file
    with open(f"{TEX}/" + label + ".tex", "w") as tf:
        tf.write(k)

    # the full sample is the same for mid2 and final, so only keep one copy

    btable_all = dfbal.loc[dfbal.exam == "mid2"].drop(columns=["exam"]).iloc[:, 0:5]

    # convert to latex

    column_format = "m{0.25\\linewidth} *{5}{>{\\centering\\arraybackslash}m{0.095\\linewidth}}"
    caption = "Balance Test, Full Sample"
    label = "balance_table_all"
    note = (
        "This table includes all students who saw their treatment assignment. "
        + "Descriptions of each variable can be found in Table \\ref{tab:controlvars_desc}. "
        + "\\textit{Female} and \\textit{Male} are coded zero for nine students who do not report "
        + "a gender. \\textit{P-values} are reported for the Welch's t-test of equal means between "
        + "the \\textit{Control} and \\textit{Incentive} arms."
    )

    k = convert_to_latex(btable_all, column_format, caption, label, note)

    # Add additional column labels
    k = k.replace(
        "\\toprule",
        "\\toprule \n & \\multicolumn{3}{c}{All Students} & P-values & \\\\ \n"
        + "\\cmidrule(lr){2-4} \n",
        1,
    )

    # space out variables
    for v in [x for x in dfbal.Variable.unique() if x not in ["", "Observations"]]:
        k = k.replace(v + " &", "\\customlinespace " + v + " &")

    # scale to page height; the table is too tall for \linewidth scaling
    k = k.replace("\\resizebox{\\linewidth}{!}{% \n", "\\resizebox*{!}{\\textheight}{%\n", 1)

    # write to tex file
    with open(f"{TEX}/" + label + ".tex", "w") as tf:
        tf.write(k)

    # Matched pairs only

    btable_matched = dfbal.iloc[:, np.r_[0:2, 10:13]].copy()
    cols = btable_matched.columns[1:]
    btable_matched = pd.concat(
        [
            btable_matched.loc[btable_matched.exam == "mid2", cols].reset_index(drop=True),
            btable_matched.loc[btable_matched.exam == "final", cols].reset_index(drop=True),
        ],
        axis=1,
    ).iloc[:, np.r_[0:4, 5:8]]
    btable_matched = btable_matched.rename(columns={"(5) - (4)": "(2) - (1)"})
    btable_matched.columns = btable_matched.columns[:-1].tolist() + ["(4) - (3)"]

    # convert to latex

    column_format = "m{0.25\\linewidth} *{6}{>{\\centering\\arraybackslash}m{0.095\\linewidth}}"
    caption = "Baseline Balance Test, Matched Pairs"
    label = "balance_table_matched"
    note = (
        "This table includes all matched pairs who both complete the second midterm "
        + "or final exams. "
        + "Descriptions of each variable can be found in Appendix Table \\ref{tab:controlvars_desc}. "
        + "\\textit{Female} and \\textit{Male} are coded zero for nine students who do not report "
        + "a gender. \\textit{P-values} are reported for the Welch's t-test of equal means between "
        + "the \\textit{Control} and \\textit{Incentive} arms."
    )


    k = convert_to_latex(btable_matched, column_format, caption, label, note)

    # Add additional column labels
    k = k.replace(
        "\\toprule",
        "\\toprule \n & \\multicolumn{2}{c}{Midterm 2} & P-values & "
        + "\\multicolumn{2}{c}{Final}  & P-values  \\\\ \n"
        + "\\cmidrule(lr){2-3}\\cmidrule(lr){5-6} \n",
        1,
    )

    # space out variables
    for v in [x for x in dfbal.Variable.unique() if x not in ["", "Observations"]]:
        k = k.replace(v + " &", "\\customlinespace " + v + " &")

    # write to tex file
    with open(f"{TEX}/" + label + ".tex", "w") as tf:
        tf.write(k)

    # ## Post-double-selection control variable selection

    # ### Table: description of eligible control vars

    # construct dict

    ctrls = [
        "Midterm 1 score",
        "Year = 2019",
        "Cumulative GPA",
        "No cum. GPA",
        "Math quiz score",
        "Tutoring visits",
        "Videos watched",
        "Hours videos",
        "Asian",
        "Latinx",
        "White",
        "Female",
        "Transfer",
    ]

    dfc = pd.DataFrame(data={"Variable": ctrls, "Description": [ctrl_dict.get(x) for x in ctrls]})

    # translate to tex

    column_format = r"p{0.3\linewidth} p{0.6\linewidth}"
    caption = "Candidate Control Variables for Post-Double-Selection"
    label = "controlvars_desc"
    note = (
        "\\textit{Midterm 1 score} and \\textit{Math quiz score} are measured in control standard deviations. "
        + "\\textit{Cumulative GPA} is measured on a 4.0 scale. Videos included in \\textit{Videos watched} and "
        + "\\textit{Hours videos} are unique course-relevant videos. The ethnicity variables are coded by university "
        + 'records: \\textit{Asian} includes "Chinese/Chinese American", "Vietnamese", "East Indian/Pakistani", '
        + '"Japanese/Japanese American", "Korean/Korean American", and "All other Asian/Asian American"; \\textit{Latinx} '
        + 'includes "Mexican/Mexican American", "Chicano", and "All other Spanish-American/Latino"; \\textit{White} '
        + 'includes "White/Caucasian"; and the omitted category includes "African American/Black", "Pacific Islander", '
        + 'and "Not given/declined to state".'
    )

    table0 = convert_to_latex(
        dfc, column_format, caption, label, note, scalewidth=False, regnote=False
    )

    # write to tex file
    with open(f"{TEX}/controlvars_desc.tex", "w") as tf:
        tf.write(table0)

    # ### Table: control variables for ITT PDS

    # first reshape wide
    dfw = df[["depvar", "model", "ctrls"]].set_index(["depvar", "model"]).unstack().reset_index()
    dfw.columns = dfw.columns.droplevel(0)
    dfw.columns = [
        "Dependent Variable",
        "Controls,\\newline Fixed Effects",
        "Controls,\\newline All Observations",
    ]
    dfw = dfw.iloc[:, [0, 2, 1]]
    dfw["og"] = dfw.iloc[:, 0].copy()

    ctrls = [x for x in dfw.iloc[:, 2].unique()]
    ctrls += [x for x in dfw.iloc[:, 1].unique() if x not in ctrls]
    ctrls = [str(x).split(" ") for x in ctrls]
    ctrls = [j for i in ctrls for j in i]
    ctrls = list(dict.fromkeys(ctrls))
    for x in ["nan"]:
        ctrls.remove(x)
    ctrls.sort()

    # Relabel variables with publication-ready names

    for i in range(0, 3):
        col = dfw.columns[i]
        dfw[col] = dfw[col].apply(
            lambda x: ("\\newline ").join(sorted(name_dict.get(k) or "None" for k in str(x).split(" ")))
        )

    # Add Table labels; keep only outcomes reported in the paper

    dfw = dfw.loc[dfw.og.isin(table_dict)].copy()
    dfw["Table"] = dfw.og.map(lambda x: f"Table \\ref{{tab:{table_dict[x]}}}")
    dfw["_order"] = dfw.og.map(lambda x: table_order[table_dict[x]])
    dfw.sort_values(["_order", dfw.columns[0]], inplace=True)
    dfw = dfw.drop(columns="_order")

    # set Table 'index' as first column
    dfw["Table"] = dfw["Table"].mask(dfw["Table"].duplicated(), "")
    dfw = dfw.loc[:, ["Table"] + [c for c in dfw.columns if c != "Table"]]
    dfw.reset_index(inplace=True, drop=True)

    # convert to tex (drop og column)
    table1 = dfw[dfw.columns[:-1]].copy()

    # shorten variable descriptions
    for c in table1.columns[-2:]:
        table1.loc[table1[c].str.contains(", unique"), c] = table1.loc[
            table1[c].str.contains(", unique"), c
        ].apply(lambda x: x.replace(", unique", ""))


    # convert to latex

    column_format = (
        r"p{0.07\linewidth} >{\hangindent=1em}p{0.38\linewidth} "
        + r"p{0.22\linewidth} p{0.22\linewidth}"
    )
    caption = "ITT Model Controls Selected via Post-Double-Selection"
    label = "controlvars_selected_itt"
    note = (
        "Controls chosen via the PDS procedure of \\textcite{bch2014a}. "
        + "In the \\textit{All Observations} model, \\textit{Midterm 1 score} and \\textit{Year = 2019} are "
        + "additionally included as controls. In the \\textit{Fixed Effects} model, pair fixed effects "
        + "and \\textit{Midterm 1 score} are included. "
        + "All control variables are measured before the start of the experiment, e.g. \\textit{Hours videos} is "
        + "the hours of videos watched as of the first midterm."
    )

    table1 = convert_to_latex(
        table1,
        column_format,
        caption,
        label,
        note,
        observations=False,
        longtable=True,
        stars=False,
        scalewidth=False,
    )

    # add horizontal lines betweeen groups
    for label in list(table_outcomes)[1:]:
        ref = f"Table \\ref{{tab:{label}}}"
        table1 = table1.replace(ref, f"\\midrule \n{ref}", 1)

    # write to tex file
    with open(f"{TEX}/controlvars_selected_itt.tex", "w") as tf:
        tf.write(table1)

    # ### Table: control variables for LATE PDS

    # first reshape wide
    dfw = dfiv.copy()

    # mark instruments
    dfw["endog"] = dfw.model.apply(lambda x: x[-1])

    # rename models FE or not
    dfw["model"] = dfw.model.apply(lambda x: x[:-2])

    # reshape wide
    dfw = (
        dfw[["depvar", "model", "endog", "ctrls"]]
        .set_index(["depvar", "endog", "model"])
        .unstack()
        .reset_index()
    )
    dfw.columns = dfw.columns.droplevel(0)
    dfw.columns = [
        "Dependent Variable",
        "Instrumented",
        "Controls,\\newline All Observations",
        "Controls,\\newline Fixed Effects",
    ]

    # rename instruments
    dfw["Instrumented"] = dfw["Instrumented"].replace({"d": "duration_mid1_u", "v": "videos_mid1_u"})

    # copy og varnames
    dfw["og"] = dfw.iloc[:, 0].copy()

    # replace varnames with publishable names
    for i in range(0, 4):
        col = dfw.columns[i]
        dfw[col] = dfw[col].apply(
            lambda x: ("\\newline ").join(sorted(name_dict.get(k) or "None" for k in str(x).split(" ")))
        )

    # sort by publishable name
    dfw.sort_values(["Dependent Variable", "Instrumented"], ascending=[True, True], inplace=True)


    # export to tex

    # get subset and convert to tex
    tablevars = dfw.og.unique()  # change this
    table = dfw.loc[dfw.og.isin(tablevars), dfw.columns[:-1]]

    # shorten variable descriptions
    for c in table.columns[-2:]:
        table.loc[table[c].str.contains(", unique"), c] = table.loc[
            table[c].str.contains(", unique"), c
        ].apply(lambda x: x.replace(", unique", ""))

    # convert to latex

    column_format = r"p{.25\linewidth} p{0.3\linewidth} " + r"p{0.22\linewidth} p{0.22\linewidth}"
    caption = "LATE Model Controls Selected via Post-Double-Selection"
    label = "controlvars_selected_iv"
    note = (
        "Controls chosen via the PDS procedure of \\textcite{bch2014a}. "
        + "In the \\textit{All Observations} model, \\textit{Midterm 1 score} and \\textit{Year = 2019} are "
        + "additionally included as controls. In the \\textit{Fixed Effects} model, pair fixed effects "
        + "and \\textit{Midterm 1 score} are included. "
        + "All control variables are measured before the start of the experiment, e.g. \\textit{Hours videos} is "
        + "the hours of videos watched as of the first midterm."
    )

    table = convert_to_latex(
        table,
        column_format,
        caption,
        label,
        note,
        scalewidth=True,
        observations=False,
        regnote=False,
    )

    # write to tex file
    with open(f"{TEX}/controlvars_selected_iv.tex", "w") as tf:
        tf.write(table)

    # ## Coefficient estimates - below cutoff experiment

    # ### Table: first stage

    # get dfb

    dfb = get_dfb(2)
    dfb.head()

    # create table for first stage vars only

    table1_vars = [
        "videos_mid2",
        "videos_mid2_u",
        "duration_mid2",
        "duration_mid2_u",
        "videos_final",
        "videos_final_u",
        "duration_final",
        "duration_final_u",
    ]

    dfsub = shape_dfb(table1_vars, ["duration_mid2_u"])

    # name changes
    rename_dict = {
        "Num. videos": "Videos",
        "Num. unique": "Unique videos",
        "Hours videos": "Hours of videos",
        "Hours unique": "Hours of unique videos",
    }
    for v in rename_dict:
        dfsub.iloc[dfsub.iloc[:, 0].str.contains(v), 0] = rename_dict.get(v)


    # translate to tex

    column_format = "m{0.35\\linewidth} *{5}{>{\\centering\\arraybackslash}m{0.1\\linewidth}}"
    caption = "Effects of Grade Incentive on Video Watching"
    label = "firststage_table"
    note = combine_notes([note_4models, note_ctrlmean])

    table = convert_to_latex(
        dfsub, column_format, caption, label, note, scalewidth=False, observations=True
    )

    # add panel labels
    table = insert_panel(table, 6, "A", "By Midterm 2", "Videos")
    table = insert_panel(table, 6, "B", "By Final Exam", "Videos", False)

    # add indents
    varlist = [x for x in dfsub.iloc[:-4, 0].unique() if x not in ["", "Observations"]]
    table = add_indents(table, varlist)

    # write to tex file
    with open(f"{TEX}/firststage.tex", "w") as tf:
        tf.write(table)

    # ### Table: second stage

    # redo dfb with different rounding

    dfb = get_dfb(3)
    dfb.head()

    def get_dfl(roundn):
        """
        Combines pds_iv_coeffs (dfiv) and lates_coeffs (dflate), formats for table output.
        """
        dfl = pd.concat([
            dfiv.copy().drop(columns=["ctrls"]),
            dflate.loc[~dflate.model.str.contains("with_zeros")].copy(),
        ])
        dfl.rename(columns={"treatbeta": "1beta", "stderr": "2stderr", "meanctrl": "3mean", "N": "4N"}, inplace=True)
        dfl = stringify_stats(add_stars(dfl), roundn)

        dfl["Instrumented"] = dfl.model.apply(lambda x: x[-1])
        dfl["model"] = dfl.model.apply(lambda x: x[:-2])

        # reshape long then wide (models as columns)
        dfl = dfl.melt(id_vars=["depvar", "model", "Instrumented"]).sort_values(
            ["depvar", "Instrumented", "model", "variable"], ascending=[False, True, True, True]
        )
        dfl.rename(columns={"variable": "stat"}, inplace=True)
        dfl = dfl.pivot(index=["depvar", "Instrumented", "stat"], columns="model").reset_index()
        dfl.columns = dfl.columns.droplevel(0)
        dfl.columns = ["depvar", "Instrumented", "stat", "Neyman", "All", "FEs", "ITT"]
        dfl = dfl[["depvar", "Instrumented", "stat", "ITT", "Neyman", "All", "FEs"]]

        dfl["og"] = dfl.depvar.copy()
        dfl["depvar"] = dfl.depvar.apply(lambda x: name_dict.get(x))
        return dfl


    dfl = get_dfl(3)
    dfl.head()

    # stack with dfb (ITT estimates)

    # keep only second stage vars
    table2_vars = table_outcomes["secondstage_table"]
    dfsub = dfb.loc[dfb.og.isin(table2_vars)].copy()

    # add 'instrumented' col (for stacking), drop ctrlmean
    dfsub.insert(1, "Instrumented", "z")
    dfsub = dfsub.drop(columns=["ctrlmean"])

    # combine the two dfs and sort, drop mean
    dfsub = pd.concat([dfsub, dfl])
    dfsub = dfsub.loc[dfsub.stat != "3mean"]
    dfsub.sort_values(["depvar", "Instrumented", "stat"], ascending=[False, False, True], inplace=True)

    # drop intermediate N within each exam
    keepidx = dfsub.groupby("og", as_index=False).stat.nth(-1).index
    dfsub = dfsub.loc[(dfsub.stat != "4N") | (dfsub.index.isin(keepidx))]
    dfsub.loc[dfsub.stat == "4N", "Instrumented"] = "Observations"

    # name instruments
    dfsub["Instrumented"] = dfsub["Instrumented"].replace(
        {"z": "RF: Incentive", "v": "2SLS: 10 unique videos", "d": "2SLS: 1 hour of unique videos"}
    )

    # remove Instrumented duplicates and unnecessary cols
    for v in dfsub.og.unique():
        dfsub.loc[dfsub.og == v, "Instrumented"] = dfsub.loc[dfsub.og == v].Instrumented.mask(
            dfsub.loc[dfsub.og == v].Instrumented.duplicated(), ""
        )
    dfsub = dfsub.drop(columns=["depvar", "stat", "og"])

    # rename cols
    dfsub.rename(
        columns={
            "Instrumented": "",
            "ITT": "(1)",
            "Neyman": "(2)",
            "All": "(3)",
            "FEs": "(4)",
        },
        inplace=True,
    )

    # append bottom of table info
    dfsub.reset_index(drop=True, inplace=True)
    dfsub.loc[len(dfsub), :] = ["Treatment assignment controls", "Yes", "No", "Yes", "Yes"]
    dfsub.loc[len(dfsub), :] = ["Demographic controls", "No", "No", "Yes", "Yes"]
    dfsub.loc[len(dfsub), :] = ["Pair fixed effects", "No", "No", "No", "Yes"]


    # translate to tex

    column_format = "m{0.35\\linewidth} *{4}{>{\\centering\\arraybackslash}m{0.1\\linewidth}}"
    caption = "Effects of Videos on Grades"
    label = "secondstage_table"
    note_4models_iv = note_4models.replace(
        "Table \\ref{tab:controlvars_selected_itt}",
        "Tables \\ref{tab:controlvars_selected_itt} and \\ref{tab:controlvars_selected_iv}",
    )
    note = combine_notes([note_bothspec, note_scorestd, note_4models_iv])

    table = convert_to_latex(
        dfsub, column_format, caption, label, note, scalewidth=False, observations=True
    )

    # add panel labels
    table = insert_panel(table, 5, "A", "Midterm 2 score", "RF: Incentive")
    table = insert_panel(table, 5, "B", "Final exam score", "RF: Incentive", False)

    # add indents
    varlist = [x for x in dfsub.iloc[:-4, 0].unique() if x not in ["", "Observations"]]
    table = add_indents(table, varlist)

    # write to tex file
    with open(f"{TEX}/secondstage.tex", "w") as tf:
        tf.write(table)

    # ### Table: spillovers to grades

    # get dfb

    dfb = get_dfb(2)
    dfb.head()

    # create table for spillover vars only

    table3_vars = [
        "gpa_letter",
        "gpa_letter_sans100a",
        "gpa_letter_sansecon",
        "gpa_econ_sans100a",
        "nclass_p",
        "nclass_np",
        "nclass_w",
        "letter_option",
        "pclass_letter",
        "pclass_pnp",
    ]
    gpalist = [x for x in table3_vars if x.find("gpa") > -1]
    dfsub = shape_dfb(table3_vars, gpalist)

    # translate to tex

    column_format = "m{0.35\\linewidth} *{5}{>{\\centering\\arraybackslash}m{0.1\\linewidth}}"
    caption = "Spillover Effects of Incentive on Other Course Grades"
    label = "spillover_grades"
    note = combine_notes([note_ittspec, note_gpa, note_4models, note_ctrlmean])

    table = convert_to_latex(
        dfsub, column_format, caption, label, note, scalewidth=True, observations=False
    )

    # remove first 4 "observations"
    idx = [m.start() for m in re.finditer("Observations", table)]
    for i in idx[3::-1]:
        table = table[:i] + table[i + len("Observations") :]

    # add panel labels
    table = insert_panel(table, 6, "A", "Effects on Term GPA", "All classes")
    table = insert_panel(table, 6, "B", "Effects on classes passed", "Num. classes passed", False)
    table = insert_panel(
        table, 6, "C", "Effects on class grade type", "Letter grade in Micro A", False
    )

    # add indents
    varlist = [x for x in dfsub.iloc[:-4, 0].unique() if x not in ["", "Observations"]]
    table = add_indents(table, varlist)

    # add \midrule before last 'Observations'
    idx = table.rfind("Observations")
    table = table[:idx] + "\n\\midrule \n" + table[idx:]

    # shrink table a bit
    idx = table.find("resizebox{")
    idx += len("resizebox{")
    table = table[:idx] + "0.9" + table[idx:]

    # write to tex file
    with open(f"{TEX}/spillover_grades.tex", "w") as tf:
        tf.write(table)

    # ### Table: spillovers to studying

    # get dfb

    dfb = get_dfb(2)
    dfb.head()

    # get dfsub

    table4_vars = [
        "attendance",
        "piazza_views",
        "piazza_daysonline",
        "piazza_questions",
        "piazza_answers",
        "pset_post",
    ]

    # gpalist = [x for x in table4_vars if x.find('gpa') > -1]
    dfsub = shape_dfb(table4_vars)

    # translate to tex

    column_format = "m{0.39\\linewidth} *{5}{>{\\centering\\arraybackslash}m{0.09\\linewidth}}"
    caption = "Spillover Effects of Incentive on Other Studying"
    label = "spillover_studying"
    note = combine_notes([note_ittspec, note_attend, note_pset, note_4models, note_ctrlmean])

    table = convert_to_latex(
        dfsub, column_format, caption, label, note, scalewidth=False, observations=True
    )

    # write to tex file
    with open(f"{TEX}/spillover_studying.tex", "w") as tf:
        tf.write(table)

    # ### Table: spillovers to subsequent quarter

    # get dfb

    dfb = get_dfb(2)
    dfb.head()

    # Table 8: Effects on enrollment and course-type outcomes (formerly Panel C)

    table8_vars = [
        "took100b",
        "winter_nclass_p",
        "winter_nclass_np",
        "winter_nclass_w",
    ]
    dfsub = shape_dfb(table8_vars)

    # translate to tex

    column_format = "m{0.35\\linewidth} *{5}{>{\\centering\\arraybackslash}m{0.1\\linewidth}}"
    caption = "Effects of Treatment on Subsequent Quarter Enrollment and Course Outcomes"
    label = "spillover_100b"
    notex = (
        "Sample includes all students who completed Micro A. "
        "Took Micro B is an indicator for enrolling in the subsequent course in the "
        "quarter following the experiment."
    )
    note_models_t8 = (
        "Model (1) contains linear controls for midterm 1 score and year; "
        "(2) is the difference in means and standard errors calculated using the repeated "
        "sampling framework of Neyman (1923); (3) and (4) use the post-double-selection "
        "(PDS) procedure of \\textcite{bch2014a} to select control variables then estimate "
        "treatment effects and standard errors. The control variables selected using PDS "
        "are listed in Appendix Table \\ref{tab:controlvars_selected_itt}."
    )
    note = combine_notes([note_ittspec, notex, note_models_t8, note_ctrlmean])

    table = convert_to_latex(
        dfsub, column_format, caption, label, note, scalewidth=True, observations=True
    )

    # add indents
    varlist = [x for x in dfsub.iloc[:, 0].unique() if x not in ["", "Observations",
               "Treatment assignment controls", "Demographic controls", "Pair fixed effects"]]
    table = add_indents(table, varlist)

    # write to tex file
    with open(f"{TEX}/spillover_100b.tex", "w") as tf:
        tf.write(table)

    # ### Table 9: Micro B results


    # Panel A: video watching outcomes
    # Panel B: exam score outcomes
    t9_panel_a = ["videos_b", "videos_b_u", "duration_b", "duration_b_u"]
    t9_panel_b = ["mid1bscorestd", "mid2bscorestd", "finalbscorestd"]
    t9_outcomes = t9_panel_a + t9_panel_b

    t9_display = {
        "videos_b": "Num. of videos",
        "videos_b_u": "Num. unique videos",
        "duration_b": "Hours of videos",
        "duration_b_u": "Hours unique videos",
        "mid1bscorestd": "Midterm 1 score",
        "mid2bscorestd": "Midterm 2 score",
        "finalbscorestd": "Final exam score",
    }

    # Mapping from PDS/ITT depvar to semenova/ipw depvar
    t9_alt_depvar = {
        "videos_b": "videos_b",
        "videos_b_u": "videos_b_u",
        "duration_b": "duration_b",
        "duration_b_u": "duration_b_u",
        "mid1bscorestd": "mid1_100bstd",
        "mid2bscorestd": "mid2_100bstd",
        "finalbscorestd": "final_100bstd",
    }

    # --- Column (1): PDS without pair FEs ---
    df_pds = pd.read_csv(f"{DATA_GEN}/pds_coeffs.csv")
    df_pds = df_pds[(df_pds["model"] == "noFEs") & (df_pds["depvar"].isin(t9_outcomes))].copy()
    df_pds = df_pds.set_index("depvar")

    # --- Column (2): Semenova (2025) Bounds ---
    semenova_path = f"{DATA_GEN}/semenova_bounds_100b.csv"
    semenova_available = os.path.exists(semenova_path)
    if not semenova_available:
        print(f"Warning: {semenova_path} not found. Column (2) will be omitted.")
    else:
        df_sem = pd.read_csv(semenova_path)
        df_sem = df_sem[df_sem["depvar"].isin(t9_alt_depvar.values())].copy()
        df_sem = df_sem.set_index("depvar")

    # --- Column (3): IPW ---
    ipw_path = f"{DATA_GEN}/ipw_100b.csv"
    ipw_available = os.path.exists(ipw_path)
    if not ipw_available:
        print(f"Warning: {ipw_path} not found. Column (3) will be omitted.")
    else:
        df_ipw = pd.read_csv(ipw_path)
        df_ipw = df_ipw[df_ipw["depvar"].isin(t9_alt_depvar.values())].copy()
        df_ipw = df_ipw.set_index("depvar")

    # Build display DataFrame

    def fmt_stars(beta, se):
        """Attach significance stars to a rounded coefficient."""
        t_stat = abs(beta / se) if se != 0 else 0
        stars_str = "***" if t_stat >= 2.576 else "**" if t_stat >= 1.96 else "*" if t_stat >= 1.645 else ""
        return f"{beta:.2f}{stars_str}"

    rows = []

    for depvar in t9_outcomes:
        label_str = t9_display[depvar]
        alt_depvar = t9_alt_depvar[depvar]

        # Column (1): PDS noFEs
        if depvar in df_pds.index:
            row_pds = df_pds.loc[depvar]
            ctrl_mean = f"{row_pds['meanctrl'] + 0.0:.2f}".replace("-0.00", "0.00")
            beta_stars = fmt_stars(row_pds["treatbeta"], row_pds["stderr"])
            se_str = f"({row_pds['stderr']:.2f})"
            n1 = str(int(row_pds["N"]))
        else:
            ctrl_mean, beta_stars, se_str, n1 = "", "", "", ""

        # Column (2): Semenova bounds
        if semenova_available and alt_depvar in df_sem.index:
            row_sem = df_sem.loc[alt_depvar]
            bounds_str = f"[{row_sem['lower_bound']:.2f}, {row_sem['upper_bound']:.2f}]"
            ci_str = r"\{" + f"{row_sem['ci_lower']:.2f}, {row_sem['ci_upper']:.2f}" + r"\}"
            n2 = str(int(row_sem["N_selected"]))
        else:
            bounds_str, ci_str, n2 = "", "", ""

        # Column (3): IPW
        if ipw_available and alt_depvar in df_ipw.index:
            row_ipw = df_ipw.loc[alt_depvar]
            ipw_beta = fmt_stars(row_ipw["treatbeta"], row_ipw["stderr"])
            ipw_se = f"({row_ipw['stderr']:.2f})"
            n3 = str(int(row_ipw["N"]))
        else:
            ipw_beta, ipw_se, n3 = "", "", ""

        row1 = {"Outcome": label_str, "Control Mean": ctrl_mean, "(1) PDS": beta_stars}
        row2 = {"Outcome": "", "Control Mean": "", "(1) PDS": se_str}
        # sample sizes differ across outcomes (Micro B exam takers vary by exam), so report N per row
        row3 = {"Outcome": "", "Control Mean": "", "(1) PDS": n1}
        if semenova_available:
            row1["(2) Semenova Bounds"] = bounds_str
            row2["(2) Semenova Bounds"] = ci_str
            row3["(2) Semenova Bounds"] = n2
        if ipw_available:
            row1["(3) IPW"] = ipw_beta
            row2["(3) IPW"] = ipw_se
            row3["(3) IPW"] = n3
        rows.extend([row1, row2, row3])

    dft9 = pd.DataFrame(rows)

    # Convert to LaTeX and write Table 9

    note_t9_col1 = (
        "Column (1) reports post-double-selection (PDS) OLS coefficients on $Incentive_i$ "
        "estimated on the selected sample of Micro B takers, with heteroskedasticity-robust "
        "standard errors in parentheses. The third row for each outcome "
        "reports the number of observations."
    )
    note_t9_col2 = (
        "Column (2) reports generalized Lee (2009) bounds following "
        "\\textcite{semenova2025}; point estimates are shown as [lower, upper] and "
        "95\\% confidence regions are shown in curly braces."
    )
    note_t9_col3 = (
        "Column (3) reports IPW-weighted OLS, where weights are the inverse probability "
        "of enrolling in Micro B conditional on baseline covariates, winsorized at the "
        "1st and 99th percentiles, with bootstrapped standard errors (1,000 replications)."
    )

    notes_list = [note_t9_col1]
    if semenova_available:
        notes_list.append(note_t9_col2)
    if ipw_available:
        notes_list.append(note_t9_col3)
    notes_list.append(note_scorestd)
    note_t9 = combine_notes(notes_list)
    # star legend only: \Regnote's robust-SE statement does not fit the bootstrapped IPW column
    note_t9 += " \\par\\noindent $^{*}p < .10$; $^{**}p < .05$; $^{***}p < .01$"

    caption = "Treatment Effects on Micro B Outcomes"
    label = "tab:microb_results"

    ncols = 3 + semenova_available + ipw_available
    column_format = "l" + "c" * (ncols - 1)

    table9 = convert_to_latex(
        dft9, column_format=column_format, caption=caption, label=label,
        note=note_t9, observations=False, scalewidth=True, stars=True, regnote=False,
    )

    # Add panel labels
    table9 = insert_panel(table9, ncols, "A", "Videos during Micro B", name_dict.get("videos_b"))
    table9 = insert_panel(table9, ncols, "B", "Micro B exam scores", name_dict.get("mid1bscorestd"), False)

    # Indent variable names
    varlist = [v for v in dft9["Outcome"].unique() if v != ""]
    table9 = add_indents(table9, varlist)

    with open(f"{TEX}/table9_microb.tex", "w") as tf:
        tf.write(table9)

    # ## Other tables

    # ### Table: heterogeneity

    # read in data
    dfh = pd.read_csv(f"{DATA_GEN}/het_coeffs.csv")
    dfh = dfh.drop(columns=["meanctrl"])
    print(dfh.dtypes)
    print(dfh.isnull().sum())
    dfh.head()

    # reformat, similar to get_dfb

    dfht = dfh.copy()

    # get stars and prepare to order stats
    dfht.rename(columns={"interactbeta": "1beta", "stderr": "2stderr", "N": "3N"}, inplace=True)
    dfht["stars"] = 0
    dfht.loc[(abs(dfht["1beta"]) - dfht["2stderr"] * 1.645) > 0, "stars"] = 1
    dfht.loc[(abs(dfht["1beta"]) - dfht["2stderr"] * 1.96) > 0, "stars"] = 2
    dfht.loc[(abs(dfht["1beta"]) - dfht["2stderr"] * 2.576) > 0, "stars"] = 3

    # stringify stats
    dfht["1beta"] = dfht["1beta"].apply(lambda x: f"{x:.3f}")
    dfht["1beta"] = dfht["1beta"] + dfht.stars.apply(lambda x: "*" * x)
    dfht["2stderr"] = dfht["2stderr"].apply(lambda x: f"({x:.3f})")
    dfht["3N"] = dfht["3N"].apply(lambda x: str(int(x)))
    dfht = dfht.drop(columns=["stars"])

    # reshape and rename columns
    dfht = dfht.melt(id_vars=["depvar", "interactvar"]).sort_values(["interactvar", "variable"])
    dfht.rename(columns={"variable": "stat"}, inplace=True)
    dfht = dfht.pivot(index=["interactvar", "stat"], columns="depvar").reset_index()
    dfht.columns = dfht.columns.droplevel(0)
    dfht.columns = ["depvar", "stat", "Final Exam", "Midterm 2"]
    dfht = dfht[["depvar", "stat", "Midterm 2", "Final Exam"]]

    # sort by prefered varlist order
    varlist = [
        "mid1scorestd",
        "y2019",
        "videos_mid1",
        "videos_mid1_u",
        "transfer",
        "female",
        "asian",
        "latx",
        "white",
        "othereth",
    ]
    sorterIndex = dict(zip(varlist, range(len(varlist))))
    dfht["rank"] = dfht["depvar"].map(sorterIndex)
    dfht = dfht.sort_values(["rank", "stat"]).reset_index(drop=True)
    dfht = dfht.drop(columns=["rank"])

    # rename depvar with actual names
    dfht["depvar"] = dfht.depvar.apply(lambda x: name_dict.get(x))

    # clear all N except last
    dfht = dfht.loc[(dfht.stat != "3N") | (dfht.index == dfht.index.max())]
    dfht.loc[dfht.stat == "3N", "depvar"] = "Observations"

    # remove every other depvar
    dfht.loc[dfht.stat == "2stderr", "depvar"] = ""

    # two manual renames
    dfht.loc[dfht.depvar == "Videos watched", "depvar"] = "Pretreatment videos"
    dfht.loc[dfht.depvar == "Videos, unique", "depvar"] = "Pretreatment videos, unique"

    # drop stat, rename 'depvar'
    dfht = dfht.drop(columns=["stat"])
    dfht.rename(columns={"depvar": "Interaction Variable"}, inplace=True)


    # translate to tex

    column_format = "m{0.40\\linewidth} *{2}{>{\\centering\\arraybackslash}m{0.12\\linewidth}}"
    caption = "Heterogeneous Effects of Treatment"
    label = "het_table"

    # table notes
    note_het = "This table reports estimates for $\\beta_2$ from Equation \\ref{eq:het_spec}."
    note = combine_notes([note_het, note_scorestd])

    table = convert_to_latex(
        dfht, column_format, caption, label, note, scalewidth=False, observations=True
    )

    # space out variables
    for v in [x for x in dfht["Interaction Variable"].unique() if x not in ["", "Observations"]]:
        table = table.replace(v + " &", "\\customlinespace " + v + " &")

    # write to tex file
    with open(f"{TEX}/het_table.tex", "w") as tf:
        tf.write(table)

    # ### Table: Anderson-Rubin confidence sets

    # Build Anderson-Rubin confidence sets table from Stata weak_iv.do output

    weak_iv_path = f"{DATA_GEN}/weak_iv.csv"
    if not os.path.exists(weak_iv_path):
        print(f"Warning: {weak_iv_path} not found. Skipping arci_table.tex.")
    else:
        df_wiv = pd.read_csv(weak_iv_path)

        exam_labels = {"mid2": "Midterm 2 score", "final": "Final exam score"}
        endog_labels = {"videos": "10 unique videos", "duration": "1 hour videos"}

        def _fmt_cset(raw):
            nums = re.findall(r"-?\d*\.\d+|-?\d+", str(raw))
            if len(nums) == 2:
                return f"[{float(nums[0]):.3f}, {float(nums[1]):.3f}]"
            return str(raw).strip()

        rows = []
        for exam in ["mid2", "final"]:
            for endog in ["videos", "duration"]:
                sub = df_wiv[(df_wiv["exam"] == exam) & (df_wiv["endog"] == endog)]
                if len(sub) == 1:
                    rows.append((
                        exam_labels[exam],
                        endog_labels[endog],
                        _fmt_cset(sub.iloc[0]["ar_cset"]),
                    ))

        body = "\n".join(
            f"\t\t\t\t{out:<16s} & {end:<19s} & {ci:<17s} \\\\"
            for out, end, ci in rows
        )
        arci_tex = (
            "\\begin{spacing}{1.0}\n"
            "\t\\begin{table}\n"
            "\t\t\\centering\n"
            "\t\t\\caption{Anderson-Rubin Confidence Sets}\n"
            "\t\t\\label{tab:arci_table}\n"
            "\t\t\\begin{threeparttable}\n"
            "\t\t\t\\begin{tabular}{lcc}\n"
            "\t\t\t\t\\toprule\n"
            "\t\t\t\tOutcome Variable & Endogenous Variable & Anderson-Rubin CI \\\\\n"
            "\t\t\t\t\\midrule\n"
            f"{body}\n"
            "\t\t\t\t\\bottomrule\n"
            "\t\t\t\\end{tabular}\n"
            "\t\t\t\\Fignote{This table displays Anderson-Rubin confidence sets at the 95\\% confidence level for the 2SLS estimator $\\hat{\\gamma}$ from Equation \\ref{eq:secondstage_spec} including year dummies and first midterm score as controls.\n"
            "\t\t\t\tOutcomes are measured in standard deviations.\n"
            "\t\t\t\tInstrumented endogenous variables are measured in 10s of unique videos or hours of unique content.\n"
            "\t\t\t}\n"
            "\t\t\\end{threeparttable}\n"
            "\t\\end{table}\n"
            "\\end{spacing}\n"
        )
        with open(f"{TEX}/arci_table.tex", "w") as tf:
            tf.write(arci_tex)

def build_referee_tables():
    """Build referee-requested tables (JEE revision)."""
    # ## Figure A1 by year: attrition by treatment arm

    attr = pd.read_csv(f"{DATA_GEN}/attrition_by_year.csv")


    def pct(n, base):
        return f"{int(n)} ({100 * n / base:.1f}\\%)" if base else str(int(n))


    def pval_text(p):
        return "no attrition" if pd.isna(p) else f"$p={p:.2f}$"


    # Above-median midterm 1 takers before removing minors and opt-outs; not in
    # the Stata export. Counted from the fall 2018 and fall 2019 treatment
    # assignment files.
    ABOVE_MEDIAN_ASSIGNED = {"2018": 216, "2019": 209}
    ABOVE_MEDIAN_ASSIGNED["pooled"] = sum(ABOVE_MEDIAN_ASSIGNED.values())

    def below_assigned(sample):
        a = attr[attr["sample"] == sample].set_index("arm")
        return int(a.loc["1"].assigned + a.loc["2"].assigned)

    def tree(sample, top_label, above_label, level2_dist="10mm"):
        a = attr[attr["sample"] == str(sample)].set_index("arm")
        r = {k: a.loc[k] for k in ["0", "1", "2"]}
        p = a.loc["pvalue"]
        below = int(r["1"].assigned + r["2"].assigned)

        def chain(row, first_label, tag):
            base = row.observed_status
            nodes = [
                first_label,
                str(int(row.consented)),
                f"{int(base)} (100\\%)",
                pct(row.took_mid2, base),
                pct(row.took_final, base),
                pct(row.took_100b, base),
            ]
            names = [f"{tag}3", f"{tag}4", f"{tag}45", f"{tag}5", f"{tag}6", f"{tag}7"]
            out = ""
            for nm, txt in zip(names, nodes):
                out += f"child {{node ({nm}) {{{txt}}}\n"
            return out + "}" * len(nodes)

        t = (
            "\t\t\\begin{tikzpicture}[\n"
            "\t\t\tnode distance=0mm, level distance=10mm,\n"
            "\t\t\tevery node/.style = {shape=rectangle, draw=none, text width = 30mm, minimum height = 1em, align=center},\n"
            "\t\t\tpval/.style = {shape=rectangle, draw=none, inner sep=0mm, outer sep=0mm, minimum height=1em, align=left, text width=20mm},\n"
            "\t\t\tcmnt/.style = {shape=rectangle, draw=none, inner sep=0mm, outer sep=0mm, minimum height=1em, align=right},\n"
            "\t\t\tlevel 1/.style = {sibling distance=50mm, level distance=15mm},\n"
            f"\t\t\tlevel 2/.style = {{sibling distance=35mm, level distance={level2_dist}}}, edge from parent fork down, edge from parent/.style = {{draw, semithick, -latex}},\n"
            "\t\t\t]\n"
            f"\t\t\t\\node [text width = 50mm] (L1) {{{top_label}}}\n"
            f"\t\t\tchild {{node (L2) {{{above_label}}}\n"
            + chain(r["0"], "\\textit{Above median}", "L")
            + "}\n"
            f"\t\t\tchild {{node {{Below or equal to median: {below}}}\n"
            + chain(r["1"], f"\\textit{{Control}}: {int(r['1'].assigned)}", "C")
            + "\n"
            + chain(r["2"], f"\\textit{{Incentive}}: {int(r['2'].assigned)}", "R")
            + "};\n"
            "\t\t\t\\node[cmnt] (l7) [left=3mm of L7] {Took Micro B};\n"
            "\t\t\t\\node[cmnt] (l6) [left=3mm of L6] {Took Final Exam};\n"
            "\t\t\t\\node[cmnt] (l5) [left=3mm of L5] {Took Midterm 2};\n"
            "\t\t\t\\node[cmnt] (l45) [left=3mm of L45] {Observed \\\\ treatment status};\n"
            "\t\t\t\\node[cmnt] (l4) [left=3mm of L4] {Opt-in and \\\\ 18 or older};\n"
            "\t\t\t\\node[cmnt] (l3) [left=3mm of L3] {Treatment arm};\n"
            "\t\t\t\\node[cmnt] (l2) [left=of l3.east |- L2.west] {Midterm score};\n"
            f"\t\t\t\\node[pval] (r5) [right=3mm of R5] {{{pval_text(p.took_mid2)}}};\n"
            f"\t\t\t\\node[pval] (r6) [right=3mm of R6] {{{pval_text(p.took_final)}}};\n"
            f"\t\t\t\\node[pval] (r7) [right=3mm of R7] {{{pval_text(p.took_100b)}}};\n"
            "\t\t\\end{tikzpicture}\n"
        )
        return t


    fig = (
        "\\begin{figure}[p]\n\t\\begin{center}\n"
        "\t\t\\caption{Attrition by Treatment Arm and Year}\n"
        "\t\t\\label{fig:attritchart_year}\n\t\t\\footnotesize\n"
        "\t\t\\textbf{Panel A: 2018}\\\\[1mm]\n" + tree(
            2018,
            f"Midterm 1 takers, 2018: {ABOVE_MEDIAN_ASSIGNED['2018'] + below_assigned('2018')}",
            f"Above median: {ABOVE_MEDIAN_ASSIGNED['2018']}",
        ) + "\n\t\t\\bigskip\n\n"
        "\t\t\\textbf{Panel B: 2019}\\\\[1mm]\n" + tree(
            2019,
            f"Midterm 1 takers, 2019: {ABOVE_MEDIAN_ASSIGNED['2019'] + below_assigned('2019')}",
            f"Above median: {ABOVE_MEDIAN_ASSIGNED['2019']}",
        ) + "\n"
        "\\end{center}\n\t\t{\\footnotesize \\noindent \\textit{Note}: Percentages in parentheses are, at each stage, the share of students who observed their treatment status "
        "who took the second midterm, took the final exam, or enrolled in Micro B, calculated separately for each treatment arm and year. "
        "The p-values are from a two-sample t-test of the equality of attrition rates between the "
        "\\textit{Control} and \\textit{Incentive} arms at each stage within year.\\par}\n"
        "\\end{figure}\n"
    )
    write_tex(TEX, "attrite_chart_by_year", fig)

    # ## Pooled attrition chart (main text)

    fig = (
        "\\begin{figure}[t]\n\t\\begin{center}\n"
        "\t\t\\caption{Attrition by Treatment Arm}\n"
        "\t\t\\label{fig:attritchart}\n\t\t\\footnotesize\n"
        + tree(
            "pooled",
            "Midterm 1 takers \\\\ eligible for experiment: "
            f"{ABOVE_MEDIAN_ASSIGNED['pooled'] + below_assigned('pooled')}",
            f"Above median: {ABOVE_MEDIAN_ASSIGNED['pooled']}",
            level2_dist="15mm",
        )
        + "\\end{center}\n\t\t{\\footnotesize \\noindent \\textit{Note}: Percentages in parentheses are, at each stage, the share of students who observed their treatment status "
        "who took the second midterm, took the final exam, or enrolled in Micro B, calculated separately for each treatment arm. "
        "The p-values are from a two-sample t-test of the equality of attrition rates between the "
        "\\textit{Control} and \\textit{Incentive} arms at each stage.\\par}\n"
        "\\end{figure}\n"
    )
    write_tex(TEX, "attrite_chart", fig)

    # ## Table A1 by year: balance, exam-taker sample

    bal = pd.read_csv(f"{DATA_GEN}/balance_table_data_by_year.csv")

    BAL_ORDER = [
        ("mid1scorestd", "Midterm 1 score"),
        ("prev_cumgpa", "Cumulative GPA"),
        ("prev_cumgpa_unobs", "No cum. GPA"),
        ("mathquizstd", "Math quiz score"),
        ("pset_pre", "Tutoring visits"),
        ("videos_mid1", "Videos watched"),
        ("videos_mid1_u", "Videos, unique"),
        ("duration_mid1", "Hours videos"),
        ("duration_mid1_u", "Hours videos, unique"),
        ("asian", "Asian"),
        ("latx", "Latinx"),
        ("white", "White"),
        ("othereth", "Other ethnicity"),
        ("female", "Female"),
        ("male", "Male"),
        ("transfer", "Transfer"),
    ]


    def balance_table(year):
        b = bal[(bal.year == year) & (bal.bothpairs == 0)].set_index(["exam", "depvar", "arm"])
        lines = []
        for v, name in BAL_ORDER:
            means, ses = [], []
            for exam in ["mid2", "final"]:
                row = [b.loc[(exam, v, a)] for a in [0, 1, 2]]
                if "pvalue" in b.columns and pd.notna(row[2]["pvalue"]):
                    p = row[2]["pvalue"]
                else:
                    p = get_p_value(
                        row[2]["mean"],
                        row[1]["mean"],
                        row[2]["stderr"],
                        row[1]["stderr"],
                        row[2]["N"],
                        row[1]["N"],
                    )
                means += [f"{r['mean']:.3f}" for r in row] + [star_p(p)]
                ses += [f"({r['stderr']:.3f})" for r in row] + [""]
            lines.append(f"\\customlinespace {name} & " + " & ".join(means) + " \\\\")
            lines.append(" & " + " & ".join(ses) + " \\\\")
        nobs = []
        for exam in ["mid2", "final"]:
            nobs += [str(int(b.loc[(exam, "mid1scorestd", a)]["N"])) for a in [0, 1, 2]] + [""]
        return (
            "\\begin{spacing}{1.0} \n"
            f"\\begin{{table}} \\centering \\caption{{Balance Test, Exam Taker Sample, {year}}} \n"
            f"\\label{{tab:balance_table_takers_{year}}} \n"
            "\\resizebox{\\linewidth}{!}{% \n\\begin{threeparttable} \n"
            "\\begin{tabular}{m{0.25\\linewidth} *{8}{>{\\centering\\arraybackslash}m{0.095\\linewidth}}}\n"
            "\\toprule \n & \\multicolumn{3}{c}{Midterm 2 Sample} & P-values & "
            "\\multicolumn{3}{c}{Final Exam Sample}  & P-values  \\\\ \n"
            "\\cmidrule(lr){2-4}\\cmidrule(lr){6-8} \n"
            "Variable & Above Median & Control & Incentive & (3) - (2) & Above Median & Control & "
            "Incentive & (6) - (5) \\\\\n\\midrule\n"
            + "\n".join(lines)
            + "\n\\midrule \nObservations & "
            + " & ".join(nobs)
            + " \\\\\n\\bottomrule\n\\end{tabular}\n"
            f"\\Fignote{{This table includes all students in {year} who completed the second midterm and final "
            "exams. It reproduces Appendix Table~\\ref{tab:balance_table_takers} separately by year. Descriptions of each "
            "variable can be found in Appendix Table \\ref{tab:controlvars_desc}. \\textit{Female} and \\textit{Male} are "
            "coded zero for students who do not report a gender. \\textit{P-values} are reported for the Welch's "
            "t-test of equal means between the \\textit{Control} and \\textit{Incentive} arms. \\Regnote} \n"
            "\\end{threeparttable}}\n\\end{table} \n\\end{spacing}\n"
        )


    for y in YEARS:
        write_tex(TEX, f"balance_table_takers_{y}", balance_table(y))

    # ## Exam score summary statistics by year

    es = pd.read_csv(f"{DATA_GEN}/exam_stats_by_year.csv")
    lines = []
    for g in ["All students", "Above median", "Control", "Incentive"]:
        gname = f"\\textit{{{g}}}" if g != "All students" else g
        lines.append(f"\\multicolumn{{9}}{{l}}{{\\textbf{{{gname}}}}} \\\\")
        for e in ["Midterm 1", "Midterm 2", "Final exam"]:
            cells = []
            for y in YEARS:
                r = es[(es.year == y) & (es.group == g) & (es.exam == e)].iloc[0]
                cells += [f"{r['mean']:.1f}", f"{r['median']:.1f}", f"{r['sd']:.1f}", str(int(r.N))]
            lines.append(f"\\indentrow{{{e}}} & " + " & ".join(cells) + " \\\\")
        lines.append("\\customlinespace")
    table = (
        "\\begin{spacing}{1.0} \n"
        "\\begin{table} \\centering \\caption{Exam Scores by Year} \n"
        "\\label{tab:exam_stats_by_year} \n\\begin{threeparttable} \n"
        "\\begin{tabular}{l *{8}{c}}\n\\toprule \n"
        " & \\multicolumn{4}{c}{2018} & \\multicolumn{4}{c}{2019} \\\\ \n"
        "\\cmidrule(lr){2-5}\\cmidrule(lr){6-9} \n"
        " & Mean & Median & SD & N & Mean & Median & SD & N \\\\ \n\\midrule\n"
        + "\n".join(lines[:-1])
        + "\n\\bottomrule\n\\end{tabular}\n"
        "\\Fignote{Raw exam scores in percent of points possible, for all students in the analysis sample who "
        "sat each exam. Midterm 1 preceded treatment assignment; \\textit{Above median}, \\textit{Control}, and "
        "\\textit{Incentive} are defined by midterm 1 score within year. Elsewhere in the paper, scores are "
        "standardized within year using the \\textit{Control} arm's mean and standard deviation.} \n"
        "\\end{threeparttable}\n\\end{table} \n\\end{spacing}\n"
    )
    write_tex(TEX, "exam_stats_by_year", table)

    # ## Tables 4 and 5 with credit-eligible video counts

    fs = pd.read_csv(f"{DATA_GEN}/credit_firststage_coeffs.csv")
    ss = pd.read_csv(f"{DATA_GEN}/credit_secondstage_coeffs.csv")

    NOTE_4MODELS = (
        "Model (1) contains linear controls for midterm 1 score and year; (2) is the difference in means and "
        "standard errors calculated using the repeated sampling framework of Neyman (1923); (3) and (4) use the "
        "post-double-selection (PDS) procedure of \\textcite{bch2014a} to select control variables then estimate "
        "treatment effects and standard errors. Models (2) and (4) include only students whose matched pair did "
        "not attrite from the experiment."
    )
    NOTE_CREDIT = (
        "Video measures count only credit-eligible video openings: a video counts only if the student did not "
        "open another video before this one could have been watched in its entirety at 2x playback speed "
        "(allowing one minute for timestamp rounding), consistent with what \\textit{Incentive} students were told was required for credit. "
        "The rule is applied identically to all arms."
    )
    FOOT = [
        ("Treatment assignment controls", ["Yes", "No", "Yes", "Yes"]),
        ("Demographic controls", ["No", "No", "Yes", "Yes"]),
        ("Pair fixed effects", ["No", "No", "No", "Yes"]),
    ]


    def row_pair(label, sub, nd, mean=None):
        sub = sub.sort_values("model")
        b = [fmt_beta(r.beta, r.se, nd) for r in sub.itertuples()]
        s = [f"({r.se:.{nd}f})" for r in sub.itertuples()]
        lead = [f"{mean:.2f}"] if mean is not None else []
        blank = [""] if mean is not None else []
        return (
            f"\\customlinespace \\indentrow{{{label}}} & "
            + " & ".join(lead + b)
            + " \\\\\n"
            + " & "
            + " & ".join(blank + s)
            + " \\\\\n"
        )


    # Table 4 analogue
    body = ""
    for exam, letter, title in [("mid2", "A", "By Midterm 2"), ("final", "B", "By Final Exam")]:
        if letter == "B":
            body += "\\midrule \n"
        body += f"\\multicolumn{{6}}{{l}}{{\\textbf{{Panel {letter}}}: {title}}} \\\\ \n"
        sub = fs[fs.exam == exam]
        for m in ["Videos", "Unique videos", "Hours of videos", "Hours of unique videos"]:
            r = sub[sub.measure == m]
            body += row_pair(m, r, 2, mean=r.meanctrl.iloc[0])
        n = sub[sub.measure == "Videos"].sort_values("model").N.astype(int).astype(str).tolist()
        body += "\\midrule \nObservations & & " + " & ".join(n) + " \\\\\n"
    for lab, vals in FOOT:
        body += f"{lab} & & " + " & ".join(vals) + " \\\\\n"
    t4 = (
        "\\begin{spacing}{1.0} \n"
        "\\begin{table} \\centering \\caption{Effects of Grade Incentive on Credit-Eligible Video Watching} \n"
        "\\label{tab:firststage_credit} \n\\begin{threeparttable} \n"
        "\\begin{tabular}{m{0.35\\linewidth} *{5}{>{\\centering\\arraybackslash}m{0.1\\linewidth}}}\n\\toprule\n"
        " & Control Mean & (1) & (2) & (3) & (4) \\\\\n\\midrule\n"
        + body
        + "\\bottomrule\n\\end{tabular}\n"
        "\\Fignote{This table replicates Table~\\ref{tab:firststage_table} using credit-eligible video measures. "
        + NOTE_CREDIT
        + " "
        + NOTE_4MODELS
        + " \\textit{Control Mean} is the mean for the Control students included in models (1) and (3). \\Regnote}\n"
        "\\end{threeparttable}\n\\end{table} \n\\end{spacing}\n"
    )
    write_tex(TEX, "firststage_credit", t4)

    # Table 5 analogue
    labels = {
        "RF": "RF: Incentive",
        "2SLS_videos10": "2SLS: 10 unique videos",
        "2SLS_hours": "2SLS: 1 hour of unique videos",
    }
    body = ""
    for exam, letter, title in [("mid2", "A", "Midterm 2 score"), ("final", "B", "Final exam score")]:
        if letter == "B":
            body += "\\midrule \n"
        body += f"\\multicolumn{{5}}{{l}}{{\\textbf{{Panel {letter}}}: {title}}} \\\\ \n"
        sub = ss[ss.exam == exam]
        for k, lab in labels.items():
            body += row_pair(lab, sub[sub.row == k], 3)
        n = sub[sub.row == "RF"].sort_values("model").N.astype(int).astype(str).tolist()
        body += "\\midrule \nObservations & " + " & ".join(n) + " \\\\\n"
    for lab, vals in FOOT:
        body += f"{lab} & " + " & ".join(vals) + " \\\\\n"
    t5 = (
        "\\begin{spacing}{1.0} \n"
        "\\begin{table} \\centering \\caption{Effects of Credit-Eligible Videos on Grades} \n"
        "\\label{tab:secondstage_credit} \n\\begin{threeparttable} \n"
        "\\begin{tabular}{m{0.35\\linewidth} *{4}{>{\\centering\\arraybackslash}m{0.1\\linewidth}}}\n\\toprule\n"
        " & (1) & (2) & (3) & (4) \\\\\n\\midrule\n" + body + "\\bottomrule\n\\end{tabular}\n"
        "\\Fignote{This table replicates Table~\\ref{tab:secondstage_table} using credit-eligible video measures "
        "as the endogenous variable. The reduced-form (\\textit{RF}) estimates do not depend on the video measure "
        "and are identical to Table~\\ref{tab:secondstage_table}. "
        + NOTE_CREDIT
        + " Test scores are measured in standard deviation units. "
        + NOTE_4MODELS
        + " \\Regnote}\n"
        "\\end{threeparttable}\n\\end{table} \n\\end{spacing}\n"
    )
    write_tex(TEX, "secondstage_credit", t5)

    # ## Micro B enrollment by year

    took = pd.read_csv(f"{DATA_GEN}/microb_took_by_year.csv")

    PANELS = [("2018", "A", "2018"), ("2019", "B", "2019"), ("pooled", "C", "Pooled"), ("diff", "D", "Difference, 2019 $-$ 2018")]


    def cells(sub, nd):
        sub = sub.sort_values("model")
        return [fmt_beta(r.beta, r.se, nd) for r in sub.itertuples()], [f"({r.se:.{nd}f})" for r in sub.itertuples()]


    # Table 8 'Took Micro B' row by year
    body = ""
    for samp, letter, title in PANELS:
        if letter != "A":
            body += "\\midrule \n"
        body += f"\\multicolumn{{6}}{{l}}{{\\textbf{{Panel {letter}}}: {title}}} \\\\ \n"
        sub = took[took["sample"] == samp].sort_values("model")
        b, s = cells(sub, 3)
        body += "\\customlinespace \\indentrow{Took Micro B} & " + " & ".join(b) + " \\\\\n & " + " & ".join(s) + " \\\\\n"
        if samp == "diff":
            body += "\\indentrow{P-value} & " + " & ".join(f"{p:.2f}" for p in sub.pvalue) + " \\\\\n"
        else:
            body += "\\indentrow{Control mean} & " + " & ".join(f"{m:.2f}" for m in sub.meanctrl) + " \\\\\n"
            body += "\\indentrow{Observations} & " + " & ".join(str(int(n)) for n in sub.N) + " \\\\\n"
    FOOT5 = [
        ("Treatment assignment controls", ["Yes", "No", "Yes", "Yes", "Yes"]),
        ("Demographic controls", ["No", "No", "Yes", "Yes", "No"]),
        ("Pair fixed effects", ["No", "No", "No", "Yes", "No"]),
        ("Sample", ["Final", "Final", "Final", "Final", "All"]),
    ]
    body += "\\midrule \n"
    for lab, vals in FOOT5:
        body += f"{lab} & " + " & ".join(vals) + " \\\\\n"
    t = (
        "\\begin{spacing}{1.0} \n"
        "\\begin{table} \\centering \\caption{Effects of Treatment on Micro B Enrollment by Year} \n"
        "\\label{tab:microb_took_by_year} \n\\begin{threeparttable} \n"
        "\\begin{tabular}{m{0.35\\linewidth} *{5}{>{\\centering\\arraybackslash}m{0.1\\linewidth}}}\n\\toprule\n"
        " & (1) & (2) & (3) & (4) & (5) \\\\\n\\midrule\n"
        + body
        + "\\bottomrule\n\\end{tabular}\n"
        "\\Fignote{This table re-estimates the \\textit{Took Micro B} row of Table~\\ref{tab:spillover_100b} separately "
        "by year; the year control is dropped within year. Models (1)--(4) are as in Table~\\ref{tab:spillover_100b} and use "
        "students who took the Micro A final exam (\\textit{Final}); models (2) and (4) include only students whose matched "
        "pair did not attrite. Model (5) is model (1) estimated on all students who saw their treatment assignment "
        "(\\textit{All}), coding students who did not enroll as zero; this is the population in "
        "Appendix Figure~\\ref{fig:attritchart_year}. Panel C reproduces Table~\\ref{tab:spillover_100b} and adds model (5). "
        "Panel D reports the difference between the 2019 and 2018 estimates; because the years are independent samples, its "
        "standard error is $\\sqrt{se_{2018}^2 + se_{2019}^2}$. \\textit{Control mean} is the enrollment rate of "
        "\\textit{Control} students in each estimation sample. \\Regnote}\n"
        "\\end{threeparttable}\n\\end{table} \n\\end{spacing}\n"
    )
    write_tex(TEX, "microb_took_by_year", t)


def main():
    parser = argparse.ArgumentParser(description="Generate paper LaTeX tables.")
    parser.add_argument(
        "--only",
        choices=["all", "main", "referee"],
        default="all",
        help="Which table set to build (default: all).",
    )
    args = parser.parse_args()
    if args.only in ("all", "main"):
        build_main_tables()
    if args.only in ("all", "referee"):
        build_referee_tables()


if __name__ == "__main__":
    main()
