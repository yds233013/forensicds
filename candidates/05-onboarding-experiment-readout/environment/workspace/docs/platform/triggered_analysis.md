# Triggered (exposure-based) analysis - XPP-12

Owner: Experimentation Platform. 2026-05-28.

Many experiments change a surface that only some assigned units reach. Analyzing all assigned units dilutes the
effect; restricting to units that reached the surface ("triggered" units) increases sensitivity.

A triggered analysis compares like with like only if the trigger condition is evaluated in the same way in every
arm, including control (counterfactual logging): the control arm must log at the point where treatment *would*
have been shown, under the same conditions. Otherwise the triggered populations differ between arms.

xp_analysis 3.0 made exposure-triggered units the readout default. Experiment plans take precedence.
