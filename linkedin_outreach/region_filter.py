"""
Region and Location Filter for LinkedIn Connections.
Categorizes connections geographically:
- Explicitly EXCLUDES India (domestic on-site not in scope).
- Prioritizes Target Regions:
    Tier 1: Europe (UK & Ireland priority; Germany, Netherlands, France, Switzerland, Nordics)
    Tier 2: United States & Canada
    Tier 3: Singapore
    Tier 4: Middle East (Dubai / UAE, Saudi Arabia, Qatar)
- Retains non-matching regions as Backlog (QUEUED_LATER).
"""

import re
from typing import Tuple, Dict, Any, Optional

# Patterns for India (to be strictly excluded from international relocation/remote outreach)
INDIA_KEYWORDS = [
    r"\bindia\b",
    r"\bbengaluru\b", r"\bbangalore\b",
    r"\bmumbai\b", r"\bbombay\b",
    r"\bdelhi\b", r"\bnew delhi\b", r"\bncr\b",
    r"\bhyderabad\b",
    r"\bpune\b",
    r"\bchennai\b", r"\bmadras\b",
    r"\bgurugram\b", r"\bgurgaon\b",
    r"\bnoida\b",
    r"\bkolkata\b", r"\bcalcutta\b",
    r"\bahmedabad\b",
    r"\bkarnataka\b", r"\bmaharashtra\b", r"\btamil nadu\b", r"\btelangana\b",
    r"\bharyana\b", r"\buttar pradesh\b", r"\bgujarat\b", r"\bkerala\b"
]

# Patterns for Africa (strictly excluded from international career/relocation outreach)
AFRICA_KEYWORDS = [
    r"\bafrica\b",
    r"\begypt\b", r"\bcairo\b", r"\balexandria\b", r"\bgiza\b",
    r"\bnigeria\b", r"\blagos\b", r"\babuja\b",
    r"\bsouth africa\b", r"\bjohannesburg\b", r"\bcape town\b", r"\bpretoria\b", r"\bdurban\b",
    r"\bkenya\b", r"\bnairobi\b", r"\bmombasa\b",
    r"\bghana\b", r"\baccra\b",
    r"\bmorocco\b", r"\bcasablanca\b", r"\brabat\b", r"\bmarrakech\b",
    r"\btunisia\b", r"\btunis\b",
    r"\balgeria\b", r"\balgiers\b",
    r"\bethiopia\b", r"\baddis ababa\b",
    r"\brwanda\b", r"\bkigali\b",
    r"\buganda\b", r"\bkampala\b",
    r"\btanzania\b", r"\bdar es salaam\b",
    r"\bcameroon\b", r"\byaounde\b", r"\bdouala\b",
    r"\bivory coast\b", r"\bcote d'ivoire\b", r"\babidjan\b",
    r"\bsenegal\b", r"\bdakar\b",
    r"\bzimbabwe\b", r"\bharare\b",
    r"\bzambia\b", r"\blusaka\b",
    r"\bmauritius\b"
]

# Patterns for Target Regions
TIER_1_EUROPE = [
    # UK & Ireland (Top Priority)
    r"\bunited kingdom\b", r"\buk\b", r"\blondon\b", r"\bengland\b", r"\bscotland\b",
    r"\bwales\b", r"\bmanchester\b", r"\bedinburgh\b", r"\bbirmingham\b", r"\bcambridge\b",
    r"\boxford\b", r"\bbristol\b", r"\bleeds\b", r"\bbelfast\b", r"\bnorthern ireland\b",
    r"\bireland\b", r"\bdublin\b", r"\bcork\b", r"\bgalway\b", r"\bsouthampton\b",
    # Western, Central & Northern Europe
    r"\bgermany\b", r"\bberlin\b", r"\bmunich\b", r"\bfrankfurt\b", r"\bhamburg\b",
    r"\bnetherlands\b", r"\bamsterdam\b", r"\brotterdam\b", r"\butrecht\b",
    r"\bfrance\b", r"\bparis\b",
    r"\bswitzerland\b", r"\bzurich\b", r"\bgeneva\b", r"\blaussanne\b",
    r"\bsweden\b", r"\bstockholm\b",
    r"\bnorway\b", r"\boslo\b",
    r"\bdenmark\b", r"\bcopenhagen\b",
    r"\bfinland\b", r"\bhelsinki\b",
    r"\baustria\b", r"\bvienna\b",
    r"\bbelgium\b", r"\bbrussels\b",
    r"\bspain\b", r"\bbarcelona\b", r"\bmadrid\b", r"\bzaragoza\b",
    r"\bportugal\b", r"\blisbon\b", r"\bporto\b",
    r"\bitaly\b", r"\bmilan\b", r"\brome\b",
    r"\bpoland\b", r"\bwarsaw\b", r"\bkrakow\b",
    r"\bhungary\b", r"\bbudapest\b",
    r"\bbulgaria\b", r"\bsofia\b",
    r"\bczech\b", r"\bprague\b",
    r"\bestonia\b", r"\btallinn\b",
    r"\bluxembourg\b",
    r"\bcyprus\b",
    r"\beurope\b",
    # Australia & New Zealand (Tier 1 English-Speaking Overseas Tech Hubs)
    r"\baustralia\b", r"\bsydney\b", r"\bmelbourne\b", r"\bbrisbane\b", r"\bperth\b",
    r"\bnew zealand\b", r"\bauckland\b"
]

