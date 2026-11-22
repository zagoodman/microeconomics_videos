* Effective F (Montiel Olea-Pflueger) and Anderson-Rubin confidence sets.
version 17
do "scripts/stata/_setup.do"

load_analysis_data
keep if arm > 0

capture frame drop results
frame create results str16 exam str16 endog double f_eff double ar_chi2 double ar_p str64 ar_cset

foreach exam in mid2 final {
    replace videos_`exam'_u = videos_`exam'_u / 10
    foreach endog in videos duration {
        ivreg2 `exam'scorestd mid1scorestd y2019 (`endog'_`exam'_u = treated), robust
        weakivtest
        local f_eff = r(F_eff)
        weakiv ivreg2 `exam'scorestd mid1scorestd y2019 (`endog'_`exam'_u = treated), ///
            robust gridpoints(2500)
        frame post results ("`exam'") ("`endog'") (`f_eff') (e(ar_chi2)) (e(ar_p)) ("`e(ar_cset)'")
    }
}

frame results: export delimited "data/generated/weak_iv.csv", replace
