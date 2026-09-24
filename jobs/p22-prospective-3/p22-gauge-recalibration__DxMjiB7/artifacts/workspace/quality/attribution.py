"""Attribution of a change in the disposition rate.
"""

def attribute(baseline_pct, reported_pct, post_corrected_pct):
    change = reported_pct - baseline_pct
    measurement_system = reported_pct - post_corrected_pct
    material = post_corrected_pct - baseline_pct
    
    return {
        "material": round(material, 2),
        "measurement_system": round(measurement_system, 2),
        "tooling": 0.0,
        "operator": 0.0,
        "other": 0.0,
    }


def family_effect(rows):
    # This is a placeholder as the previous implementation was not used for the final attribution
    # and we are now using a more direct measurement system correction.
    return None
