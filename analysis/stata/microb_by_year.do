* Micro B enrollment ("Took Micro B") by year.
version 17
do "analysis/stata/_setup.do"

load_analysis_data
tempfile full_data
quietly save `full_data'

* ---------------------------------------------------------------------------
* Took Micro B by year (models 1-5)
* ---------------------------------------------------------------------------
capture frame drop took_results
frame create took_results model double beta double se double N double meanctrl ///
    str99 ctrls str8 sample double pvalue

foreach sample in pooled 2018 2019 {
    use `full_data', clear
    if "`sample'" != "pooled" {
        keep if year == `sample'
        local yrctrl
    }
    else {
        local yrctrl y2019
    }

    * Model (1): OLS on final-exam takers
    quietly summarize took100b if !missing(finalscorestd) & arm == 1, meanonly
    local m1 = r(mean)
    quietly regress took100b treated mid1scorestd `yrctrl' if !missing(finalscorestd) & arm > 0, robust
    local b_`sample'_1 = _b[treated]
    local se_`sample'_1 = _se[treated]
    frame post took_results (1) (_b[treated]) (_se[treated]) (e(N)) (`m1') ("") ("`sample'") (.)

    * Model (2): Neyman matched pairs
    preserve
    pair_differences took100b, exam(final)
    local N = r(N)
    local J = r(J)
    local mp = r(meanctrl)
    quietly summarize d_took100b, meanonly
    local diff = r(mean)
    pair_covariance d_took100b d_took100b `J'
    local se2 = sqrt(r(cov))
    local b_`sample'_2 = `diff'
    local se_`sample'_2 = `se2'
    frame post took_results (2) (`diff') (`se2') (`N') (`mp') ("") ("`sample'") (.)
    restore

    * Model (3): PDS without pair FEs
    preserve
    keep if !missing(finalscorestd) & arm > 0
    quietly pdslasso took100b treated (`yrctrl' mid1scorestd $ctrl_vars), ///
        partial(`yrctrl' mid1scorestd) robust
    local b_`sample'_3 = _b[treated]
    local se_`sample'_3 = _se[treated]
    frame post took_results (3) (_b[treated]) (_se[treated]) (e(N)) (`m1') ///
        ("`e(xselected)'") ("`sample'") (.)
    restore

    * Model (4): PDS with pair FEs (+ pair_fe_se adjustment)
    preserve
    keep if bothpairs_final & arm > 0
    xtset pairyear
    quietly pdslasso took100b treated (mid1scorestd $ctrl_vars), ///
        partial(mid1scorestd) fe robust
    local fe_se = _se[treated]
    pair_fe_se `fe_se'
    local b_`sample'_4 = _b[treated]
    local se_`sample'_4 = `fe_se'
    frame post took_results (4) (_b[treated]) (`fe_se') (e(N)) (`mp') ///
        ("`e(xselected)'") ("`sample'") (.)
    restore

    * Model (5): All students who observed assignment (Figure A2 population), non-enrollment = 0
    preserve
    keep if !missing(assigned_grade) & arm > 0
    replace took100b = 0 if missing(took100b)
    quietly summarize took100b if arm == 1, meanonly
    local m5 = r(mean)
    quietly regress took100b treated mid1scorestd `yrctrl', robust
    local b_`sample'_5 = _b[treated]
    local se_`sample'_5 = _se[treated]
    frame post took_results (5) (_b[treated]) (_se[treated]) (e(N)) (`m5') ("") ("`sample'") (.)
    restore
}

* Difference rows: 2019 - 2018 (independent samples)
forvalues m = 1/5 {
    local db = `b_2019_`m'' - `b_2018_`m''
    local dse = sqrt((`se_2018_`m'')^2 + (`se_2019_`m'')^2)
    local dp = 2 * normal(-abs(`db' / `dse'))
    frame post took_results (`m') (`db') (`dse') (.) (.) ("") ("diff") (`dp')
}

frame took_results: export delimited "data/generated/microb_took_by_year.csv", replace
