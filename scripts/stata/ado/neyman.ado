program neyman
    version 17
    args y exam
    preserve
    pair_differences `y', exam(`exam')
    local N = r(N)
    local meanctrl = r(meanctrl)
    local J = r(J)
    quietly summarize d_`y', meanonly
    local diff = r(mean)
    pair_covariance d_`y' d_`y' `J'
    frame post results ("`y'") (`meanctrl') (`diff') (sqrt(r(cov))) (`N') ("Neyman")
    restore
end
