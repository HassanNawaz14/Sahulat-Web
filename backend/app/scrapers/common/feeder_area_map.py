FEEDER_AREA_MAP: dict[str, list[str]] = {
    # LESCO — Lahore
    "model-town-feeder": ["model-town", "gulberg"],
    "garden-town-feeder": ["garden-town", "samnabad"],
    "faisal-town-feeder": ["faisal-town", "johar-town"],
    "defence-feeder": ["dha", "defence"],
    "dha-r-block": ["dha-phase-5", "dha-r-block"],
    "dha-y-block": ["dha-phase-5", "dha-y-block"],
    "dha-x-block": ["dha-phase-5", "dha-x-block"],
    "dha-phase-6-feeder": ["dha-phase-6", "dha"],
    "cantt-feeder": ["cantt", "lahore-cantt"],
    "iqbal-town-feeder": ["iqbal-town", "wafaqi-colony"],
    "nishter-town-feeder": ["nishter-town", "multan-road"],
    "samanabad-feeder": ["samnabad", "samanabad"],
    "gulberg-feeder": ["gulberg", "liberty"],
    "johar-town-feeder": ["johar-town", "johar-block"],
    "township-feeder": ["township", "new-garden-town"],
    "valencia-feeder": ["valencia", "valencia-town"],
    "bahria-town-feeder": ["bahria-town", "bahria"],
    "lake-city-feeder": ["lake-city", "raiwind"],
    "wapda-town-feeder": ["wapda-town", "wapda"],
    "shahdara-feeder": ["shahdara", "shahdara-town"],
    "wassanpura-feeder": ["wassanpura", "wassan"],
    "allama-iqbal-town-feeder": ["allama-iqbal-town", "iqbal-town"],
    "raiwind-feeder": ["raiwind", "raiwind"],
    "saddar-feeder": ["saddar", "lahore-saddar"],
    "shadman-feeder": ["shadman", "shadman-colony"],
    "ichhra-feeder": ["ichhra", "ichhra-bazaar"],
    "anarkali-feeder": ["anarkali", "anarkali-bazaar"],
    "hall-road-feeder": ["hall-road", "hall-road-area"],
    "mcleod-road-feeder": ["mcleod-road", "mcleod"],
    "upper-mall-feeder": ["upper-mall", "mall-road"],
    "lower-mall-feeder": ["lower-mall", "mall-road"],
    "firdous-market-feeder": ["firdous-market", "firdous"],
    "muslim-town-feeder": ["muslim-town", "muslimabad"],
    "nazimabad-feeder": ["nazimabad", "karachi-nazimabad"],

    # GEPCO — Gujranwala
    "gujranwala-cantt-feeder": ["gujranwala-cantt", "cantt"],
    "model-town-grw-feeder": ["gujranwala-model-town", "model-town"],

    # IESCO — Islamabad
    "f-6-feeder": ["f-6", "islamabad-f-6"],
    "f-7-feeder": ["f-7", "islamabad-f-7"],
    "f-8-feeder": ["f-8", "islamabad-f-8"],
    "f-10-feeder": ["f-10", "islamabad-f-10"],
    "g-9-feeder": ["g-9", "islamabad-g-9"],
    "i-8-feeder": ["i-8", "islamabad-i-8"],
    "rawalpindi-cantt-feeder": ["rawalpindi-cantt", "cantt"],
    "saddar-rwp-feeder": ["rawalpindi-saddar", "saddar"],
}

DEFAULT_CITY_MAP: dict[str, str] = {
    "lesco": "lahore",
    "gepco": "gujranwala",
    "fesco": "faisalabad",
    "iesco": "islamabad",
    "mepco": "multan",
    "pesco": "peshawar",
    "qesco": "quetta",
    "hesco": "hyderabad",
    "sepco": "sukkur",
    "kelectric": "karachi",
    "sngpl": "lahore",
    "ssgc": "karachi",
    "wasa_lhr": "lahore",
    "kwsb": "karachi",
    "ptcl": "lahore",
    "nayatel": "islamabad",
}


def lookup_area(feeder_name: str) -> list[str]:
    key = feeder_name.strip().lower().replace(" ", "-")
    # Match by longest suffix first to avoid substring collisions
    # e.g. "dha-r-block" should match before "block" matches something else
    sorted_keys = sorted(FEEDER_AREA_MAP.keys(), key=len, reverse=True)
    for pattern in sorted_keys:
        if key.endswith(pattern) or pattern.endswith(key):
            return FEEDER_AREA_MAP[pattern]
    return [feeder_name.strip().lower()]


def default_city(provider_code: str) -> str:
    return DEFAULT_CITY_MAP.get(provider_code, "lahore")
