"""Graded tolerances for P22, with the basis for each.

Every tolerance is set from the measured spread of the *legitimate* estimators of the same quantity across the
four graded extracts (see tools/p22/method_audit.json), at roughly 1.5-2x the worst case. None of them was
chosen to make a particular solution pass.
"""
# Offset on the BORE_DIA_42 feature, per machine, in micrometres.
# Worst observed spread between the retained-artefact bridge, the two-machine difference in differences and the
# design value: 0.75 um. Tolerance 1.2 um.
OFFSET_UM = 1.2

# Direct counts over ~12,000 parts; binomial SE is about 0.15 pp. No estimation is involved.
RATE_DIRECT_PP = 0.3

# The corrected rate inherits the offset's uncertainty at about 0.39 pp per um, and the coarsest accepted route
# (the un-recalibrated machine's own rate, SE 0.28 pp) sits 0.47 pp away on one extract. Tolerance 0.7 pp.
RATE_CORRECTED_PP = 0.7

# Attribution components are differences of corrected rates. Worst observed estimator spread 0.49 pp.
ATTRIBUTION_PP = 0.8

# The five components must add to the observed change; the contract states 0.2 pp, allowed 0.25 for rounding.
ATTRIBUTION_SUM_PP = 0.25

# Strata are direct counts; strata with fewer than 400 parts are not graded.
STRATUM_PP = 0.5
STRATUM_MIN_N = 400

# part_dispositions.csv must agree with the rate the readout states.
CSV_CONSISTENCY_PP = 0.15
