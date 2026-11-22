# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project Overview

Research replication repository for the paper *"The Effects of Supplementary Videos on Learning in Intermediate Microeconomics: Estimates from a Field Experiment"* by Melissa Famulari and Zachary A. Goodman (UC San Diego). Evaluates the effectiveness of the Intermediate Microeconomics Video Handbook (IMVH) using a randomized controlled trial.

## Pipeline

The project is split into `construction/` (raw data → clean datasets in `data/generated/`) and `analysis/` (clean datasets → estimates, tables, and figures; never reads `data/raw/`):

1. **Data Construction** (`construction/assemble_data.py`) — Python (`uv run python construction/assemble_data.py`). Reads raw Excel/CSV files from `data/raw/`, outputs processed datasets to `data/generated/` (`student_analysis_sample.csv`, `student_demographics_{fall,winter}.csv`, `weekly_video_panel.csv`, `video_watch_rates.csv`, `treatment_awareness_quiz.csv`). In `construction/modules/loaders.py` (`load_quarter_gpa`), the 2018 registrar label `"N Classes - Not Passed - DFNP"` is harmonized with 2019 `"N Classes - Not Passed"` into `nclass_np` (counts D, F, and NP grades only, excluding incompletes).
2. **Statistical Analysis** (`analysis/stata/`) — Stata 17. From the repo root: `stata -b do analysis/stata/run_all.do` (logs to `logs/`), or `do analysis/stata/<name>.do` for one table. Scripts writing CSVs to `data/generated/`: `balance`, `itt`, `pds`, `late`, `pds_iv`, `weak_iv`, `microb_selection`, `heterogeneity`, `by_year_balance` (`attrition_by_year`, `balance_table_data_by_year`, `exam_stats_by_year`), `credit_eligible` (`credit_firststage_coeffs`, `credit_secondstage_coeffs`), and `microb_by_year` (`microb_took_by_year`, `microb_videos_by_year`); `sample_checks` and `robustness` write logs only. Shared programs are one-per-file in `analysis/stata/ado/` (on the adopath via `_setup.do`, which also holds the control and outcome lists). Key conventions:
   - PDS control candidates are the 2021 accepted set (no `mathquiz_unobs`).
   - `ado/pair_fe_se.ado` hard-codes the $\sqrt{N/(N-G)}$ pair-FE degrees-of-freedom adjustment omitted by `pdslasso`/`ivlasso` 1.1.02 (applied in `pds_itt`, `pds_iv`, `credit_eligible`, and `microb_by_year`). If a newer package version already applies this adjustment, SEs would be double-corrected — verify against a known printed value (e.g., `9.585 (2.185)`).
   - `ado/pair_differences.ado` drops pairs with any missing outcome difference before computing $J$, $N = 2J$, and the Control mean.
   - `microb_selection.do` and `microb_by_year.do` bootstrap (`reps(1000)`, fixed seed `20192`) the full logit → IPW → 1st/99th-percentile winsorization → WLS pipeline.
   - `weak_iv.do` writes effective $F$ (`weakivtest`) and Anderson–Rubin confidence sets (`weakiv`) to `data/generated/weak_iv.csv`.
   - `robustness.do` runs randomization inference within `strata(pairyear)` (`reps(5000)` for both exams, `arm > 0`) and `sqreg` with `y2019` (`reps(500)`). `heterogeneity.do` seeds `mhtreg` (`set seed 20191`).
   - The Stata plotting code was dropped; figures come from `analysis/python/make_figures.py`.
3. **Table & Figure Generation** (`analysis/python/assemble_tables.py`, `analysis/python/assemble_referee_tables.py`, `analysis/python/make_figures.py`) — Python. Reads coefficient estimates from `data/generated/` (including `weak_iv.csv` → `tex/tables/arci_table.tex` and the by-year / credit-eligible CSVs → `tex/tables/*_by_year.tex`, `balance_table_takers_{2018,2019}.tex`, `*_credit.tex`), formats publication-ready LaTeX tables to `tex/tables/`.

Generalized Lee bounds (R):

- `Rscript analysis/r/semenova_bounds.R <leebounds-repo> <year>` — by-year generalized Lee bounds (`semenova_bounds_100b_{2018,2019}.csv`), needed by `assemble_referee_tables.py`. Without a year it rewrites the pooled Table 9 bounds (bootstrap was unseeded before, so pooled CIs will shift slightly).

*(Helper modules `analysis/python/modules/analysis_data.py` and `analysis/python/modules/estimators.py` are retained for figure generation and `scripts/export_results.py`; all econometric estimation runs in `analysis/stata/`.)*

Paper figures: `analysis/python/make_figures.py` (`analysis/python/modules/figures.py`) generates the nine figures the paper includes, in the JEE print style (B&W, arms by line pattern/weight, Times New Roman bold 8–10 pt, ≤5×5 in). Writes `tex/plots/<name>.pdf` for LaTeX (included at native size, no `width=`) and `tex/plots/jee/<name>.{eps,tif}` (600 dpi grayscale) for submission. Use opaque grays only — EPS has no transparency.

Paper site (private, local-only one-pager, built with the `paper-site` skill):

- `uv run python scripts/export_results.py` writes `results/numbers.json` from the estimate CSVs in `data/generated/` and rasterizes five paper PDFs from `tex/plots/` to `results/figures/*.png`. Every table number is checked against the committed `tex/tables/*.tex` cell; where they differ the printed value wins and the mismatch is listed (as of Nov 2026, 31 cells differ: mostly pair-FE standard errors in model (4), ~1/√2 of the printed ones, plus a few PDS estimates — the CSVs were regenerated after the tables were built).
- Prose lives in `site/content.md` (`{{key}}` placeholders only, no typed results). Build: `python ~/.claude-zgoodman/skills/paper-site/scripts/build_site.py --numbers results/numbers.json --content site/content.md --figures results/figures --bib tex/paper/bibliography.bib --out site/_build` (gitignored). Serve on 127.0.0.1 only.

The final paper is compiled from `tex/paper/video_experiment.tex` which includes the generated tables and plots.

## Environment Setup

```bash
uv sync
```

Stata 17 must be installed separately for `analysis/stata/`. Required packages (checked by `_setup.do`): `ivreg2`, `ranktest`, `weakiv`, `weakivtest`, `avar`, `moremata`, `pdslasso`/`lassopack`, `mhtreg`, `ritest`.

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

- **Python**: pandas, numpy, scipy, matplotlib, pillow, openpyxl
- **Stata**: Used for all econometric analysis (IV estimation, heterogeneous effects, spillover analysis)
- **R**: Used for generalized Lee bounds (`analysis/r/semenova_bounds.R`)
- **LaTeX**: BibLaTeX with Chicago 15th edition / JEE author-date style (`style=authoryear` customized in `tex/paper/preamble.tex`), 12pt Times New Roman (`times`), double-spaced, unnumbered headings, automated endnotes

## Repository Conventions

- Data files (`.xlsx`, `.xls`, `.csv`, `.dta`) are gitignored — never commit raw data
- Generated outputs (plots as PDFs/EPS/TIFF, tables as `.tex`) are committed to version control
- `analysis/r/semenova_bounds.R` is a standalone R script that computes generalized Lee bounds.
- No formal test suite; validation is done through script execution and output diffs

## Post-Change Checklist

After every change, check whether AGENTS.md or other documentation needs to be updated to reflect the change. This includes changes to the pipeline, build process, dependencies, conventions, or project structure.
