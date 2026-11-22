version 17
do "scripts/stata/_setup.do"

local blocking mid1scorestd y2019
local interact_vars `blocking' videos_mid1 videos_mid1_u transfer female white asian latx othereth
local outcomes mid2scorestd finalscorestd

load_analysis_data

capture frame drop results
frame create results str32 depvar str32 interactvar meanctrl interactbeta stderr N

foreach v of local interact_vars {
    generate inter_`v' = treated * `v'
    foreach y of local outcomes {
        quietly summarize `y' if arm == 1
        local meanctrl = r(mean)
        local main = cond(`: list v in blocking', "", "`v'")
        quietly regress `y' treated inter_`v' mid1scorestd y2019 `main' if arm > 0, robust
        frame post results ("`y'") ("`v'") (`meanctrl') (_b[inter_`v']) (_se[inter_`v']) (e(N))
    }
}

frame results: export delimited "data/generated/het_coeffs.csv", replace

* Multiple-hypothesis adjustment (List, Shaikh and Xu); log output only.
local not_tested videos_mid1
local mht_vars : list interact_vars - not_tested
local equations
foreach v of local mht_vars {
    local main = cond(`: list v in blocking', "", "`v'")
    foreach y of local outcomes {
        local equations `equations' (`y' inter_`v' `main' treated mid1scorestd y2019)
    }
}
preserve
keep if arm > 0
set seed 20191
mhtreg `equations'
restore
