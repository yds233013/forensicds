# Conditional Correctness: Evaluating Professional AI Analysts by Re-executing Their Deliverables Against Mechanism Variants

An agent is handed a manufacturing quality dispute: a defect rate has risen and a supply agreement caps
material-attributable defects at 5.5 %. A frontier model works it for forty-eight steps, finds the measurement
instrument has drifted to an offset of 7.81 µm against a design value of 8.20, recomputes the corrected nonconforming
rate to 3.81 % against a true 3.83 %, and recommends no supplier action — which is right. It also writes
`"tooling": 0.0` into the attribution as a literal, because on this quarter's data the tool-wear contribution happens to
be 0.17 percentage points. Regenerate the same organisation with a longer insert-change interval, where wear contributes
3.08 points, and that same analysis pushes the rate over the contractual limit while still recommending no action. Every
rubric criterion still passes on the world it was shown. The analysis was correct; it was not correct for a reason that
survives the world being different.

Professional benchmarks grade one instance of one world, and the best of them do so deliberately. APEX-Agents audited
its tasks "to ensure a single correct and well-specified answer exists"; APEX-Accounting verifies each task "admits a
single defensible answer" and removed twenty-four incomplete-information tasks; each task belongs to a single world;
the judge sees the deliverable, not the trajectory. For *scoring* this is right — it is why judge agreement with expert
ground truth reaches 97.1 %. It also makes one property unmeasurable: whether a deliverable is correct **because** the
analysis identified the mechanism that makes it correct, or merely because it coincided with that mechanism's value in
the one world it saw.

I propose to measure it. **Conditional correctness**: author the world as a generator over its decision-relevant latent
mechanisms, then grade the agent's deliverable by re-executing it, unchanged, against sibling worlds it never saw — same
documents, same contract, same cast, different mechanism values underneath. A correct analysis must hold where the
mechanism is unchanged, flip to a specified different decision where a mechanism crosses the governing document's
threshold, and decline where the sibling withdraws the evidence that identified the estimand. The unit of evaluation is
the world family, not the instance.

Most components exist, and this credits rather than competes with them. Invariance and directional-sensitivity relations
are CheckList's, and before that metamorphic testing's. Hidden pre-registered decision-relevant variants of professional
cases are Turk's (arXiv:2605.30590), which already shows variant scoring reorders a frontier leaderboard. Scored
abstention on non-identifiable estimands in a data-science agent benchmark is CausalDS's (arXiv:2607.08093), whose
matched variants explicitly preserve the conceptual SCM and "never flip an identifiability label"; the three-legged score
exists for LLM judges (arXiv:2605.06161). Two things are unoccupied: paired siblings where the same corpus yields an
**opposite correct decision** because one latent mechanism differs, and **re-executing the deliverable instead of
re-prompting the model**. The second makes the first affordable.

That cost property is measured. In a pilot I ran, nine rollouts cost $1.4667 in total model spend and each was graded
against four worlds, because the verifier re-executes the agent's own pipeline against each regenerated sibling; a full
reference trial took 32 seconds. **The marginal cost of the Nth sibling is compute, not inference.** Families of eight are
affordable where eight re-prompts are not, and because siblings are regenerated at grading time, contamination resistance
is structural — there is no fixed instance to memorise.

The preliminary evidence is deliberately model-free. Across 45 single-defect mutations of expert reference analyses in
three worlds, 42 of them defective: 30 (71 %) are caught numerically on the visible world, **10 (24 %, Wilson 95 % CI 13.5–38.5 %) are
invisible there and caught by a sibling**, and 2 (5 %) are invisible on all four — caught instead by procedure-inspecting rubric
criteria, direct evidence that siblings and rubrics are complementary. All three reference analyses pass all four
worlds, the control showing siblings are not simply harder. Separately, in nine prospective trials of one frontier
model, visible-instance grading would record four successes where family grading records none. The limits are real: one
model, three tasks, one domain, defects written by the worlds' own author, no power for any rate. Those nine trials are
an existence proof, not an effect size.

The study is designed so its primary experiment can end it. Six world families in production data science, eight
siblings each, frozen under a hashed analysis plan before any model runs. The primary experiment is model-free: 150
defects written by experts who did not author the worlds, graded by three instruments — visible-instance grading, the
best rubric two independent experts can write **for the visible world alone**, and the family. If the family's
incremental detection over that rubric is under ten points, expert rubrics on one world are sufficient and I report
that. Only then do six frontier agents across four-plus developers run 180 rollouts, with a second arm re-running the
agent from scratch on siblings — separating artifact brittleness from analysis failure, and establishing whether cheap
replay is a valid proxy for expensive re-rollout.

Two limits are hard. The deliverable must be re-executable — true of data science, analytics, accounting close and
financial modelling, false of legal drafting or consulting prose — and the world must be generatively authored, so this
cannot be retrofitted to an estate whose mechanisms were never parameterised. No APEX benchmark covers data science, so
the two gaps compose.

This matters because a professional analysis is not consumed once. It runs again next month on next month's data, and its
value is the number of periods over which its decision stays correct — what a firm needs to know before handing a
recurring close or a monitoring decision to an agent. APEX already treats reliability rather than accuracy as the live
question: no model exceeds 2.6 % Pass^8 on APEX-Accounting. Pass^k asks whether an agent repeats itself on one world;
conditional correctness asks whether its answer survives the world differing. It is a second axis reported alongside
single-instance pass rate, not a replacement.

The deliverable is a method, a generator and evidence about whether it detects anything — not a benchmark; six families
is the sample size for the claim. Shipped: the specification format and generator; six families with siblings and
adjudication records; the defect bank; the control-arm rubrics; a family verifier against Archipelago's interface; one
family built from APEX-Accounting's public trap register, because accounting is the intended application; and the paper,
including the sibling-count curve that prices how many worlds are worth buying.

I have built the pilot this rests on — three parameterised worlds, a verifier that re-executes submitted pipelines
against regenerated siblings, 45 defect suites, and one prospective evaluation under a hashed pre-registered plan with
nine valid trials of nine. Its weakness is that one person authored the worlds, the defects and the verifier. An expert
network fixes exactly that, which is why independent authorship sits in this design's critical path rather than its
acknowledgements.
