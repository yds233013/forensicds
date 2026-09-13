"""Hidden generalization fixtures for Task 05 (never present in the agent's environment).

Each fixture keeps the XP-231 design (workspace randomization at onboarding start, self-serve non-internal
eligibility, first assignment binding, 14-day workspace activation from assignment, stratified estimator) and changes
how exposures, identities, assignments and the true effect are produced.
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    # A: no true effect; strong exposure asymmetry (checklist mount rarely completes for low-intent users); many agency
    #    users in several workspaces; a 'starter' self-serve plan; strata by plan and region; more SDK retries.
    _spec(name="hidden_a", seed=8128, xp_start="2026-02-02", extract_date="2026-04-02", analysis_date="2026-04-01",
          workspaces_per_day=90, self_serve_plans={"free": 0.45, "starter": 0.30, "team": 0.25}, stratify="plan_region",
          agency_share=0.18, sdk_retry_share=0.06, rebucket_incidents=[], core_lift=0.0,
          mount_intercept=-0.4, mount_intercept_after_fix=-0.4, perf_fix_at="2099-01-01 00:00:00",
          campaigns=[], concurrent_user_xp=None),
    # B: a real positive effect; exposure asymmetry reversed (control logging drops on a slow dashboard, checklist logs
    #    reliably); larger teams; two cache-flush incidents re-bucket many workspaces; long onboarding delays.
    _spec(name="hidden_b", seed=4096, xp_start="2026-10-19", extract_date="2026-12-16", analysis_date="2026-12-15",
          workspaces_per_day=80, extra_members={"1-10": 3.5, "11-50": 7.0, "51-200": 11.0, "201+": 14.0},
          core_lift=0.45, control_log_rate=0.72, mount_intercept=3.0, mount_intercept_after_fix=3.0,
          perf_fix_at="2099-01-01 00:00:00", onboarding_lag_long_share=0.35, onboarding_lag_long_days=[1, 20],
          rebucket_incidents=[{"at": "2026-11-09 03:00:00", "share": 0.15, "lookback_days": 25},
                              {"at": "2026-11-30 22:00:00", "share": 0.10, "lookback_days": 25}],
          campaigns=[{"from": "2026-11-23", "to": "2026-11-30", "extra_per_day": 50, "intent_shift": -0.9}],
          concurrent_user_xp={"id": "XP-260", "from": "2026-10-01", "visit_rate": 0.35}),
    # C: a real negative effect; many internal test workspaces and a smaller self-serve share; the analysis date falls
    #    shortly after heavy late enrollment (maturity matters); more checklist mount failures early on.
    _spec(name="hidden_c", seed=2718, xp_start="2027-01-11", extract_date="2027-03-02", analysis_date="2027-03-01",
          workspaces_per_day=95, self_serve_share=0.62, internal_share=0.08, core_lift=-1.0,
          mount_intercept=-0.2, mount_intercept_after_fix=1.2, perf_fix_at="2027-02-15 12:00:00",
          campaigns=[{"from": "2027-02-10", "to": "2027-02-25", "extra_per_day": 60, "intent_shift": 0.4}],
          rebucket_incidents=[{"at": "2027-02-03 09:30:00", "share": 0.08, "lookback_days": 14}],
          concurrent_user_xp={"id": "XP-270", "from": "2027-01-18", "visit_rate": 0.15}),
]
