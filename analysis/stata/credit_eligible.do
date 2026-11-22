* Tables 4 and 5 re-estimated with credit-eligible video counts (*_cr columns).
version 17
do "analysis/stata/_setup.do"

load_analysis_data

* ---------------------------------------------------------------------------
* 1. First stage (Table 4 with credit-eligible video counts)
* ---------------------------------------------------------------------------
capture frame drop fs_results
frame create fs_results str8 exam str24 measure model double beta double se ///
    long N double meanctrl str99 ctrls

foreach exam in mid2 final {
    foreach mspec in ///
        `"Videos|videos_`exam'_cr"' ///
        `"Unique videos|videos_`exam'_cr_u"' ///
        `"Hours of videos|duration_`exam'_cr"' ///
        `"Hours of unique videos|duration_`exam'_cr_u"' {
        gettoken mlabel v : mspec, parse("|")
        local v = substr("`v'", 2, .)

        * Control mean on Model (1)/(3) sample (matching Table 4).
        quietly summarize `v' if !missing(`exam'scorestd) & arm == 1, meanonly
        local meanctrl = r(mean)

        * Model (1): OLS with midterm 1 score and year
        quietly regress `v' treated mid1scorestd y2019 if !missing(`exam'scorestd) & arm > 0, robust
        frame post fs_results ("`exam'") ("`mlabel'") (1) (_b[treated]) (_se[treated]) ///
            (e(N)) (`meanctrl') ("")

        * Model (2): Neyman matched-pair difference in means
        preserve
        pair_differences `v', exam(`exam')
        local N = r(N)
        local J = r(J)
        quietly summarize d_`v', meanonly
        local diff = r(mean)
        pair_covariance d_`v' d_`v' `J'
        frame post fs_results ("`exam'") ("`mlabel'") (2) (`diff') (sqrt(r(cov))) ///
            (`N') (`meanctrl') ("")
        restore

        * Model (3): PDS without pair FEs
        preserve
        keep if !missing(`exam'scorestd) & arm > 0
        quietly pdslasso `v' treated (y2019 mid1scorestd $ctrl_vars), ///
            partial(y2019 mid1scorestd) robust
        frame post fs_results ("`exam'") ("`mlabel'") (3) (_b[treated]) (_se[treated]) ///
            (e(N)) (`meanctrl') ("`e(xselected)'")
        restore

        * Model (4): PDS with pair FEs (+ pair_fe_se adjustment)
        preserve
        keep if bothpairs_`exam' & arm > 0
        xtset pairyear
        quietly pdslasso `v' treated (mid1scorestd $ctrl_vars), ///
            partial(mid1scorestd) fe robust
        local fe_se = _se[treated]
        pair_fe_se `fe_se'
        frame post fs_results ("`exam'") ("`mlabel'") (4) (_b[treated]) (`fe_se') ///
            (e(N)) (`meanctrl') ("`e(xselected)'")
        restore
    }
}

frame fs_results: export delimited "data/generated/credit_firststage_coeffs.csv", replace

* ---------------------------------------------------------------------------
* 2. Second stage (Table 5 with credit-eligible video counts)
* ---------------------------------------------------------------------------
capture frame drop ss_results
frame create ss_results str8 exam str16 row model double beta double se long N str99 ctrls

foreach exam in mid2 final {
    local y `exam'scorestd
    local dur duration_`exam'_cr_u
    tempvar vid10
    generate double `vid10' = videos_`exam'_cr_u / 10

    * Reduced Form (RF)
    quietly regress `y' treated mid1scorestd y2019 if !missing(`y') & arm > 0, robust
    frame post ss_results ("`exam'") ("RF") (1) (_b[treated]) (_se[treated]) (e(N)) ("")

    preserve
    pair_differences `y', exam(`exam')
    local N = r(N)
    local J = r(J)
    quietly summarize d_`y', meanonly
    local diff = r(mean)
    pair_covariance d_`y' d_`y' `J'
    frame post ss_results ("`exam'") ("RF") (2) (`diff') (sqrt(r(cov))) (`N') ("")
    restore

    preserve
    keep if !missing(`y') & arm > 0
    quietly pdslasso `y' treated (y2019 mid1scorestd $ctrl_vars), ///
        partial(y2019 mid1scorestd) robust
    frame post ss_results ("`exam'") ("RF") (3) (_b[treated]) (_se[treated]) ///
        (e(N)) ("`e(xselected)'")
    restore

    preserve
    keep if bothpairs_`exam' & arm > 0
    xtset pairyear
    quietly pdslasso `y' treated (mid1scorestd $ctrl_vars), ///
        partial(mid1scorestd) fe robust
    local fe_se = _se[treated]
    pair_fe_se `fe_se'
    frame post ss_results ("`exam'") ("RF") (4) (_b[treated]) (`fe_se') ///
        (e(N)) ("`e(xselected)'")
    restore

    * 2SLS: per 10 credit-eligible unique videos & per hour of credit-eligible unique content
    foreach rspec in `"2SLS_videos10|`vid10'"' `"2SLS_hours|`dur'"' {
        gettoken rlabel d : rspec, parse("|")
        local d = substr("`d'", 2, .)

        * Model (1): 2SLS with midterm 1 score and year
        quietly ivregress 2sls `y' mid1scorestd y2019 (`d' = treated) if !missing(`y') & arm > 0, vce(robust)
        frame post ss_results ("`exam'") ("`rlabel'") (1) (_b[`d']) (_se[`d']) (e(N)) ("")

        * Model (2): Neyman LATE (Wald ratio of pair-difference means)
        preserve
        pair_differences `y' `d', exam(`exam')
        local N = r(N)
        local J = r(J)
        quietly summarize d_`y', meanonly
        local itt = r(mean)
        pair_covariance d_`y' d_`y' `J'
        local var_itt = r(cov)
        quietly summarize d_`d', meanonly
        local fs = r(mean)
        pair_covariance d_`d' d_`d' `J'
        local var_fs = r(cov)
        pair_covariance d_`y' d_`d' `J'
        local late = `itt' / `fs'
        local se = abs(`late') * sqrt(`var_itt' / (`itt')^2 + `var_fs' / (`fs')^2 - 2 * r(cov) / ((`itt') * (`fs')))
        frame post ss_results ("`exam'") ("`rlabel'") (2) (`late') (`se') (`N') ("")
        restore

        * Model (3): PDS IV without pair FEs
        preserve
        keep if !missing(`y') & arm > 0
        quietly ivlasso `y' (y2019 mid1scorestd $ctrl_vars) (`d' = treated), ///
            partial(y2019 mid1scorestd treated) robust
        frame post ss_results ("`exam'") ("`rlabel'") (3) (_b[`d']) (_se[`d']) ///
            (e(N)) ("`e(xselected)'")
        restore

        * Model (4): PDS IV with pair FEs (+ pair_fe_se adjustment)
        preserve
        keep if bothpairs_`exam' & arm > 0
        xtset pairyear
        quietly ivlasso `y' (mid1scorestd $ctrl_vars) (`d' = treated), ///
            partial(mid1scorestd treated) fe robust
        local fe_se = _se[`d']
        pair_fe_se `fe_se'
        frame post ss_results ("`exam'") ("`rlabel'") (4) (_b[`d']) (`fe_se') ///
            (e(N)) ("`e(xselected)'")
        restore
    }

    drop `vid10'
}

frame ss_results: export delimited "data/generated/credit_secondstage_coeffs.csv", replace
