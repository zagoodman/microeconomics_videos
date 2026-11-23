* Neyman (co)variance of two pair-difference means: sum((a - abar)(b - bbar)) / (J(J - 1)).
program pair_covariance, rclass
    version 17
    args a b J
    tempvar product
    quietly summarize `a', meanonly
    local abar = r(mean)
    quietly summarize `b', meanonly
    generate `product' = (`a' - `abar') * (`b' - r(mean))
    quietly summarize `product', meanonly
    return scalar cov = r(sum) / (`J' * (`J' - 1))
end
