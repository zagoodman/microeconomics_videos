* Post-double-selection lasso 2SLS, without and with pair fixed effects.
program pds_iv
    version 17
    args y exam
    preserve
    keep if !missing(`y') & arm > 0
    replace videos_`exam'_u = videos_`exam'_u / 10
    foreach model in IV IVFE {
        if "`model'" == "IVFE" {
            keep if bothpairs_`exam'
            xtset pairyear
            local partial mid1scorestd
            local fe fe
        }
        else {
            local partial y2019 mid1scorestd
            local fe
        }
        quietly summarize `y' if arm == 1
        local meanctrl = r(mean)
        foreach endog in videos duration {
            local x `endog'_`exam'_u
            ivlasso `y' (`partial' $ctrl_vars) (`x' = treated), partial(`partial' treated) `fe' robust
            local fe_se = _se[`x']
            if "`fe'" != "" pair_fe_se `fe_se'
            frame post results ("`y'") (`meanctrl') (_b[`x']) (`fe_se') (e(N)) ///
                ("`e(xselected)'") ("PDS_`model'_`=substr("`endog'", 1, 1)'")
        }
    }
    restore
end
