"""Graded tolerances for P20, with the basis for each.

Every graded quantity is a deterministic function of the extract, so the tolerances are not sampling allowances.
They exist to admit the legitimate choices a competent analyst can make - chiefly the length of the recent
window - without admitting a different population or a different scoring basis. The AUC allowance of 0.02 covers
a window two weeks shorter or longer than the twelve the readout uses; the control-arm AUC moves by about 0.01
over that range and its own standard error is about 0.009.
"""
AUC = 0.02
DEFECT_SHARE_PP = 3.0
EFFECT_PP = 3.0
ATTRIBUTION = 0.025
ATTRIBUTION_SUM = 0.012
POPULATION_N_REL = 0.20      # the evaluated population's size, relative, to admit a different window
