#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><span><a href="#Stuff-shared-across-tables" data-toc-modified-id="Stuff-shared-across-tables-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Stuff shared across tables</a></span><ul class="toc-item"><li><span><a href="#Import-data" data-toc-modified-id="Import-data-1.1"><span class="toc-item-num">1.1&nbsp;&nbsp;</span>Import data</a></span></li><li><span><a href="#Variable-descriptions" data-toc-modified-id="Variable-descriptions-1.2"><span class="toc-item-num">1.2&nbsp;&nbsp;</span>Variable descriptions</a></span></li><li><span><a href="#Common-captions" data-toc-modified-id="Common-captions-1.3"><span class="toc-item-num">1.3&nbsp;&nbsp;</span>Common captions</a></span></li><li><span><a href="#Common-funtions" data-toc-modified-id="Common-funtions-1.4"><span class="toc-item-num">1.4&nbsp;&nbsp;</span>Common funtions</a></span></li></ul></li><li><span><a href="#Covariate-balance" data-toc-modified-id="Covariate-balance-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Covariate balance</a></span></li><li><span><a href="#Post-double-selection-control-variable-selection" data-toc-modified-id="Post-double-selection-control-variable-selection-3"><span class="toc-item-num">3&nbsp;&nbsp;</span>Post-double-selection control variable selection</a></span><ul class="toc-item"><li><span><a href="#Table:-description-of-eligible-control-vars" data-toc-modified-id="Table:-description-of-eligible-control-vars-3.1"><span class="toc-item-num">3.1&nbsp;&nbsp;</span>Table: description of eligible control vars</a></span></li><li><span><a href="#Table:-control-variables-for-ITT-PDS" data-toc-modified-id="Table:-control-variables-for-ITT-PDS-3.2"><span class="toc-item-num">3.2&nbsp;&nbsp;</span>Table: control variables for ITT PDS</a></span></li><li><span><a href="#Table:-control-variables-for-LATE-PDS" data-toc-modified-id="Table:-control-variables-for-LATE-PDS-3.3"><span class="toc-item-num">3.3&nbsp;&nbsp;</span>Table: control variables for LATE PDS</a></span></li></ul></li><li><span><a href="#Coefficient-estimates---below-cutoff-experiment" data-toc-modified-id="Coefficient-estimates---below-cutoff-experiment-4"><span class="toc-item-num">4&nbsp;&nbsp;</span>Coefficient estimates - below cutoff experiment</a></span><ul class="toc-item"><li><span><a href="#Table:-first-stage" data-toc-modified-id="Table:-first-stage-4.1"><span class="toc-item-num">4.1&nbsp;&nbsp;</span>Table: first stage</a></span></li><li><span><a href="#Table:-second-stage" data-toc-modified-id="Table:-second-stage-4.2"><span class="toc-item-num">4.2&nbsp;&nbsp;</span>Table: second stage</a></span></li><li><span><a href="#Table:-spillovers-to-grades" data-toc-modified-id="Table:-spillovers-to-grades-4.3"><span class="toc-item-num">4.3&nbsp;&nbsp;</span>Table: spillovers to grades</a></span></li><li><span><a href="#Table:-spillovers-to-studying" data-toc-modified-id="Table:-spillovers-to-studying-4.4"><span class="toc-item-num">4.4&nbsp;&nbsp;</span>Table: spillovers to studying</a></span></li><li><span><a href="#Table:-spillovers-to-subsequent-quarter" data-toc-modified-id="Table:-spillovers-to-subsequent-quarter-4.5"><span class="toc-item-num">4.5&nbsp;&nbsp;</span>Table: spillovers to subsequent quarter</a></span></li></ul></li><li><span><a href="#Other-tables" data-toc-modified-id="Other-tables-5"><span class="toc-item-num">5&nbsp;&nbsp;</span>Other tables</a></span><ul class="toc-item"><li><span><a href="#Table:-heterogeneity" data-toc-modified-id="Table:-heterogeneity-5.1"><span class="toc-item-num">5.1&nbsp;&nbsp;</span>Table: heterogeneity</a></span></li></ul></li></ul></div>

