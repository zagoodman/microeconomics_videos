#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/paper"

pdflatex video_experiment.tex
biber video_experiment
pdflatex video_experiment.tex
pdflatex video_experiment.tex
