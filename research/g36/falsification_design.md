# G36 falsification design

A strong analyst must be able to **challenge their own transport assumptions**, and a future
trajectory analysis must be able to distinguish "constructed a plausible forecast" from "tried to
break their own forecast". The evidence below is designed to make that distinction visible.

| diagnostic | what the analyst does | which assumption it tests |
|---|---|---|
| **control-arm vs history** | compare the pilot's *control* households against the historical weather-load curve | **A1**: the tariff did not change the weather response. If controls diverge from history, something other than the tariff moved. |
| **covariate balance inside opt-in** | compare TOU and control arms on segment, base load, prior consumption | **A2**: randomisation inside the opt-in group held |
| **opt-in vs population comparison** | compare enrolled households to the customer master on segment mix and base load | **quantifies H1** - shows the selection is real and how large it is |
| **response heterogeneity by segment** | estimate the response separately per segment and inspect the spread | **A3**: segment captures the effect modification. If responses are flat across segments, reweighting by segment buys nothing |
| **response vs CDD within the pilot** | plot/fit the estimated reduction against daily cooling-degree-days | **quantifies H2** - the damping is visible *inside* the pilot summer, not merely asserted |
| **pilot CDD range vs target CDD range** | compare the two distributions | **A5**: is the target inside the fitted range, or is this extrapolation? |
| **positivity check** | count pilot households per segment | **A4**: every population segment is represented |
| **placebo period** | apply the pipeline to a pre-pilot summer where no tariff existed; the estimated response should be ~0 | detects a pipeline that manufactures a response from noise |
| **leave-one-segment-out** | refit excluding each segment in turn | stability of the transported response |
| **reconciliation** | segment forecasts weighted to population vs a direct population forecast | arithmetic consistency (necessary, not sufficient - see `coherent_wrong_gate.md`) |

## The two diagnostics that matter most

**Response vs CDD inside the pilot.** This is the single check that separates `W8` (selection fixed
only) from the correct answer. The damping is estimable *within the pilot summer*, because the pilot
summer itself spans a range of daily temperatures. An analyst who plots reduction against CDD sees
the slope; one who takes a pilot average never looks.

**Opt-in vs population mix.** This is the check that separates `W9` (temperature fixed only) from
correct. It requires comparing the enrolment log to the customer master - two artefacts the analyst
must think to join.

A trajectory that performs neither, and simply reports a transported number, has produced a
plausible forecast without testing it. That is the behaviour the baseline should be able to detect.

## Deliberately available negative control

The pre-pilot summers contain no tariff. Running the response-estimation pipeline on them must yield
approximately zero. This is a genuine falsification opportunity and costs the design nothing.