TIER_2_NORTH_AMERICA = [
    # United States
    r"\bunited states\b", r"\busa\b", r"\bu\.s\.\b", r"\bsan francisco\b", r"\bsf bay\b",
    r"\bsilicon valley\b", r"\bcalifornia\b", r"\bnew york\b", r"\bnyc\b", r"\bseattle\b",
    r"\bwashington\b", r"\baustin\b", r"\btexas\b", r"\bhouston\b", r"\bdallas\b",
    r"\bboston\b", r"\bmassachusetts\b", r"\bchicago\b", r"\billinois\b",
    r"\blos angeles\b", r"\bdenver\b", r"\bcolorado\b", r"\batlanta\b", r"\bgeorgia\b",
    r"\bmiami\b", r"\bflorida\b", r"\borlando\b", r"\bphiladelphia\b", r"\bpennsylvania\b",
    r"\bsan diego\b", r"\bsan jose\b", r"\bphoenix\b", r"\barizona\b",
    r"\bpittsburgh\b", r"\bbaltimore\b", r"\bmaryland\b", r"\bvirginia\b",
    r"\bnorth carolina\b", r"\braleigh\b", r"\bcharlotte\b",
    # Canada
    r"\bcanada\b", r"\btoronto\b", r"\bvancouver\b", r"\bmontreal\b", r"\bontario\b",
    r"\bbritish columbia\b", r"\bquebec\b", r"\bottawa\b", r"\bwaterloo\b",
    r"\balberta\b", r"\bedmonton\b", r"\bcalgary\b"
]

TIER_3_SINGAPORE = [
    r"\bsingapore\b", r"\bsg\b"
]

TIER_4_MIDDLE_EAST = [
    r"\bdubai\b", r"\babu dhabi\b", r"\bunited arab emirates\b", r"\buae\b",
    r"\bsaudi arabia\b", r"\briyadh\b", r"\bjeddah\b",
    r"\bqatar\b", r"\bdoha\b"
]

def classify_location(location_str: Optional[str]) -> Tuple[bool, str, str]:
    """
    Classifies a connection's location.
    
    Returns:
        (is_eligible, tier_label, normalized_region)
        - is_eligible: True if matches Tier 1, 2, 3, or 4 and is NOT in India.
        - tier_label: E.g. 'Tier 1 (Europe)', 'Tier 2 (North America)', 'Excluded (India)', 'Queued (Other)'
        - normalized_region: Short region code ('europe', 'north_america', 'singapore', 'middle_east', 'india', 'other')
    """
    if not location_str or not isinstance(location_str, str):
        return False, "Queued (Unknown Location)", "unknown"

    loc_lower = location_str.lower()

    # 1. Check India Exclusion
    for pattern in INDIA_KEYWORDS:
        if re.search(pattern, loc_lower):
            return False, "Excluded (India)", "india"

    # 2. Check Africa Exclusion
    for pattern in AFRICA_KEYWORDS:
        if re.search(pattern, loc_lower):
            return False, "Excluded (Africa)", "africa"

    # Disambiguate country Georgia (Tbilisi) from US State of Georgia
    if "tbilisi" in loc_lower:
        return False, "Queued (Other Region)", "other"

    # 3. Check Tier 1: Europe (UK & Ireland priority)
    for pattern in TIER_1_EUROPE:
        if re.search(pattern, loc_lower):
            return True, "Tier 1 (Europe)", "europe"

    # 3. Check Tier 2: North America
    for pattern in TIER_2_NORTH_AMERICA:
        if re.search(pattern, loc_lower):
            return True, "Tier 2 (North America)", "north_america"

    # 4. Check Tier 3: Singapore
    for pattern in TIER_3_SINGAPORE:
        if re.search(pattern, loc_lower):
            return True, "Tier 3 (Singapore)", "singapore"

    # 5. Check Tier 4: Middle East
    for pattern in TIER_4_MIDDLE_EAST:
        if re.search(pattern, loc_lower):
            return True, "Tier 4 (Middle East)", "middle_east"

    # Other region (retained for backlog)
    return False, "Queued (Other Region)", "other"
