# Recordable case standard (HSE, Meridian Industrial Services)

The client access requirement is written on **recordable cases**, as defined by the recordkeeping
standard our contracts adopt. This page is the operative definition for reporting.

## 1. What is recordable

A case is recordable when it is work related and results in any of: death, days away from work,
restricted work or job transfer, medical treatment beyond first aid, loss of consciousness, or a
significant injury or illness diagnosed by a licensed health-care professional.

`incident_cases.classification` carries the determination:

| Value | Meaning | Recordable? |
|---|---|---|
| `RECORDABLE` | determination made, criteria met | **yes** |
| `FIRST_AID` | treated, but first aid only | no |
| `UNDER_REVIEW` | determination not yet made | **not yet** - a case counts only once it is classified `RECORDABLE` |
| `NOT_WORK_RELATED` | determination made, not work related | no |

## 2. One case per injured person

The log opens **one row per injured person**. An event that injures three workers is three cases, not
one; `event_id` groups them. A single worker injured in one event is one case however many body parts
are noted.

## 3. Which window a case belongs to

A case belongs to the window in which the incident **occurred** (`occurred_on`), not the window in
which it was entered (`recorded_on`). Entry lags the incident - typically days, sometimes months after
a determination is disputed - so the two dates fall in different windows often enough to matter.

## 4. Which site a case belongs to

`incident_cases.site_id` is the site where the incident happened. For a worker who covers more than one
site this is not their home site in `workers.home_site_id`.

## 5. Whose cases count

Agency workers are supervised day to day by Meridian supervisors on Meridian sites. Under the standard
the host employer records their cases, so they count on our rate exactly as employees' do.