# ## Stuff shared across tables

# ### Import data

import re

import numpy as np
import pandas as pd
from scipy.stats import t

from table_utils import (
    add_stars,
    stringify_stats,
    convert_to_latex,
    combine_notes,
    insert_panel,
    add_indents,
    get_p_value,
    star_p,
)

pd.options.display.max_columns = 50
pd.options.display.max_rows = 100
pd.options.display.max_colwidth = 100


df = pd.read_csv("../data/generated/pds_coeffs.csv")
print(df.dtypes)
print(df.isnull().sum())
df.head()


dff = pd.read_csv("../data/generated/itt_coeffs.csv")
print(dff.dtypes)
print(dff.isnull().sum())
dff.head()


dflate = pd.read_csv("../data/generated/lates_coeffs.csv")
print(dflate.dtypes)
print(dflate.isnull().sum())
dflate.head()


dfiv = pd.read_csv("../data/generated/pds_iv_coeffs.csv")
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

# variables appearing in which table
table_dict = {
    "attendance": 4,
    "duration_final": 1,
    "duration_final_u": 1,
    "duration_mid2": 1,
    "duration_mid2_u": 1,
    "duration_b": 5,
    "duration_u_b": 5,
    "final_100b": 5,
    "finalscorestd": 2,
    "gpa_econ_sans100a": 3,
    "gpa_letter": 3,
    "gpa_letter_sans100a": 3,
    "gpa_letter_sansecon": 3,
    "letter_option": 3,
    "mid1bscorestd": 5,
    "mid2bscorestd": 5,
    "mid2scorestd": 2,
    "nclass_letter": 3,
    "nclass_np": 3,
    "nclass_p": 3,
    "nclass_pnp": 3,
    "nclass_w": 3,
    "pclass_letter": 3,
    "pclass_pnp": 3,
    "piazza_answers": 4,
    "piazza_daysonline": 4,
    "piazza_questions": 4,
    "piazza_views": 4,
    "pset_post": 4,
    "took100b": 5,
    "units_letter": 3,
    "units_pnp": 3,
    "units_w": 3,
    "videos_final": 1,
    "videos_final_u": 1,
    "videos_mid2": 1,
    "videos_mid2_u": 1,
    "videos_b": 5,
    "videos_u_b": 5,
    "winter_gpa_econ_sans100a": 5,
    "winter_gpa_letter": 5,
    "winter_gpa_letter_sans100a": 5,
    "winter_gpa_letter_sansecon": 5,
    "winter_nclass_letter": 5,
    "winter_nclass_np": 5,
    "winter_nclass_p": 5,
    "winter_nclass_pnp": 5,
    "winter_nclass_w": 5,
    "winter_pclass_letter": 5,
    "winter_pclass_pnp": 5,
    "winter_units_letter": 5,
    "winter_units_pnp": 5,
    "winter_units_w": 5,
}


# ### Common captions

# list named strings to be included in the captions of multiple tables.


# notes on model specification

note_ittspec = "This table reports coefficients on $Incentive_i$ from Equations \\ref{eq:itt_spec}."

note_bothspec = (
    "This table reports coefficients on $Incentive_i$ from Equation \\ref{eq:itt_spec} "
    + "(Reduced Form, \\textit{RF}) and $\\hat{Video_i}$ from Equation \\ref{secondstage_spec} "
    + "(Two-Stage Least Squares, \\textit{2SLS})."
)

