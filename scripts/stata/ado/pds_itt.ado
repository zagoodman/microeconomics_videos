* Post-double-selection lasso ITT, without and with pair fixed effects.
program pds_itt
    version 17
    args y exam
    foreach model in noFEs FEs {
        preserve
        if "`model'" == "FEs" {
            keep if bothpairs_`exam'
            xtset pairyear
            local partial mid1scorestd
            local fe fe
        }
        else {
            keep if !missing(`exam'scorestd)
            local partial y2019 mid1scorestd
            local fe
        }
        quietly summarize `y' if arm == 1
        local meanctrl = r(mean)
        pdslasso `y' treated (`partial' $ctrl_vars) if arm > 0, partial(`partial') `fe' robust
        local fe_se = _se[treated]
        if "`fe'" != "" pair_fe_se `fe_se'
        restore
        frame post results ("`y'") (`meanctrl') (_b[treated]) (`fe_se') (e(N)) ///
            ("`e(xselected)'") ("`model'")
    }
end
