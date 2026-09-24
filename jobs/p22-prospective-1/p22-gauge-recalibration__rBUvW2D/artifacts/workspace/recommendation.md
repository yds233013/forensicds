# Recommendation: Escalation of MAN-4471 Nonconformance

**Date:** 2026-06-25  
**From:** Process Data Scientist, Building 2  
**To:** Purchasing, Operations, Plant Manager  
**Subject:** Restatement of escalation per Schedule 3 §3.2 of Supply Quality Agreement

## 1. Executive Summary

The proposed escalation to a change of supplier against Brendale Special Steels regarding the MAN-4471 gallery bore is **withdrawn**. 

While the reported nonconforming rate in weeks 19–24 rose to 6.69 %, our investigation confirms that this increase was primarily due to a measurement system offset on CMM-1, not the supplied material. When measured against the drawing's **conformance reference** (as required by Schedule 3 §3.2 and established under QP-07), the actual nonconforming rate is **3.81 %**. This is below the 5.5 % threshold required for supplier escalation.

## 2. Evidence and Analysis

### 2.1 Measurement System Offset
Following a `PERIODIC+ADJUST` calibration event on 2026-05-04 (Week 19), CMM-1 was found to carry a **+7.81 µm** offset on the MAN-4471 bore feature. This offset was established through the quarterly retained-artefact programme (QP-07 §5) using reference artefacts REF-01 through REF-20. 

Because the feature tolerance is ±30 µm, this positive offset caused many conforming parts to be incorrectly dispositioned as `FAIL`. CMM-2, which did not undergo adjustment in this period, maintains a negligible offset of +0.30 µm.

### 2.2 Corrected Nonconforming Rate
We have re-evaluated all 12,000 parts produced in the post-step window (weeks 19–24) by removing the machine-specific offsets from the raw readings.

| Metric | Reported (Uncorrected) | Corrected (Conformance Ref) |
|---|---|---|
| Nonconforming Rate (Weeks 19–24) | 6.69 % | **3.81 %** |
| Baseline Rate (Weeks 13–18) | 2.75 % | 2.75 % |
| **Change (Percentage Points)** | **+3.94 pp** | **+1.06 pp** |

### 2.3 Attribution of Change
The total increase of 3.94 percentage points in the reported nonconforming rate is attributed as follows:
* **Measurement System:** 2.88 pp (Due to CMM-1 calibration drift)
* **Material:** 1.06 pp (Likely due to increased hardness of H3 family)
* **Other:** 0.00 pp

## 3. Compliance with Supply Quality Agreement

Schedule 3 §3.2 stipulates that escalation may only be pursued where the nonconforming rate **measured against the drawing's conformance reference** exceeds 5.5 % over a six-week window.

As the corrected rate is 3.81 %, the conditions for escalation are not met.

## 4. Recommendations

1. **Rescind the supplier nonconformance claim** against Brendale Special Steels.
2. **Immediate adjustment of CMM-1** to remove the +7.81 µm offset.
3. **Re-disposition** of affected stock from weeks 19–24 using the corrected values provided in `out/part_dispositions.csv`.
4. Proceed with the standard corrective-action process under Schedule 5 to address the 1.06 pp increase in the true nonconforming rate associated with the H3 material.

*Signed:*  
Process Data Scientist, Building 2
