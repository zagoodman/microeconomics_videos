# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Research replication repository for the paper *"The Effects of Supplementary Videos on Learning in Intermediate Microeconomics: Estimates from a Field Experiment"* by Melissa Famulari and Zachary A. Goodman (UC San Diego). Evaluates the effectiveness of the Intermediate Microeconomics Video Handbook (IMVH) using a randomized controlled trial.

## Pipeline

The project follows a three-stage pipeline, each driven by a Jupyter notebook:

1. **Data Assembly** (`jupyter/assemble_data.ipynb`) — Python kernel. Reads raw Excel data from `data/raw/`, outputs processed files to `data/generated/`.
2. **Statistical Analysis** (`jupyter/analyze_data.ipynb`) — Stata kernel ([stata_kernel](https://kylebarron.dev/stata_kernel/)). Runs IV regressions, balance checks, attrition analysis. Generates PDF plots to `tex/plots/`.
3. **Table Generation** (`jupyter/assemble_tables.ipynb`) — Python kernel. Reads coefficient estimates, formats publication-ready LaTeX tables to `tex/tables/`.

Referee-revision analyses (JEE, 2026) run as a Python side-pipeline after stage 1:

- `jupyter/referee_analysis.ipynb` — attrition/balance by year, exam score summary stats, Tables 4–5 with credit-eligible video counts (`*_cr` columns, built in `assemble_data.ipynb` via `modules/video_agg.add_credit_flag`), and Table 8 "Took Micro B" / Table 9 Panel A by year (incl. IPW port). Writes CSVs to `data/generated/`.
- `Rscript jupyter/modules/semenova_bounds.R <leebounds-repo> <year>` — by-year generalized Lee bounds (`semenova_bounds_100b_{2018,2019}.csv`), needed by the next notebook. Without a year it rewrites the pooled Table 9 bounds (bootstrap was unseeded before, so pooled CIs will shift slightly).
- `jupyter/assemble_referee_tables.ipynb` — turns those CSVs into `tex/tables/*_by_year.tex`, `balance_table_takers_{2018,2019}.tex`, `*_credit.tex`.

These use `modules/estimators.py` (numpy ports of the Stata OLS/2SLS/Neyman/`pdslasso`/`ivlasso`/IPW estimators) and `modules/analysis_data.py` (port of the Stata data prep). Written because the Stata license expired; `referee_analysis.ipynb` asserts that the ports reproduce the existing Stata output CSVs before computing anything new. Known gap: `ivlasso` with pair fixed effects selects different controls in 2 of 4 cases.

`assemble_tables.ipynb` no longer runs cleanly under current pandas (it writes malformed balance tables, then errors). Fix it before re-running, or revert the `tex/tables/` files it overwrites.

The final paper is compiled from `tex/paper/video_experiment.tex` which includes the generated tables and plots.

## Environment Setup

```bash
uv sync
```

Stata kernel must be installed separately for `analyze_data.ipynb`. Required Stata packages: `avar`, `binsreg`, `binscatter2`.

Raw data is private and excluded from the repo via `.gitignore` — must be downloaded separately into `data/`.

## LaTeX Setup

Install BasicTeX (minimal TeX distribution for macOS):

```bash
brew install --cask basictex
```

After installing, restart your terminal or run `eval "$(/usr/libexec/path_helper)"`, then update `tlmgr` and install required packages:

```bash
sudo tlmgr update --self
sudo tlmgr install scalerel doublestroke cmathbb placeins preprint threeparttable threeparttablex multirow csquotes epigraph biblatex biber biblatex-apa environ nextpage xstring
```

## Compiling the Paper

```bash
./tex/build.sh
```

## Key Dependencies

- **Python**: pandas, numpy, scipy, matplotlib, torch, pandas-flavor
- **Stata**: Used for all econometric analysis (IV estimation, heterogeneous effects, spillover analysis)
- **LaTeX**: BibLaTeX with Chicago 15th edition / JEE author-date style (`style=authoryear` customized in `tex/paper/preamble.tex`), 12pt Times New Roman (`times`), double-spaced, unnumbered headings, automated endnotes

## Exporting Notebooks

Notebooks are auto-exported as scripts on save via [nbautoexport](https://github.com/drivendataorg/nbautoexport). Config lives in `jupyter/.nbautoexport`. Exported scripts go to `jupyter/script/`. To manually export all notebooks:

```bash
uv run nbautoexport export jupyter/
```

## Repository Conventions

- Data files (`.xlsx`, `.xls`, `.csv`, `.dta`) are gitignored — never commit raw data
- Generated outputs (plots as PDFs, tables as `.tex`) are committed to version control
- Exported notebook scripts in `jupyter/script/` are committed to version control — these are **auto-generated** by nbautoexport from the `.ipynb` files and should never be edited directly. Always read/edit the `.ipynb` source notebooks, not the exported scripts.
- `jupyter/modules/semenova_bounds.R` is a standalone R script that computes generalized Lee bounds.
- HTML notebook renders in `jupyter/html_renders/` are marked as vendored in `.gitattributes`
- No formal test suite; validation is done through notebook execution and exploratory outputs

## Post-Change Checklist

After every change, check whether CLAUDE.md or other documentation needs to be updated to reflect the change. This includes changes to the pipeline, build process, dependencies, conventions, or project structure.
