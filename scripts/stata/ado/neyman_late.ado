* Wald ratio of pair-difference means; delta-method SE.
program neyman_late
    version 17
    args y exam
    preserve
    replace videos_`exam'_u = videos_`exam'_u / 10
    pair_differences `y' videos_`exam'_u duration_`exam'_u, exam(`exam')
    local N = r(N)
    local meanctrl = r(meanctrl)
    local J = r(J)
    quietly summarize d_`y', meanonly
    local itt = r(mean)
    pair_covariance d_`y' d_`y' `J'
    local var_itt = r(cov)
    foreach endog in videos duration {
        local fs_var d_`endog'_`exam'_u
        quietly summarize `fs_var', meanonly
        local fs = r(mean)
        pair_covariance `fs_var' `fs_var' `J'
        local var_fs = r(cov)
        pair_covariance d_`y' `fs_var' `J'
        local late = `itt' / `fs'
        local se = abs(`late') * sqrt(`var_itt' / (`itt')^2 + `var_fs' / (`fs')^2 - 2 * r(cov) / ((`itt') * (`fs')))
        frame post results ("`y'") (`meanctrl') (`late') (`se') (`N') ("N_late_`=substr("`endog'", 1, 1)'")
    }
    restore
end
