# Screening service agreement — Kestrel Screening / Northwater Retail (extract)

## 3. Performance standard

3.1 Kestrel warrants that the screen's **precision** — the share of transactions it flags that are
genuinely fraudulent — will be at least the **precision floor** stated in `contract_terms`
(`precision_floor`).

3.2 The standard is written on **Northwater's traffic**, not on Kestrel's book as a whole and not on
any published benchmark. Northwater's fraud rate for the term of the agreement is fixed at
`merchant_fraud_rate` in `contract_terms`, agreed from their own chargeback history at signing.

3.3 Kestrel shall demonstrate the screen's performance **from its own production runs during the
quarter**, using the review outcomes the quality programme produces (`docs/review_queue_sop.md`).
Marketing benchmark material is not evidence for clause 3.1.

3.4 Where the reported precision falls below the floor, Kestrel shall **remediate**: retune the screen
at its own cost and re-certify the following quarter. At or above the floor the screen is **accepted**
for the quarter.

## 4. Reporting

4.1 The quarterly certificate reports the screen's measured detection performance for the quarter and
the precision under clause 3.2, in the form set out in `docs/outputs/performance_contract.md`.
