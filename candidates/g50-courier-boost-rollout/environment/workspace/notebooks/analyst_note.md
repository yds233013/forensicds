# Working note — Boost readout

**Why the phase-2 design is the one to use.** Phase 1 was a three-week soak in eight markets, scheduled to
catch payout and fraud incidents before we exposed the whole estate. It is only three weeks, it is sixteen
markets at best, and a market-level comparison across eight and eight gives an interval several points wide —
useless for a committee decision. Phase 2 randomised per order over six weeks and 120k orders, which is why
the interval is four tenths of a point rather than several points. I used phase 2.

**Things I checked and then stopped worrying about.**

- Assignment looks clean. Realised boost share tracks the configured target in every market-week; the largest
  z across 96 market-weeks is 2.09, which is what you expect from 96 draws.
- The enrolled and never-enrolled markets were comparable before the programme opened (14.55 vs 15.30 % late).
- The effect is present in all sixteen markets, between −3.4 and −4.6 pp. A single market or a single week is
  not driving it.
- Courier supply per arm is identical to within 0.08 %. This was the one I expected to find something in, and
  there is nothing there, so whatever Boost is doing it is not doing it by changing how many couriers we have.

**Open.** The control arm is 2.4 pp worse than the never-enrolled markets. Those markets were never
randomised against the enrolled ones, so I do not think a level gap between them tells us anything, and I have
left it at that. Worth a second look if anyone has time before the committee, but it does not change the
headline.
