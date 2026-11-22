program mark_complete_pairs
    version 17
    args score name
    bysort pair year: egen `name' = total(!missing(`score'))
    replace `name' = `name' >= 2
end
