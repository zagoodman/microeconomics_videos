# semenova_bounds.R
# Compute generalized Lee Bounds (Semenova 2025) for Micro B outcomes.
#
# Reads:  data/generated/semenova_sample.csv  (exported by analyze_data.do)
# Writes: data/generated/semenova_bounds_100b.csv
#
# Dependencies: dplyr, expm, quantreg, reldist
# Also requires the vsemenova/leebounds repo cloned locally.
#
# Usage:
#   Rscript jupyter/modules/semenova_bounds.R <path-to-leebounds-repo>
#
# Example:
#   Rscript jupyter/modules/semenova_bounds.R ~/github/leebounds

library(dplyr)
library(expm)
library(quantreg)
library(reldist)

# --- Parse args ---
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: Rscript semenova_bounds.R <path-to-leebounds-repo>")
}
leebounds_path <- args[1]

# --- Source the Semenova package ---
source(file.path(leebounds_path, "R", "auxiliary.R"))
source(file.path(leebounds_path, "R", "leebounds.R"))
source(file.path(leebounds_path, "R", "first_stage_functions.R"))
source(file.path(leebounds_path, "R", "second_stage_functions.R"))

# --- Read data ---
df <- read.csv("data/generated/semenova_sample.csv")

# Covariates for selection model (all baseline controls)
covariates_selection <- c(
  "y2019",
  "mid1scorestd", "mathquizstd", "mathquiz_unobs",
  "transfer", "prev_cumgpa", "prev_cumgpa_unobs",
  "female", "asian", "latx", "white"
)

# Covariates for outcome quantile regression — drop near-constant indicators
# (mathquiz_unobs ~3% missing, prev_cumgpa_unobs) to avoid singular design matrix
# when Semenova interacts all covariates with treatment
covariates_outcome <- c(
  "y2019",
  "mid1scorestd", "mathquizstd",
  "transfer", "prev_cumgpa",
  "female", "asian", "latx", "white"
)

# Outcome variables and their raw names in the data
outcomes <- list(
  list(depvar = "videos_b",      col = "videos_b"),
  list(depvar = "videos_b_u",    col = "videos_b_u"),
  list(depvar = "duration_b",    col = "duration_b"),
  list(depvar = "duration_b_u",  col = "duration_b_u"),
  list(depvar = "mid1_100bstd",  col = "mid1_100bstd"),
  list(depvar = "mid2_100bstd",  col = "mid2_100bstd"),
  list(depvar = "final_100bstd", col = "final_100bstd")
)

# Treatment probability (balanced RCT within randomized pairs)
prop_treat <- mean(df$treated)

# Trimming thresholds (Semenova recommended formula)
N <- nrow(df)
rhoN <- N^(-1/4) * log(N)^(-1)
p0 <- 1 - rhoN
p1 <- 1 + rhoN

N_bootstrap <- 2000

# --- Run bounds for each outcome ---
results <- data.frame(
  depvar      = character(),
  lower_bound = numeric(),
  upper_bound = numeric(),
  ci_lower    = numeric(),
  ci_upper    = numeric(),
  N           = integer(),
  N_selected  = integer(),
  stringsAsFactors = FALSE
)

for (out in outcomes) {
  cat("Running Semenova bounds for:", out$depvar, "\n")

  # Selection: outcome is observed (took Micro B AND has non-missing value)
  selected <- as.numeric(df$took100b == 1 & !is.na(df[[out$col]]))
  raw_outcome <- df[[out$col]]
  raw_outcome[is.na(raw_outcome)] <- 0

  # Build leedata
  leedata <- data.frame(
    treat     = df$treated,
    selection = selected,
    outcome   = selected * raw_outcome,
    weights   = rep(1, N),
    prop1     = rep(prop_treat, N),
    prop0     = rep(1 - prop_treat, N)
  )
  # Attach all covariates (union of selection and outcome covariate sets)
  for (cv in union(covariates_selection, covariates_outcome)) {
    leedata[[cv]] <- df[[cv]]
  }

  # Compute bounds
  result <- ortho_leebounds(
    leedata                 = leedata,
    selection_function_name = "glm",
    variables_for_selection = covariates_selection,
    variables_for_outcome   = covariates_outcome,
    quantile_grid_size      = 0.01,
    outcome_function_name   = "rq",
    min_wage                = min(leedata$outcome[leedata$selection == 1]),
    max_wage                = max(leedata$outcome[leedata$selection == 1]),
    ortho                   = TRUE,
    p0                      = p0,
    p1                      = p1
  )

  bounds <- GetBounds(result)
  cat("  Bounds:", bounds[1], bounds[2], "\n")

  # Bootstrap confidence region
  bounds_bb <- main_bb(
    result$leedata,
    N_rep         = N_bootstrap,
    function_name = second_stage_wrapper,
    ortho         = TRUE,
    p0            = p0,
    p1            = p1
  )
  cr <- compute_confidence_region(bounds_bb, bounds, ci_alpha = 0.05)
  cat("  95% CR:", cr[1], cr[2], "\n")

  results <- rbind(results, data.frame(
    depvar      = out$depvar,
    lower_bound = bounds[1],
    upper_bound = bounds[2],
    ci_lower    = cr[1],
    ci_upper    = cr[2],
    N           = N,
    N_selected  = sum(selected),
    stringsAsFactors = FALSE
  ))
}

# Also compute basic Lee (2009) bounds for comparison
cat("\nComputing basic Lee (2009) bounds for comparison...\n")
for (out in outcomes) {
  selected <- as.numeric(df$took100b == 1 & !is.na(df[[out$col]]))
  raw_outcome <- df[[out$col]]
  raw_outcome[is.na(raw_outcome)] <- 0

  leedata <- data.frame(
    treat     = df$treated,
    selection = selected,
    outcome   = selected * raw_outcome,
    weights   = rep(1, N),
    prop1     = rep(prop_treat, N),
    prop0     = rep(1 - prop_treat, N)
  )

  basic <- basic_lee_bound(leedata)
  basic_bounds <- GetBounds(basic)
  cat("  ", out$depvar, "basic Lee:", basic_bounds[1], basic_bounds[2], "\n")

  results <- rbind(results, data.frame(
    depvar      = paste0(out$depvar, "_lee2009"),
    lower_bound = basic_bounds[1],
    upper_bound = basic_bounds[2],
    ci_lower    = NA,
    ci_upper    = NA,
    N           = N,
    N_selected  = sum(selected),
    stringsAsFactors = FALSE
  ))
}

# --- Write results ---
write.csv(results, "data/generated/semenova_bounds_100b.csv", row.names = FALSE)
cat("\nResults written to data/generated/semenova_bounds_100b.csv\n")
