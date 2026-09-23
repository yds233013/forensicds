# G44 — quarterly screening performance certificate (sampling design and base rate)

Coverage area 9 of FORENSICDS-10: calibration and deployment shift. Built after G42 was solved 3/3,
under principle 17: **nothing that resolves the object is stated in the workspace.** The documents
describe how the review queue is fed, how the benchmark panel was assembled and what the contract is
written on; they never state that the labels need weighting or that precision depends on the base rate.

## 1. The business setting

Kestrel Screening certifies each quarter that its fraud screen meets a precision floor of 0.80 on
Northwater Retail's traffic. The published certificate reports 0.998 (the marketing benchmark panel) and
0.948 (Kestrel's own flagged transactions) and certifies the quarter. The contract figure is **0.775** —
the quarter fails and the remediation clause bites.

## 2. The two derivations

**(a) The labels exist under a known but uneven design.** Every flagged transaction is reviewed; a
systematic one-in-N sample of passed transactions is reviewed; ad-hoc cases arrive from chargebacks and
escalations under no rule at all. Counting review rows as if they were a sample of traffic understates
what the screen passed by a factor of N, and mixes in cases selected *because* they turned out to be
fraud. N is in the extract's contract terms and is 10 in three extracts and 20 in one, so it cannot be
hard-coded (mutation M11 checks this).

**(b) Precision is a property of the traffic, not of the screen.** Sensitivity and specificity
transport between populations; precision does not. The benchmark panel is case-rich by construction and
Kestrel's own book runs at several times Northwater's contracted rate, so both published figures
describe populations the contract is not written on. The transport is
`se·p / (se·p + (1−sp)·(1−p))` at the contracted rate — arithmetic that no document supplies.

## 3. Identifiability

Two independent routes agree exactly on all four extracts: the generator's truth, computed from the
in-memory world before it is written to SQL, and the oracle, computed from the extract with pandas.

| Extract | sensitivity | specificity | own-traffic precision | contract precision | decision |
|---|---|---|---|---|---|
| visible  | 0.964371 | 0.997885 | 0.948044 | 0.775094 | remediate |
| hidden_a | 0.946556 | 0.998553 | 0.963087 | 0.831524 | accept |
| hidden_b | 0.962848 | 0.997790 | 0.947005 | 0.767116 | remediate |
| hidden_c | 0.887188 | 0.999032 | 0.964126 | 0.873740 | accept |

Two accept, two remediate; the closest margin to the floor is 0.025, an order of magnitude larger than
the grading tolerance (5e-5) and far smaller than every wrong construction in the panel.

## 4. Pre-build wrong-object panel

Twelve wrong objects, labelled before any number was read (`tools/g44/panel.py`), **all twelve separated
on all four extracts**, and ten of the twelve flip the certification decision on at least two
(`tools/g44/panel_results.json`). The two that never flip it — including ad-hoc reviews (−0.003 to
−0.009) and treating unsampled passes as verified negatives (+0.004 to +0.016) — still miss the graded
figure by more than the tolerance, and they are the two errors that a careful analyst is least likely
to make, so the task does not turn on them.

The largest errors are the ones the published certificate actually makes: quoting the panel (+0.13 to
+0.23), quoting own-traffic precision (+0.09 to +0.18), and ignoring the sample weights (−0.44 to
−0.62).

## 5. Why this should be harder than G42

G42's rules were all stated, and the model applied them in three trials out of three at six cents each.
Here the workspace states the *workflow* and the *contract*, and the analyst has to notice two things
nobody wrote down: that a one-in-N sample needs weighting before it can stand for the traffic it was
drawn from, and that a precision measured on one population does not describe another. That is the same
shape as the tasks this model class has not passed — Task02 (features as of the prediction time), G10
(censoring), G24 (logging policy), G34 (competing risks).

Whether that holds is an empirical question, and the baseline answers it. The prediction is recorded
here before the baseline runs: **0/3 or 1/3, with the dominant failure being the base-rate transport
rather than the weights**, because the certificate's own numbers make the unweighted, untransported
figure look confirmatory.
