# Time-of-use pilot - design note

**Owner:** Experimentation
**Status:** closed, analysis phase

## Recruitment

The pilot was **voluntary**. Customers were invited by email and bill insert; those who responded
were enrolled. Enrolment is recorded in `tou_pilot_enrolment` with the date each customer signed up.

We did not attempt to recruit a representative sample. Enrolment was open until the target count was
reached, and the customers who came forward are the customers who came forward.

## Assignment

Among enrolled customers, the tariff was assigned **at random**: roughly half were switched to the
time-of-use rate for the pilot season, and the remainder stayed on the flat rate as a control group
and were paid a participation credit. `assigned_arm` records which.

The randomisation was performed once, before the season began, by the platform's assignment service.
Balance on premises type, historical consumption and service zone is reproducible from the extract.

## Season

The pilot ran through the 2026 peak season. `weather_daily` carries that season's actual cooling
degree days alongside the historical seasons.

## What the pilot does and does not establish

Within the enrolled group, the treatment and control arms are comparable, so the difference between
them is caused by the tariff. The enrolled group itself was not drawn at random from the estate.
