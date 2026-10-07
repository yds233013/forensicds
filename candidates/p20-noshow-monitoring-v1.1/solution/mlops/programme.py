"""The reminder programme's effect, estimated from the clinics left outside it.

The comparison is confined to the score band the programme acts on, because that is the only band in which any
patient was called, and it is stratified by clinic size band because that is how the excluded set was drawn.
"""
from mlops import metrics


def calling_threshold(con, percentile, pre_weeks_end):
    """The threshold the programme fixed at start, reproduced from the pre-programme score distribution."""
    rows = con.execute(
        "SELECT s.score AS score FROM model_scores s JOIN appointments a ON a.appt_id = s.appt_id "
        "WHERE s.model_version = 'noshow-v3.1' AND a.week < ?", (pre_weeks_end,)).fetchall()
    scores = sorted(r["score"] for r in rows)
    if not scores:
        return None
    return scores[int((1.0 - percentile) * len(scores))]


def effect_pp(rows, excluded, size_band, threshold):
    """Size-stratified difference in the no-show rate inside the called band: excluded clinics less programme
    clinics. Weighted by the excluded arm's counts, which is the population the difference is reported for."""
    num = den = 0.0
    per_band = {}
    bands = sorted({size_band[r["clinic_id"]] for r in rows})
    for band in bands:
        ctrl = [r for r in rows if r["clinic_id"] in excluded
                and size_band[r["clinic_id"]] == band and r["score_v31"] >= threshold]
        prog = [r for r in rows if r["clinic_id"] not in excluded
                and size_band[r["clinic_id"]] == band and r["score_v31"] >= threshold]
        if len(ctrl) < 50 or len(prog) < 50:
            continue
        rc, rp = metrics.no_show_rate_pct(ctrl), metrics.no_show_rate_pct(prog)
        per_band[band] = {"n_control": len(ctrl), "n_programme": len(prog), "diff_pp": rc - rp}
        num += (rc - rp) * len(ctrl)
        den += len(ctrl)
    return (num / den if den else None), per_band
