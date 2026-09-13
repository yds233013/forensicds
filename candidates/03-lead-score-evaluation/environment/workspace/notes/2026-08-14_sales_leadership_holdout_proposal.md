# Proposal: retire the exploration holdout and raise the router threshold

From: VP Sales Development. To: RevOps Analytics, CRO staff. 2026-08-14.

The August lead-score evaluation shows the model is far stronger than we thought: ROC AUC is up from the high
0.6s to above 0.8, and the top score decile now converts at roughly four times the average. With a model this
sharp, sending 10% of inbound leads to SDRs at random wastes capacity we badly need for high-score leads.

Proposal for the Q4 router change:
1. Set the exploration holdout to 0%.
2. Raise the threshold to the `recommended_threshold` in the August report.

Can RevOps confirm the numbers before the October router release?
