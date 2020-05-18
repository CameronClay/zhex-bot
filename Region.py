NA = 'NA'
EU = 'EU'
ALL = 'ALL'

REGIONS = [NA, EU]
VALID_REGIONS = REGIONS.copy()
VALID_REGIONS.append(ALL)

def Valid(region):
    return region in VALID_REGIONS

def ToList(region):
    if Valid(region):
        return REGIONS if region == ALL else [region]
        
    return []