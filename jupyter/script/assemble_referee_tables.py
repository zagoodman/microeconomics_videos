#!/usr/bin/env python
# coding: utf-8

# # Referee-requested tables (JEE revision)
# 
# Python kernel. Reads the CSVs written by `scripts/stata/` (`by_year_balance.do`, `credit_eligible.do`, `microb_by_year.do`) and writes LaTeX to `tex/tables/`:
# 
# | Output | Referee point |
# |---|---|
# | `attrite_chart_by_year.tex` | 1 — Figure A1 by year |
# | `balance_table_takers_2018.tex`, `balance_table_takers_2019.tex` | 1 — Table A1 by year |
# | `exam_stats_by_year.tex` | 2 — exam mean/median/SD by year |
# | `firststage_credit.tex`, `secondstage_credit.tex` | 4 — Tables 4 and 5 with credit-eligible videos |
# | `microb_took_by_year.tex`, `microb_videos_by_year.tex` | 3 — Table 8 (Took Micro B) and Table 9 Panel A by year |
# 
# Kept separate from `assemble_tables.ipynb` so these tables build on their own.

import pandas as pd
from table_utils import get_p_value, star_p

DATA_GEN = "../data/generated"
TEX = "../tex/tables"
YEARS = [2018, 2019]

REGNOTE = "\\Regnote"


def write(name, text):
    with open(f"{TEX}/{name}.tex", "w") as f:
        f.write(text)
    print(f"wrote {name}.tex")


def stars(beta, se):
    z = abs(beta) / se
    return "***" if z > 2.576 else "**" if z > 1.96 else "*" if z > 1.645 else ""


def fmt_beta(beta, se, nd):
    s = stars(beta, se)
    return f"{beta:.{nd}f}" + (f"\\sym{{{s}}}" if s else "")


# ## Figure A1 by year: attrition by treatment arm

attr = pd.read_csv(f"{DATA_GEN}/attrition_by_year.csv")


def pct(n, base):
    return f"{int(n)} ({100 * n / base:.1f}\\%)" if base else str(int(n))


def pval_text(p):
    return "no attrition" if pd.isna(p) else f"$p={p:.2f}$"


def tree(year):
    a = attr[attr["sample"] == str(year)].set_index("arm")
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
        "\t\t\tlevel 2/.style = {sibling distance=35mm, level distance=10mm}, edge from parent fork down, edge from parent/.style = {draw, semithick, -latex},\n"
        "\t\t\t]\n"
        f"\t\t\t\\node [text width = 50mm] (L1) {{Midterm 1 takers, {year}}}\n"
        "\t\t\tchild {node (L2) {Above median}\n"
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
    "\t\t\\caption{Attrition by treatment arm and year}\n"
    "\t\t\\label{fig:attritchart_year}\n\t\t\\footnotesize\n"
    "\t\t\\textbf{Panel A: 2018}\\\\[1mm]\n" + tree(2018) + "\n\t\t\\bigskip\n\n"
    "\t\t\\textbf{Panel B: 2019}\\\\[1mm]\n" + tree(2019) + "\n"
    "\t\t{Percentages in parentheses are the portion of students who observe their treatment status and took the "
    "second midterm, final exam, and enrolled in Micro B, calculated separately for each treatment arm and year. "
    "The p-values are from a two-sample t-test of the equality of attrition rates between the "
    "\\textit{Control} and \\textit{Incentive} arms at each stage within year. "
    "\\textit{Above median} counts before removing minors and opt-outs are not available by year.}\n"
    "\t\\end{center}\n\\end{figure}\n"
)
write("attrite_chart_by_year", fig)


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
        f"\\begin{{table}} \\centering \\caption{{Balance test, exam taker sample, {year}}} \n"
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
        "exams. It reproduces Table~\\ref{tab:balance_table_takers} separately by year. Descriptions of each "
        "variable can be found in Table \\ref{tab:controlvars_desc}. \\textit{Female} and \\textit{Male} are "
        "coded zero for students who do not report a gender. \\textit{P-values} are reported for the Welch's "
        "t-test of equal means between the \\textit{Control} and \\textit{Incentive} arms. \\Regnote} \n"
        "\\end{threeparttable}}\n\\end{table} \n\\end{spacing}\n"
    )


for y in YEARS:
    write(f"balance_table_takers_{y}", balance_table(y))


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
    "\\begin{table} \\centering \\caption{Exam scores by year} \n"
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
write("exam_stats_by_year", table)


# ## Tables 4 and 5 with credit-eligible video counts

fs = pd.read_csv(f"{DATA_GEN}/credit_firststage_coeffs.csv")
ss = pd.read_csv(f"{DATA_GEN}/credit_secondstage_coeffs.csv")

