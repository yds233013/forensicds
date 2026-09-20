# G34 — FY27 installed-base reliability run (fleet reliability gate)

A pump manufacturer must size next year's spare critical-assembly build. The published figure says
55.2% of the installed base will suffer an unplanned failure within 36 months, clearing the 28%
procurement trigger. Operations dispute it; Engineering, asking a different question of the same
extract, are comfortable with it.

Both are right about their own question. The published run answers the assembly-life question and
reports it against the procurement rule, which is written on a different quantity: what actually
happens to a unit's original assembly under the current maintenance programme, where a scheduled
overhaul or a retirement removes the assembly from the population that can still fail.

Design, simulation and gate record: `research/g34/` (the first G34 design was rejected; the
competing-risks redesign is in the `redesign_*` files).
