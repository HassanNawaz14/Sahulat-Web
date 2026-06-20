FEEDER_AREA_MAP: dict[str, list[str]] = {
    "model-town-feeder": ["model-town", "gulberg"],
    "garden-town-feeder": ["garden-town", "samnabad"],
    "faisal-town-feeder": ["faisal-town", "johar-town"],
    "defence-feeder": ["dha", "defence"],
    "cantt-feeder": ["cantt", "lahore-cantt"],
    "iqbal-town-feeder": ["iqbal-town", "wafaqi-colony"],
    "nishter-town-feeder": ["nishter-town", "multan-road"],
    "samanabad-feeder": ["samnabad", "samanabad"],
    "gulberg-feeder": ["gulberg", "liberty"],
    "johar-town-feeder": ["johar-town", "johar-block"],
}


def lookup_area(feeder_name: str) -> list[str]:
    key = feeder_name.strip().lower().replace(" ", "-")
    for pattern, tags in FEEDER_AREA_MAP.items():
        if pattern in key or key in pattern:
            return tags
    return [feeder_name.strip().lower()]
