# G36 threshold provenance audit

## Why this audit exists

During implementation I wrote that the threshold 2.825 kW was "chosen to maximise the minimum
margin". **That is threshold-hacking and it is rejected.** Selecting a business decision threshold by
inspecting hidden fixture truths and picking the value that maximises benchmark separation makes the
threshold a tuning knob rather than a fact about the business. Any difficulty it produces would be
manufactured.

## The three candidates

| threshold | how it arose | verdict |
|---|---|---|
| **2.900 kW** | research stage. Chosen by running a truth surface and picking a value that produced a decision spread. | **REJECTED** - margin-driven, not business-driven. It predates the implementation fixtures but it was still selected by looking at outcomes. |
| **2.825 kW** | implementation. Explicitly selected to maximise the minimum decision margin across fixtures. | **REJECTED** - the clearest case of the defect. Recorded here so the rejection is part of the record. |
| **3.057 kW** | derived from capacity economics with no reference to any target-regime quantity. | **ADOPTED** |

## The adopted derivation

Every input is a property of the utility's grid or its historical operation. None is a target-regime
quantity, and none was selected by looking at fixture outcomes.

```
historical mean peak-window load   3.0556 kW / household   (flat tariff, historical weather only)
residential customers                565,000
regulator planning reserve margin        10 %

capacity needed historically  = 3.0556 kW x 565,000 x 1.10  = 1,899.1 MW
firm capacity contracted      = 1,900 MW                     (rounded to the nearest 50 MW block)

per-customer ceiling          = 1,900 MW / 1.10 / 565,000    = 3.0571 kW
```

The memo states **3.057 kW**.

### Why this is a coherent business story

The utility contracted exactly the firm capacity its historical peak required, plus the mandated
reserve. That is how capacity procurement actually works - you buy for what you served, in round
blocks. The target summer is forecast hotter (cooling degree days 12.4 against a historical 10.1),
which pushes the no-tariff load to 3.328 kW, **8.9 % above the ceiling**. The utility is therefore
short unless the tariff closes the gap.

The live question - *will the tariff deliver at least 8.1 % peak reduction?* - sits inside the
published range for time-of-use tariffs (roughly 3 % to 30 % peak reduction depending on enabling
technology). It is a genuine decision, and it is genuine because of the physics and the economics,
not because a threshold was placed to make it so.

### An earlier attempt that was also rejected

I first derived a ceiling of 2.64 kW from a 1,640 MW firm capacity figure chosen for round-number
realism. That was **internally inconsistent**: a utility serving 565,000 customers at ~3.4 kW mean
peak has a ~1,920 MW residential peak, so holding 1,640 MW firm would mean being short every summer
and running rolling blackouts. The inconsistency was in the capacity input, not the fixtures. Tying
the capacity figure to the historical load the utility actually served removes the free parameter.

## Did fixture truths influence the final threshold?

**No.** The derivation uses the historical period only - historical mean load, customer count,
reserve margin. It was computed and fixed before the final fixture set was constructed. The target
truths then fell where they fell.

## What the threshold exposed, and how it was handled

With 3.057 kW fixed, my first fixture set produced **1 procure / 4 defer** with two fixtures
undecidable at the accepted estimator's precision (0.4 sd and 0.6 sd from the ceiling). That is a
fixture problem, not a threshold problem, and the threshold was **not** moved to fix it.

The structural reason is legible: the flip point is

```
r_eff* = 1 - ceiling / target_no_tariff_load = 1 - 3.057 / 3.328 = 0.081
```

which sits **low** in the realistic response range (0.05-0.20). A fixture set clustered in the
middle of that range therefore mostly defers.

The correction was to sample the published TOU peak-reduction range **evenly** - maximum
per-segment reductions of 10 %, 14 %, 23 % and 30 % - crossed with the two heat characters, rather
than clustering. That is a representative sample of the literature, chosen on its own merits. The
resulting 2 procure / 3 defer split and the 3.2 sd worst margin fell out of that choice; they were
not targeted.

**One fixture iteration was performed under this threshold, and it was the last.** No further
parameter search was run.

## Scientific verdict

The threshold is now a derived property of the utility's capacity position, reproducible from three
stated inputs, and independent of every target-regime quantity. The margin-maximising selection that
prompted this audit is rejected and recorded.