NOTE_4MODELS = (
    "Model (1) contains linear controls for midterm 1 score and year; (2) is the difference in means and "
    "standard errors calculated using the repeated sampling framework of Neyman (1923); (3) and (4) use the "
    "post-double-selection (PDS) procedure of \\textcite{bch2014a} to select control variables then estimate "
    "treatment effects and standard errors. Models (2) and (4) include only students whose matched-pair did "
    "not attrite from the experiment."
)
NOTE_CREDIT = (
    "Video measures count only credit-eligible video openings: a video counts only if the student did not "
    "open another video before this one could have been watched in its entirety at 2x playback speed "
    "(allowing one minute for timestamp rounding), the condition \\textit{Incentive} students were told was required for credit. "
    "The rule is applied identically to all arms."
)
FOOT = [
    ("Treatment assignment controls", ["Yes", "No", "Yes", "Yes"]),
    ("Demographic controls", ["No", "No", "Yes", "Yes"]),
    ("Pair Fixed Effects", ["No", "No", "No", "Yes"]),
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
write("firststage_credit", t4)

# Table 5 analogue
labels = {
    "RF": "RF: Incentive",
    "2SLS_videos10": "2SLS: 10 videos",
    "2SLS_hours": "2SLS: 1 hour of videos",
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
write("secondstage_credit", t5)


# ## Micro B enrollment and Micro B video watching by year

took = pd.read_csv(f"{DATA_GEN}/microb_took_by_year.csv")
vids = pd.read_csv(f"{DATA_GEN}/microb_videos_by_year.csv")
sem = {y: pd.read_csv(f"{DATA_GEN}/semenova_bounds_100b_{y}.csv").set_index("depvar") for y in YEARS}

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
    ("Pair Fixed Effects", ["No", "No", "No", "Yes", "No"]),
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
    "Figure~\\ref{fig:attritchart_year}. Panel C reproduces Table~\\ref{tab:spillover_100b} and adds model (5). "
    "Panel D reports the difference between the 2019 and 2018 estimates; because the years are independent samples, its "
    "standard error is $\\sqrt{se_{2018}^2 + se_{2019}^2}$. \\textit{Control mean} is the enrollment rate of "
    "\\textit{Control} students in each estimation sample. \\Regnote}\n"
    "\\end{threeparttable}\n\\end{table} \n\\end{spacing}\n"
)
write("microb_took_by_year", t)


# Table 9 Panel A by year
VID_ROWS = [
    ("videos_b", "Num. of videos"),
    ("videos_b_u", "Num. unique videos"),
    ("duration_b", "Hours of videos"),
    ("duration_b_u", "Hours unique videos"),
]
body = ""
for samp, letter, title in [p for p in PANELS if p[0] != "pooled"]:
    letter = {"2018": "A", "2019": "B", "diff": "C"}[samp]
    if letter != "A":
        body += "\\midrule \n"
    body += f"\\multicolumn{{6}}{{l}}{{\\textbf{{Panel {letter}}}: {title}}} \\\\ \n"
    v = vids[vids["sample"] == samp].set_index(["depvar", "model"])
    for dv, lab in VID_ROWS:
        pd_, iw = v.loc[(dv, "pds")], v.loc[(dv, "ipw")]
        if samp == "diff":
            row1 = ["", fmt_beta(pd_.beta, pd_.se, 2), "", fmt_beta(iw.beta, iw.se, 2), ""]
            row2 = ["", f"({pd_.se:.2f})", "", f"({iw.se:.2f})", ""]
        else:
            sb, lee = sem[int(samp)].loc[dv], sem[int(samp)].loc[f"{dv}_lee2009"]
            row1 = [
                f"{pd_.meanctrl:.2f}",
                fmt_beta(pd_.beta, pd_.se, 2),
                f"[{sb.lower_bound:.2f}, {sb.upper_bound:.2f}]",
                fmt_beta(iw.beta, iw.se, 2),
                f"[{lee.lower_bound:.2f}, {lee.upper_bound:.2f}]",
            ]
            row2 = ["", f"({pd_.se:.2f})", f"\\{{{sb.ci_lower:.2f}, {sb.ci_upper:.2f}\\}}", f"({iw.se:.2f})", ""]
        body += f"\\customlinespace \\indentrow{{{lab}}} & " + " & ".join(row1) + " \\\\\n & " + " & ".join(row2) + " \\\\\n"
    if samp != "diff":
        sb = sem[int(samp)].loc["videos_b"]
        n = [int(v.loc[("videos_b", "pds")].N), int(sb.N_selected), int(v.loc[("videos_b", "ipw")].N), int(sb.N_selected)]
        body += "\\indentrow{Observations} & & " + " & ".join(map(str, n)) + " \\\\\n"
t = (
    "\\begin{spacing}{1.0} \n"
    "\\begin{table} \\centering \\caption{Treatment Effects on Micro B Video Watching by Year} \n"
    "\\label{tab:microb_videos_by_year} \n\\resizebox{\\linewidth}{!}{% \n\\begin{threeparttable} \n"
    "\\begin{tabular}{lccccc}\n\\toprule\n"
    " & Control Mean & (1) PDS & (2) Semenova Bounds & (3) IPW & (4) Lee Bounds \\\\\n\\midrule\n"
    + body
    + "\\bottomrule\n\\end{tabular}\n"
    "\\Fignote{This table re-estimates Panel A of Table~\\ref{tab:microb_results} separately by year; the year "
    "control is dropped within year, as are covariates with no variation within year. Columns (1)--(3) are as in "
    "Table~\\ref{tab:microb_results}. Column (4) reports \\textcite{lee2009} bounds without covariates. In 2018, "
    "\\textit{Control} and \\textit{Incentive} students enrolled in Micro B at nearly the same rate "
    "(Table~\\ref{tab:microb_took_by_year}), so little trimming is required. In 2019, the outcome model for column (2) "
    "omits the \\textit{White} indicator, which is collinear with treatment among selected students. Panel C reports the "
    "difference between the 2019 and 2018 estimates, with standard error $\\sqrt{se_{2018}^2 + se_{2019}^2}$. \\Regnote}\n"
    "\\end{threeparttable}}\n\\end{table} \n\\end{spacing}\n"
)
write("microb_videos_by_year", t)

