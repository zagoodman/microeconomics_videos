* Micro B enrollment ("Took Micro B") and Panel A video watching by year.
version 17
do "analysis/stata/_setup.do"

local panel_a videos_b videos_b_u duration_b duration_b_u
local selection_x mid1scorestd mathquizstd transfer ///
    prev_cumgpa prev_cumgpa_unobs female asian latx white

* Bootstrap program for 1st/99th-percentile winsorized IPW (matching microb_selection.do).
capture program drop _ipw_by_year
program define _ipw_by_year, rclass
    version 17
    syntax, outcomes(namelist) selection_x(namelist) [yrctrl(namelist)]
    tempvar phat ipw
    quietly logit took100b treated `selection_x' `yrctrl'
    quietly predict double `phat', pr
    quietly generate double `ipw' = 1 / `phat' if took100b == 1
    quietly _pctile `ipw' if took100b == 1, p(1 99)
    local lo = r(r1)
    local hi = r(r2)
    quietly replace `ipw' = `lo' if took100b == 1 & `ipw' < `lo'
    quietly replace `ipw' = `hi' if took100b == 1 & !missing(`ipw') & `ipw' > `hi'
    foreach y of local outcomes {
        quietly regress `y' treated mid1scorestd `yrctrl' [pweight = `ipw'] if took100b == 1
        return scalar b_`y' = _b[treated]
    }
    ereturn clear
end

load_analysis_data
tempfile full_data
quietly save `full_data'

* ---------------------------------------------------------------------------
* 1. Took Micro B by year (models 1-5)
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

* ---------------------------------------------------------------------------
* 2. Panel A Micro B video outcomes by year (PDS and bootstrapped IPW)
* ---------------------------------------------------------------------------
capture frame drop vids_results
frame create vids_results str32 depvar str8 model double beta double se double N ///
    double meanctrl str99 ctrls str8 sample double pvalue

foreach sample in pooled 2018 2019 {
    use `full_data', clear
    if "`sample'" != "pooled" {
        keep if year == `sample'
        local yrctrl
    }
    else {
        local yrctrl y2019
    }

    * PDS (no FEs) on all Micro B enrollees (same sample as IPW and bounds)
    preserve
    keep if took100b == 1 & arm > 0
    foreach v of local panel_a {
        quietly summarize `v' if arm == 1, meanonly
        local mc = r(mean)
        quietly pdslasso `v' treated (`yrctrl' mid1scorestd $ctrl_vars), ///
            partial(`yrctrl' mid1scorestd) robust
        local vpds_`sample'_`v'_b = _b[treated]
        local vpds_`sample'_`v'_se = _se[treated]
        frame post vids_results ("`v'") ("pds") (_b[treated]) (_se[treated]) ///
            (e(N)) (`mc') ("`e(xselected)'") ("`sample'") (.)
    }
    restore

    * Bootstrapped IPW on all students who observed assignment
    * (no preserve/restore here since bootstrap uses preserve internally)
    keep if !missing(assigned_grade) & arm > 0

    * Drop covariates that are constant within this sample.
    local active_x
    foreach x of local selection_x {
        quietly summarize `x'
        if r(sd) > 0 & !missing(r(sd)) local active_x `active_x' `x'
    }

    local boot_exp
    foreach v of local panel_a {
        local boot_exp `boot_exp' b_`v'=r(b_`v')
    }
    local yropt
    if "`yrctrl'" != "" local yropt yrctrl(`yrctrl')
    bootstrap `boot_exp', reps(1000) seed(20192): ///
        _ipw_by_year, outcomes(`panel_a') selection_x(`active_x') `yropt'

    foreach v of local panel_a {
        quietly summarize `v' if took100b == 1 & arm == 1, meanonly
        local mc = r(mean)
        quietly count if took100b == 1 & !missing(`v')
        local N = r(N)
        local vipw_`sample'_`v'_b = _b[b_`v']
        local vipw_`sample'_`v'_se = _se[b_`v']
        frame post vids_results ("`v'") ("ipw") (_b[b_`v']) (_se[b_`v']) ///
            (`N') (`mc') ("") ("`sample'") (.)
    }
}

* Difference rows: 2019 - 2018
foreach v of local panel_a {
    foreach m in pds ipw {
        local db = `v`m'_2019_`v'_b' - `v`m'_2018_`v'_b'
        local dse = sqrt((`v`m'_2018_`v'_se')^2 + (`v`m'_2019_`v'_se')^2)
        local dp = 2 * normal(-abs(`db' / `dse'))
        frame post vids_results ("`v'") ("`m'") (`db') (`dse') (.) (.) ("") ("diff") (`dp')
    }
}

frame vids_results: export delimited "data/generated/microb_videos_by_year.csv", replace
