* Reshapes the matched-pair sample to one row per pair with d_<var> = Incentive - Control.
program pair_differences, rclass
    version 17
    syntax varlist, exam(name)
    gettoken y : varlist
    keep if bothpairs_`exam' & arm > 0
    keep pairyear treated `varlist'
    quietly reshape wide `varlist', i(pairyear) j(treated)
    foreach v of local varlist {
        generate d_`v' = `v'1 - `v'0
        quietly drop if missing(d_`v')
    }
    quietly summarize `y'0, meanonly
    return scalar meanctrl = r(mean)
    return scalar J = _N
    return scalar N = 2 * _N
end
