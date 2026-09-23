# G44 concept screen — assay positive predictive value under a two-stage testing workflow

Coverage area 9 of FORENSICDS-10: calibration and deployment shift. Designed against principle 17: the
laboratory documents describe the **workflow** (who gets confirmatory testing, how the audit sample is
drawn, how the validation panel was assembled) and never state the statistical consequence. The object
has to be derived from how the data came to exist, as in Task02, G05, G10, G24 and G34.

## Setting

A diagnostics laboratory runs a two-stage workflow for a screening assay:

1. every routine specimen gets the rapid screen;
2. every **screen-positive** goes to the confirmatory assay (the reference standard);
3. a **systematic 1-in-N sample of screen-negatives** also goes to the confirmatory assay, as the
   quality agreement's audit requires.

The client contract is written on the assay's **positive predictive value in the routine population**:
below 0.80 the laboratory must add a second confirmatory step at its own cost.

The vendor's validation report quotes PPV = 0.94, measured on an **enriched panel** in which known
positives were oversampled. The laboratory's own monitoring quotes a similar number, computed from the
specimens that happen to have confirmatory results.

## Why both published numbers are wrong

- The panel's PPV is a property of the panel's prevalence, not of the routine population. Sensitivity
  and specificity transport; PPV does not.
- Among specimens with a confirmatory result, screen-positives are present in full and screen-negatives
  only at 1-in-N. Computing anything on "specimens with a confirmatory result" as though it were the
  routine population is verification bias — and it is the natural query to write, because those are the
  only rows with a truth column.

The contract object is the PPV the routine population would show: the panel's sensitivity and
specificity applied to the routine prevalence, where the routine prevalence is recovered from the
confirmatory results using the **known** sampling design (positives sampled with certainty,
negatives at a known fraction). The weights are known exactly, as in G24, so the estimate is a
deterministic function of the extract and can be graded exactly.

## Candidate wrong objects (labelled before any number is read)

W01 the vendor panel's PPV quoted directly · W02 PPV computed on all confirmed specimens (verification
bias) · W03 prevalence taken as the screen-positive rate · W04 prevalence taken from confirmed
positives over all specimens · W05 audit sampling weights ignored · W06 screen-negatives without a
confirmatory result treated as true negatives · W07 sensitivity and specificity taken from routine data
rather than the panel (where negatives are unverified) · W08 accuracy or F1 substituted for PPV · W09
NPV reported as PPV · W10 panel enrichment ratio applied to PPV rather than to prevalence · W11
prevalence estimated over the wrong denominator (specimens vs patients, repeat testing) · W12 PPV
pooled across assay lots when the contract is written per lot in force.

## Gate (must pass before any build)

1. the remediation decision must not be constant across the graded extracts;
2. each wrong object must move the graded PPV by more than the reporting precision (0.001) on at least
   three of four extracts, and at least three must flip the remediation decision somewhere;
3. two independent computational routes must agree on the truth exactly;
4. **principle 17 check**: no workspace document may state that PPV depends on prevalence, or give the
   transport formula; the documents describe only the workflow, the audit design and the panel's
   construction.
