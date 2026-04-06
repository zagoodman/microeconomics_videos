# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Research replication repository for the paper *"The Effects of Supplementary Videos on Learning in Intermediate Microeconomics: Estimates from a Field Experiment"* by Melissa Famulari and Zachary A. Goodman (UC San Diego). Evaluates the effectiveness of the Intermediate Microeconomics Video Handbook (IMVH) using a randomized controlled trial.

## Pipeline

The project follows a three-stage pipeline, each driven by a Jupyter notebook:

1. **Data Assembly** (`jupyter/assemble_data.ipynb`) — Python kernel. Reads raw Excel data from `data/raw/`, outputs processed files to `data/generated/`.
2. **Statistical Analysis** (`jupyter/analyze_data.ipynb`) — Stata kernel ([stata_kernel](https://kylebarron.dev/stata_kernel/)). Runs IV regressions, balance checks, attrition analysis. Generates PDF plots to `tex/plots/`.
3. **Table Generation** (`jupyter/assemble_tables.ipynb`) — Python kernel. Reads coefficient estimates, formats publication-ready LaTeX tables to `tex/tables/`.

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
- **LaTeX**: BibLaTeX with APA style (custom `apa.bbx`/`apa.cbx`)

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
