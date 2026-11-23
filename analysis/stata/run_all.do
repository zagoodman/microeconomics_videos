version 17
capture log close _all
capture mkdir "logs"

foreach script in sample_checks balance itt pds late pds_iv weak_iv microb_selection ///
    heterogeneity robustness by_year_balance credit_eligible microb_by_year figure_data {
    log using "logs/`script'.log", replace text name(`script')
    do "analysis/stata/`script'.do"
    log close `script'
}
