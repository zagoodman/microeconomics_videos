program itt_ols
    version 17
    args y exam
    preserve
    keep if !missing(`exam'scorestd) & !missing(`y') & arm > 0
    quietly summarize `y' if arm == 1
    local meanctrl = r(mean)
    regress `y' treated mid1scorestd y2019, robust
    frame post results ("`y'") (`meanctrl') (_b[treated]) (_se[treated]) (e(N)) ("itt")
    restore
end
