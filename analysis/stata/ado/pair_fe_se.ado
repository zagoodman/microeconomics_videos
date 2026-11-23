* ivlasso/pdslasso 1.1.02 omit the pair-FE degrees-of-freedom correction N / (N - G).
program pair_fe_se
    version 17
    args se
    quietly levelsof pairyear if e(sample)
    local adjusted = `se' * sqrt(e(N) / (e(N) - r(r)))
    c_local fe_se `adjusted'
end
