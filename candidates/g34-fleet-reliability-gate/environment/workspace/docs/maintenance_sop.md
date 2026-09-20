# Maintenance standard operating procedure — MP-series pumps (extract)

Owner: Field Service Engineering. Applies to all MP-220/340/360/480 units in the installed base.

## 1. Scheduled overhaul

Every unit is scheduled for a major overhaul at **24 months of service age**. Scheduling slack of a
few months is normal and depends on site shutdown windows; the work order is raised when the unit
is actually taken down, not when it becomes due.

At overhaul the **critical assembly (bearing pack and shaft seal) is removed and exchanged for a
new assembly**. The removed assembly is scrapped; it is not refurbished and does not return to
service. The unit restarts service with a new assembly and a new assembly life.

## 2. Unplanned failure

An unplanned failure is an in-service seizure or loss of containment of the critical assembly that
stops the unit outside a planned window. It raises a `UNPL_FAIL` work order and triggers an
emergency assembly replacement from stock, plus a field-service callout.

## 3. Retirement

A unit is retired when the site closes, the duty is discontinued, or the frame reaches end of life.
Retirement is a fleet decision taken on commercial and site grounds; it is **not** triggered by the
condition of the critical assembly. A retired unit is permanently withdrawn: it does not return to
service and generates no further aftermarket demand.

## 4. Condition monitoring

Each unit carries vibration channels feeding the telemetry platform. **Telemetry status is a
separate feed from the work-order system.** A channel outage means the platform has stopped
receiving data from that channel; it does not mean the unit has stopped. Units routinely run for
months with a degraded or dead vibration channel, and field service records no removal because
none has occurred. A unit is only out of service when a work order says so.

Note from the 2025 reliability review: vibration channels sit on the same bearing housing as the
assembly they monitor, and a channel that goes quiet is often the first sign that the housing is
running hot. Channel health is not a maintenance trigger on its own.
