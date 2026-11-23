program late_2sls
    version 17
    args y exam
    preserve
    keep if !missing(`y') & arm > 0
    replace videos_`exam'_u = videos_`exam'_u / 10
    quietly count if !missing(`y')
    local N = r(N)
    quietly summarize `y' if arm == 1
    local meanctrl = r(mean)
    foreach endog in videos duration {
        local x `endog'_`exam'_u
        ivregress 2sls `y' mid1scorestd y2019 (`x' = treated), vce(robust)
        frame post results ("`y'") (`meanctrl') (_b[`x']) (_se[`x']) (`N') ///
            ("late_`=substr("`endog'", 1, 1)'")
    }
    restore
end
