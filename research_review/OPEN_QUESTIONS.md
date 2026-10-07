# Open questions

Unresolved, ordered by how much they affect the dossier's conclusions. Each says what would settle it.

## Affecting the central scientific claim

**1. Do the eleven criterion-failure shapes reflect one mechanism or several?**
Chapter 08 establishes a statistical regularity (the decision-relevant quantity is the modal failure) and
explicitly does **not** establish a shared cause. Two shapes are mirror images, which a single cause
cannot produce. → **Settled by experiment A** (manual adjudication, free).

**2. Where do failures sit on the six binary-reward tasks?**
`g10`, `g36`, `g05`, `02`, `g24`, `g08` emit one bit. We therefore have **no criterion evidence from any
task Claude solved**, and none from `g10`, the task with the strongest behavioural evidence of correct
engagement. The instrumented four share an author period and are all attribution/decomposition tasks.
→ **Settled by experiment B** (~$29).

**3. How much of the measured failure is premature scaffold stopping?**
Claude used 13-15 steps on `g36` where Gemini used 40-54, and both failed. Several trajectories end with
confident completion language. The trajectories record no termination reason — **not observable**.
→ **Settled by experiment C** (~$15).

**4. Is Claude's advantage architecture or tier?**
Opus against Flash is not a matched comparison. → **Settled by experiment E** (tier-matched Haiku).

## Affecting specific numbers

**5. `p31-prospective-1` — valid or invalid?**
4 steps, 23,987 prompt tokens, 5 tool calls, then empty turns and no outputs. The agent demonstrably ran,
so it is counted **valid** and flagged BORDERLINE in `ALL_TRIALS.csv`. Early scaffold termination cannot be
excluded. Sensitivity: reclassifying it makes `p31` 0/2 and the Gemini denominator 30; the 1-pass headline
is unaffected. → Settled by a scaffold-level log, if one exists outside the trajectory.

**6. How much of `p20`'s quantity failure is the sign artifact versus genuine error?**
Both arms ran on v1, which lacks the convention. 12 Claude and 7 Gemini sign-flip field failures; every
trial also has genuine failures. The `attribution_auc[...]` failures carry no artifact, so the finding
survives — but the magnitude of the quantity error is overstated. → Settled by running Claude on
`p20-v1.1`, which already exists (~$3).

**7. Which pinned file does `claude-code` change in `g50`?**
`tests/test.sh:76` discards the filename. **UNKNOWN.** I attempted the diagnostic — replicate the installer
in the frozen image and rerun the check with output shown — but the Docker daemon was not running.
→ Settled in about an hour, free, with Docker available.

## Affecting the record rather than the results

**8. Why was `g36-tou-capacity-gate` promoted into the final ten after being closed as development-only?**
`30026c6` closes it as development-only; it nonetheless ships. **No artifact records the promotion
decision.** Given it scored 0/3 for both models, the inclusion is defensible on headroom, but the reasoning
is missing. **UNKNOWN.**

**9. Was there one original Abundant brief or two?**
`research/audit/abundant_requirements.md` restates "5-10 tasks"; the final-ten handoffs restate "exactly
10". Neither brief is in the repository, which the 2026-09-23 audit recorded at the time. **INFERENCE:**
two briefs. → Settled only by the source documents.

**10. Was `harbor check` ever run on the final ten?**
It was run on eight pool tasks during development, each returning 1. The final-ten run failed twice for
environment reasons (host contention, then an unauthenticated scaffold agent). So the *scaffold-agent
experience of the instructions* is untested for the final ten. → Settled on an authenticated idle host.

**11. Is `g50`'s pre-exposure adversarial record reproducible?**
63 submissions, 40 malformed-output attacks, 8 sandbox attacks — **REPORTED, NOT REVERIFIED** here; it
needs Docker.

## Documentation defects found, not yet fixed

**12. `report/FINAL_REPORT.md:982` and `HANDOFF_ABUNDANT_FINAL_SUBMISSION.md:794` state that no task tests
justified deferral. `p31` does** (`tests/world.py:300`; agent-visible at `readout_contract.md:42`), and
both models failed to produce it. The scale plan's top-priority template is therefore mis-stated: the
priority is to *replicate* the pattern, not invent it.

**13. `README.md:26` still documents the superseded five-task suite** ("2/15 successful trials; task-level
pass@3 = 1/5") and lists G34 in the final suite. G34 is not in the final ten.

**14. `g36-tou-capacity-gate-v1.1` remains on disk**, abandoned and unfrozen, never trialled, not in the
submission archive.

## Questions this dossier cannot answer in principle

**15. Why did any individual agent act as it did.** Trajectories record actions and, unevenly, reasoning
summaries. No private reasoning is observable, and none is attributed anywhere in this dossier.

**16. Whether the benchmark measures a capability that transfers to real analytical work.** Every DGP is a
modelling choice. `g50`'s mean-preserving queue, `g10`'s censoring process and `p22`'s gauge offset are
literature-grounded but not measured from any real system. Every conclusion is conditional on them.
→ Settled only by human-expert trials on the same tasks, which this project never ran.
