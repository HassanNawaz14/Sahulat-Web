def compute_confidence(report_count: int) -> float:
    if report_count >= 10:
        return 0.92
    if report_count >= 5:
        return 0.82
    if report_count >= 3:
        return 0.65
    if report_count >= 1:
        return 0.45
    return 0.25
