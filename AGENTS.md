# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project Overview

Replication repository for *"The Effects of Supplementary Videos on Learning in Intermediate Microeconomics: Estimates from a Field Experiment"* by Melissa Famulari and Zachary A. Goodman (UC San Diego). Evaluates the effectiveness of the Intermediate Microeconomics Video Handbook (IMVH) using a randomized controlled trial.

## Pipeline

The codebase separates data construction from analysis: `construction/` transforms private raw files in `data/raw/` into clean datasets in `data/generated/`, and `analysis/` consumes only `data/generated/` (never `data/raw/`).

1. **Data Construction** (`construction/assemble_data.py`)
   - Run with `uv run python construction/assemble_data.py`.
   - Reads raw administrative, exam, and video-usage files from `data/raw/` and writes cleaned analysis datasets to `data/generated/`.

2. **Econometric Analysis** (`analysis/stata/`)
   - Run the full suite from the repository root with `stata -b do analysis/stata/run_all.do` (logs written to `logs/`), or run individual scripts with `do analysis/stata/<script>.do`.
   - Shared helper programs live one-per-file in `analysis/stata/ado/` and are added to the adopath by `analysis/stata/_setup.do`, which also defines global control/outcome lists and verifies required Stata packages.
   - `analysis/stata/ado/pair_fe_se.ado` applies a pair-fixed-effects degrees-of-freedom standard error adjustment that `pdslasso`/`ivlasso` omits. If a newer version of those packages applies this adjustment natively, verify against the committed LaTeX tables to avoid double-correcting.

3. **Generalized Lee Bounds** (`analysis/r/semenova_bounds.R`)
   - Standalone R script computing generalized Lee bounds (Semenova) from the selection sample exported by Stata.
   - Requires a local clone of the `vsemenova/leebounds` repository:
     ```bash
     Rscript analysis/r/semenova_bounds.R <path-to-leebounds-repo>
     ```

4. **Tables & Figures** (`analysis/python/`)
   - `uv run python analysis/python/make_tables.py` (supports `--only {all,main,referee}`) reads estimation CSVs from `data/generated/` and writes publication-ready LaTeX tables to `tex/tables/`.
   - `uv run python analysis/python/make_figures.py` generates journal-formatted grayscale figures (PDF for LaTeX, EPS/TIFF for submission) in `tex/plots/`. Keep figure styling opaque grayscale (EPS does not support transparency).
   - Figures read `data/generated/figure_sample.csv`, the student-level sample exported by `analysis/stata/figure_data.do` (run by `run_all.do`); Python never re-derives the analysis sample.
   - Helper modules in `analysis/python/modules/` support figure generation and table formatting only; all econometric estimation runs in Stata and R. Do not add Python ports of the Stata estimators or data prep.

5. **Paper Compilation** (`tex/`)
   - Run `./tex/build.sh` to compile `tex/paper/video_experiment.tex` (which inputs the generated tables and plots).

## Environment Setup

- **Python**: `uv sync` (uses `pandas`, `numpy`, `scipy`, `matplotlib`, `pillow`, `openpyxl`).
- **Stata**: Install Stata separately along with the user-written packages checked in `analysis/stata/_setup.do`.
- **R**: Requires `dplyr`, `expm`, `quantreg`, `reldist`, plus a local clone of `vsemenova/leebounds`.
- **LaTeX**: BibLaTeX with Chicago / JEE author-date formatting (`tex/paper/preamble.tex`). On macOS with BasicTeX:
  ```bash
  brew install --cask basictex
  sudo tlmgr update --self
  sudo tlmgr install scalerel doublestroke cmathbb placeins preprint threeparttable threeparttablex multirow csquotes epigraph biblatex biber biblatex-apa environ nextpage xstring
  ```

## Repository Conventions

- **Data privacy**: Raw and generated data files (`.xlsx`, `.xls`, `.csv`, `.dta`) are gitignored. Never commit raw data; it must be obtained separately and placed in `data/raw/`.
- **Committed outputs**: Generated LaTeX tables (`tex/tables/*.tex`) and figure files (`tex/plots/`) are tracked in version control.
- **Validation**: There is no formal test suite; validate changes by re-running the affected pipeline stage and reviewing diffs in generated tables, figures, and logs.
- **Documentation**: After structural changes to the pipeline, build process, dependencies, or conventions, update this file to keep it accurate.