note_4models = (
    "Model (1) contains linear controls for midterm 1 score and year; (2) is "
    + "the difference in means and standard errors calculated using the repeated sampling "
    + "framework of Neyman (1923); (3) and (4) use the post-double-selection (PDS) procedure of "
    + "\\textcite{bch2014a} to select control variables then estimate treatment effects and "
    + "standard errors. The control variables selected using PDS are listed in Table "
    + "\\ref{tab:controlvars_selected_itt}. Models (2) and (4) include only students whose matched-"
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
    dfb = pd.concat([df.copy().drop(columns=["ctrls"]), dff.copy()])
    dfb = dfb[dfb["model"] != "itt_zeros"]
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
    dfsub.loc[len(dfsub)] = ["Pair Fixed Effects",            "", "No",  "No",  "No",  "Yes"]

    dfsub.rename(columns={"depvar": "", "ctrlmean": "Control Mean",
                           "ITT": "(1)", "Neyman": "(2)", "All": "(3)", "FEs": "(4)"}, inplace=True)
    return dfsub


# get_p_value and star_p are imported from table_utils


# ## Covariate balance
# 
# Create table showing balance across treatment arms on observables

# Read in data

dfbal = pd.read_csv("../data/generated/balance_table_data.csv")

# stack mean, stderr, N
dfbal = dfbal.melt(["exam", "depvar", "arm", "bothpairs"], var_name="stat", value_name="value")
dfbal.stat.replace({"mean": "1mean", "stderr": "2stderr", "N": "3N"}, inplace=True)

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
dfbal.insert(6, "p_all", 0)
dfbal.insert(10, "p_takers", 0)
dfbal.insert(13, "p_both", 0)

samples = ["all", "takers", "both"]

for i in range(int(len(dfbal) / 3)):
    rown = i * 3
    for k in samples:
        meant = dfbal.loc[rown, "treat_" + k]
        meanc = dfbal.loc[rown, "ctrl_" + k]
        stderrt = dfbal.loc[rown + 1, "treat_" + k]
        stderrc = dfbal.loc[rown + 1, "ctrl_" + k]
        Nt = dfbal.loc[rown + 2, "treat_" + k]
        Nc = dfbal.loc[rown + 2, "ctrl_" + k]
        dfbal.loc[3 * i, "p_" + k] = get_p_value(meant, meanc, stderrt, stderrc, Nt, Nc)

# get stars
for k in samples:
    dfbal["p_" + k] = dfbal.apply(lambda x: star_p(x["p_" + k]) if x["stat"] == "1mean" else "", 1)

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

display(dfbal)


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
caption = "Balance test, exam taker sample"
label = "balance_table_takers"
note = (
    "This table includes all students who completed the second midterm and final exams. "
    + "Descriptions of each variable can be found in Table \\ref{controlvars_desc}. "
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
with open("../tex/tables/" + label + ".tex", "w") as tf:
    tf.write(k)


# the full sample is the same for mid2 and final, so only keep one copy

btable_all = dfbal.loc[dfbal.exam == "mid2"].drop(columns=["exam"]).iloc[:, 0:5]

# convert to latex

column_format = "m{0.25\\linewidth} *{5}{>{\\centering\\arraybackslash}m{0.095\\linewidth}}"
caption = "Balance test, full sample"
label = "balance_table_all"
note = (
    "This table includes all students who saw their treatment assignment. "
    + "Descriptions of each variable can be found in Table \\ref{controlvars_desc}. "
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

# write to tex file
with open("../tex/tables/" + label + ".tex", "w") as tf:
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
caption = "Baseline balance test, matched pairs"
label = "balance_table_matched"
note = (
    "This table includes all matched pairs who both complete the second midterm "
    + "or final exams. "
    + "Descriptions of each variable can be found in Table \\ref{controlvars_desc}. "
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
with open("../tex/tables/" + label + ".tex", "w") as tf:
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
display(dfc.head())

# translate to tex

column_format = r"p{0.3\linewidth} p{0.6\linewidth}"
caption = "Candidate control variables for post-double-selection"
label = "controlvars_desc"
note = (
    "\\textit{Midterm 1 score} and \\textit{Math quiz score} are measured in control standard deviations. "
    + "\\textit{Cumulative GPA} is measured on a 4.0 scale. Videos included in \\textit{Videos watched} and "
    + "\\textit{Hours videos} are unique course-relevant videos. The ethnicity variables are coded by university "
    + 'records: \\textit{Asian} includes "Chinese/Chinese American", "Vietnamese", "East Indian/Pakistani", '
    + '"Japanese/Japanese American", "Korean/Korean American", and "All other Asian/Asian American"; \\textit{Latinx} '
    + 'includes "Mexican/Mexican American", "Chicano", and "All other Spanish-American/Latino"; \\textit{White} '
    + 'includes "White/Caucasian"; and the omitted category inludes "African American/Black", "Pacific Islander", '
    + 'and "Not give/declined to state".'
)

table0 = convert_to_latex(
    dfc, column_format, caption, label, note, scalewidth=False, regnote=False
)

# write to tex file
with open("../tex/tables/controlvars_desc.tex", "w") as tf:
    tf.write(table0)


# ### Table: control variables for ITT PDS

# first reshape wide
dfw = df[["depvar", "model", "ctrls"]].set_index(["depvar", "model"]).unstack().reset_index()
dfw.columns = dfw.columns.droplevel(0)
dfw.columns = [
    "Dependent Variable",
    "Controls,\newline Fixed Effects",
    "Controls,\newline All Observations",
]
dfw = dfw.iloc[:, [0, 2, 1]]
dfw["og"] = dfw.iloc[:, 0].copy()
dfw.head()


ctrls = [x for x in dfw.iloc[:, 2].unique()]
ctrls += [x for x in dfw.iloc[:, 1].unique() if x not in ctrls]
ctrls = [str(x).split(" ") for x in ctrls]
ctrls = [j for i in ctrls for j in i]
ctrls = list(dict.fromkeys(ctrls))
for x in ["nan"]:
    ctrls.remove(x)
ctrls.sort()
ctrls


# Relabel variables with publication-ready names

for i in range(0, 3):
    print(i)
    dfw.iloc[:, i] = dfw.iloc[:, i].apply(
        lambda x: sorted([name_dict.get(k) or "None" for k in str(x).split(" ")]) or x
    )
    dfw.iloc[:, i] = dfw.iloc[:, i].apply(lambda x: ("\newline ").join(x))


# Add Table labels

# tables:
# 1 - first stage
# 2 - second stage
# 3 - spillovers to grades
# 4 - spillovers to study methods
# 5 - spillovers to following quarter

dfw["Table"] = dfw.og.apply(lambda x: f"Table {table_dict.get(x)!s}")
dfw.sort_values(["Table", dfw.columns[0]], inplace=True)

# set Table 'index' as first column
dfw["Table"] = dfw["Table"].mask(dfw["Table"].duplicated(), "")
dfw = dfw.loc[:, ["Table"] + [c for c in dfw.columns if c != "Table"]]
dfw.reset_index(inplace=True, drop=True)

display(dfw.head())


# TODO: get subset of models in paper

# get subset and convert to tex
table1vars = dfw.og.unique()  # change this
table1 = dfw.loc[dfw.og.isin(table1vars), dfw.columns[:-1]]

# shorten variable descriptions
for c in table1.columns[-2:]:
    table1.loc[table1[c].str.contains(", unique"), c] = table1.loc[
        table1[c].str.contains(", unique"), c
    ].apply(lambda x: x.replace(", unique", ""))

display(table1.head())


# convert to latex

column_format = (
    r"p{0.07\linewidth} >{\hangindent=1em}p{0.38\linewidth} "
    + r"p{0.22\linewidth} p{0.22\linewidth}"
)
caption = "ITT model controls selected via post-double-selection"
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
for i in range(2, 6):
    table1 = table1.replace(f"Table {i!s}", f"\\midrule \nTable {i!s}", 1)

# write to tex file
with open("../tex/tables/controlvars_selected_itt.tex", "w") as tf:
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
    "Controls,\newline Fixed Effects",
    "Controls,\newline All Observations",
]

# rename instruments
dfw.Instrumented.replace({"d": "duration_mid1_u", "v": "videos_mid1_u"}, inplace=True)

# order columns, copy og varnames
dfw = dfw.iloc[:, [0, 1, 3, 2]]
dfw["og"] = dfw.iloc[:, 0].copy()

# replace varnames with publishable names
for i in range(0, 4):
    dfw.iloc[:, i] = dfw.iloc[:, i].apply(
        lambda x: sorted([name_dict.get(k) or "None" for k in str(x).split(" ")]) or x
    )
    dfw.iloc[:, i] = dfw.iloc[:, i].apply(lambda x: ("\newline ").join(x))

# sort by publishable name
dfw.sort_values(["Dependent Variable", "Instrumented"], ascending=["False", "True"], inplace=True)

dfw.head()


# export to tex

# get subset and convert to tex
tablevars = dfw.og.unique()  # change this
table = dfw.loc[dfw.og.isin(tablevars), dfw.columns[:-1]]

# shorten variable descriptions
for c in table.columns[-2:]:
    table.loc[table[c].str.contains(", unique"), c] = table.loc[
        table[c].str.contains(", unique"), c
    ].apply(lambda x: x.replace(", unique", ""))

display(table.head())

# convert to latex

column_format = r"p{.25\linewidth} p{0.3\linewidth} " + r"p{0.22\linewidth} p{0.22\linewidth}"
caption = "LATE model controls selected via post-double-selection"
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
with open("../tex/tables/controlvars_selected_iv.tex", "w") as tf:
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

dfsub


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
with open("../tex/tables/firststage.tex", "w") as tf:
    tf.write(table)


# ### Table: second stage

# redo dfb with different rounding

dfb = get_dfb(3)
dfb.head()


def get_dfl(roundn):
    """
    Combines pds_iv_coeffs (dfiv) and lates_coeffs (dflate), formats for table output.
    """
    dfl = pd.concat([dfiv.copy().drop(columns=["ctrls"]), dflate.copy()])
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
table2_vars = [x for x in table_dict if table_dict.get(x) == 2]
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
dfsub.Instrumented.replace(
    {"z": "RF: Incentive", "v": "2SLS: 10 videos", "d": "2SLS: 1 hour of videos"},
    inplace=True,
)

# remove Instrumented duplicates and unnecessary cols
for v in dfsub.og.unique():
    dfsub.loc[dfsub.og == v, "Instrumented"] = dfsub.loc[dfsub.og == v].Instrumented.mask(
        dfsub.loc[dfsub.og == v].Instrumented.duplicated(), ""
    )
dfsub = dfsub.drop(column=["depvar", "stat", "og"])

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
dfsub.loc[len(dfsub), :] = ["Pair Fixed Effects", "No", "No", "No", "Yes"]

dfsub


# translate to tex

column_format = "m{0.35\\linewidth} *{4}{>{\\centering\\arraybackslash}m{0.1\\linewidth}}"
caption = "Effects of Videos on Grades"
label = "secondstage_table"
note = combine_notes([note_bothspec, note_scorestd, note_4models])

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
with open("../tex/tables/secondstage.tex", "w") as tf:
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
dfsub


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
with open("../tex/tables/spillover_grades.tex", "w") as tf:
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
dfsub


# translate to tex

column_format = "m{0.39\\linewidth} *{5}{>{\\centering\\arraybackslash}m{0.09\\linewidth}}"
caption = "Spillover Effects of Incentive on Other Studying"
label = "spillover_studying"
note = combine_notes([note_ittspec, note_attend, note_pset, note_4models, note_ctrlmean])

table = convert_to_latex(
    dfsub, column_format, caption, label, note, scalewidth=False, observations=True
)

# write to tex file
with open("../tex/tables/spillover_studying.tex", "w") as tf:
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
dfsub


# translate to tex

column_format = "m{0.35\\linewidth} *{5}{>{\\centering\\arraybackslash}m{0.1\\linewidth}}"
caption = "Effects of Treatment on Subsequent Quarter Enrollment and Course Outcomes"
label = "spillover_100b"
notex = (
    "Sample includes all students who completed Micro A (saw treatment assignment). "
    "Took Micro B is an indicator for enrolling in the subsequent course in the "
    "quarter following the experiment."
)
note_models_t8 = (
    "Model (1) contains linear controls for midterm 1 score and year; "
    "(2) is the difference in means and standard errors calculated using the repeated "
    "sampling framework of Neyman (1923); (3) and (4) use the post-double-selection "
    "(PDS) procedure of \\textcite{bch2014a} to select control variables then estimate "
    "treatment effects and standard errors. The control variables selected using PDS "
    "are listed in Table \\ref{tab:controlvars_selected_itt}."
)
note = combine_notes([note_ittspec, notex, note_models_t8, note_ctrlmean])

table = convert_to_latex(
    dfsub, column_format, caption, label, note, scalewidth=True, observations=True
)

# add indents
varlist = [x for x in dfsub.iloc[:, 0].unique() if x not in ["", "Observations",
           "Treatment assignment controls", "Demographic controls", "Pair Fixed Effects"]]
table = add_indents(table, varlist)

# write to tex file
with open("../tex/tables/spillover_100b.tex", "w") as tf:
    tf.write(table)


# ### Table 9: Micro B results

import os

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
df_pds = pd.read_csv("../data/generated/pds_coeffs.csv")
df_pds = df_pds[(df_pds["model"] == "noFEs") & (df_pds["depvar"].isin(t9_outcomes))].copy()
df_pds = df_pds.set_index("depvar")

# --- Column (2): Semenova (2025) Bounds ---
semenova_path = "../data/generated/semenova_bounds_100b.csv"
semenova_available = os.path.exists(semenova_path)
if not semenova_available:
    print(f"Warning: {semenova_path} not found. Column (2) will be omitted.")
else:
    df_sem = pd.read_csv(semenova_path)
    df_sem = df_sem[df_sem["depvar"].isin(t9_alt_depvar.values())].copy()
    df_sem = df_sem.set_index("depvar")

# --- Column (3): IPW ---
ipw_path = "../data/generated/ipw_100b.csv"
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
obs_col1 = ""
obs_col2 = ""
obs_col3 = ""

for depvar in t9_outcomes:
    label_str = t9_display[depvar]
    alt_depvar = t9_alt_depvar[depvar]

    # Column (1): PDS noFEs
    if depvar in df_pds.index:
        row_pds = df_pds.loc[depvar]
        ctrl_mean = f"{row_pds['meanctrl']:.2f}"
        beta_stars = fmt_stars(row_pds["treatbeta"], row_pds["stderr"])
        se_str = f"({row_pds['stderr']:.2f})"
        obs_col1 = str(int(row_pds["N"]))
    else:
        ctrl_mean, beta_stars, se_str = "", "", ""

    # Column (2): Semenova bounds
    if semenova_available and alt_depvar in df_sem.index:
        row_sem = df_sem.loc[alt_depvar]
        bounds_str = f"[{row_sem['lower_bound']:.2f}, {row_sem['upper_bound']:.2f}]"
        ci_str = r"\{" + f"{row_sem['ci_lower']:.2f}, {row_sem['ci_upper']:.2f}" + r"\}"
        obs_col2 = str(int(row_sem["N_selected"]))
    else:
        bounds_str, ci_str = "", ""

    # Column (3): IPW
    if ipw_available and alt_depvar in df_ipw.index:
        row_ipw = df_ipw.loc[alt_depvar]
        ipw_beta = fmt_stars(row_ipw["treatbeta"], row_ipw["stderr"])
        ipw_se = f"({row_ipw['stderr']:.2f})"
        obs_col3 = str(int(row_ipw["N"]))
    else:
        ipw_beta, ipw_se = "", ""

    row1 = {"Outcome": label_str, "Control Mean": ctrl_mean, "(1) PDS": beta_stars}
    row2 = {"Outcome": "", "Control Mean": "", "(1) PDS": se_str}
    if semenova_available:
        row1["(2) Semenova Bounds"] = bounds_str
        row2["(2) Semenova Bounds"] = ci_str
    if ipw_available:
        row1["(3) IPW"] = ipw_beta
        row2["(3) IPW"] = ipw_se
    rows.append(row1)
    rows.append(row2)

# Observations row
obs_row = {"Outcome": "Observations", "Control Mean": "", "(1) PDS": obs_col1}
if semenova_available:
    obs_row["(2) Semenova Bounds"] = obs_col2
if ipw_available:
    obs_row["(3) IPW"] = obs_col3
rows.append(obs_row)

dft9 = pd.DataFrame(rows)
dft9


# Convert to LaTeX and write Table 9

note_t9_col1 = (
    "Column (1) reports post-double-selection (PDS) OLS coefficients on $Incentive_i$ "
    "estimated on the selected sample of Micro B takers."
)
note_t9_col2 = (
    "Column (2) reports generalized Lee (2009) bounds following "
    "\\textcite{semenova2025}; point estimates are shown as [lower, upper] and "
    "95\\% confidence regions are shown in curly braces."
)
note_t9_col3 = (
    "Column (3) reports IPW-weighted OLS, where weights are the inverse probability "
    "of enrolling in Micro B conditional on baseline covariates. "
)

notes_list = [note_t9_col1]
if semenova_available:
    notes_list.append(note_t9_col2)
if ipw_available:
    notes_list.append(note_t9_col3)
notes_list.append(note_scorestd)
note_t9 = combine_notes(notes_list)

caption = "Treatment Effects on Micro B Outcomes"
label = "tab:microb_results"

ncols = 3 + semenova_available + ipw_available
column_format = "l" + "c" * (ncols - 1)

table9 = convert_to_latex(
    dft9, column_format=column_format, caption=caption, label=label,
    note=note_t9, observations=True, scalewidth=True, stars=True, regnote=False,
)

# Add panel labels
table9 = insert_panel(table9, ncols, "A", "Videos during Micro B", name_dict.get("videos_b"))
table9 = insert_panel(table9, ncols, "B", "Micro B exam scores", name_dict.get("mid1bscorestd"), False)

# Indent variable names
varlist = [v for v in dft9["Outcome"].unique() if v not in ["", "Observations"]]
table9 = add_indents(table9, varlist)

with open("../tex/tables/table9_microb.tex", "w") as tf:
    tf.write(table9)


# ## Other tables

# ### Table: heterogeneity

# read in data
dfh = pd.read_csv("../data/generated/het_coeffs.csv")
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

dfht


# translate to tex

column_format = "m{0.40\\linewidth} *{2}{>{\\centering\\arraybackslash}m{0.12\\linewidth}}"
caption = "Heterogeneous Effects of Treatment"
label = "het_table"

# table notes
note_het = "This table reports estimates for $\\beta_2$ from Equation \\ref{het_spec}."
note = combine_notes([note_het, note_scorestd])

table = convert_to_latex(
    dfht, column_format, caption, label, note, scalewidth=False, observations=True
)

# space out variables
for v in [x for x in dfht["Interaction Variable"].unique() if x not in ["", "Observations"]]:
    table = table.replace(v + " &", "\\customlinespace " + v + " &")

# write to tex file
with open("../tex/tables/het_table.tex", "w") as tf:
    tf.write(table)

