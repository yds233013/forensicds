# SOP-118 — Outpatient reminder-call programme

## 1. Purpose

To reduce did-not-attend rates in outpatient clinics by telephoning patients at higher risk of not attending.

## 2. Targeting

Patients are selected by the risk score recorded in `model_scores` for the model named in
`policy_config` under `programme.score_model`. The share of the score distribution called, the start week and
the clinic ramp order are all held in `policy_config` and are not to be changed without Clinical Operations
sign-off.

The calling threshold was fixed at programme start from the score distribution observed before the programme
began, and has not been changed since.

## 3. Rollout

Clinics joined in `programme.ramp_group` order, one group per week, over `programme.ramp_weeks` weeks.

A set of clinics listed under `programme.excluded_clinics` was determined at programme start and is outside the
programme. The selection was drawn stratified by `clinics.size_band`. Requests to bring an excluded clinic into
the programme go to Clinical Operations; none have been made.

## 4. Calling

Bookings selected for calling appear in `reminder_calls` with the call outcome. `REACHED` means the patient was
spoken to. `NO_ANSWER` and `VOICEMAIL` mean no contact was made; no message is left describing the appointment.

## 5. Reporting

Programme reporting is the responsibility of Clinical Operations. Model performance reporting is separate and
is governed by MRM-04.
