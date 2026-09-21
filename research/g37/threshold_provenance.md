# Threshold provenance — fixed BEFORE any fixture existed

## C1: Ppk ≥ 1.33, and customer notification if the latent Ppk is below it
- **Source.** The automotive supply-chain convention on ongoing capability for a characteristic
  under statistical control:
  - the AIAG PPAP manual (4th ed.) asks for index > 1.67 at initial PPAP;
  - customer-specific requirements (CSRs) commonly set **≥ 1.33 for ongoing production**.

  The G37 business documents will cite a *supply agreement clause* modelled on that convention:
  "maintain Ppk ≥ 1.33 on the thickness characteristic; notify the customer within 5 working days
  of any window in which it is not met."
- **Independence.** 1.33 corresponds to ±4σ inside the specification. It is an industry-standard
  value that predates this project, and it was not derived from any fixture.
- **Fixed before fixture outcomes:** **yes.** This file is written before `sim/` exists. The fixtures
  must be built around 1.33, never the reverse. If a fixture truth lands near 1.33, the fixture is
  redesigned for distance on scientific grounds (a different regime), and this is logged. The
  threshold is never moved.
- **Specification limits.** 2.500 ± 0.060 mm, from the customer drawing. They are fixed here, before
  simulation.

## C2: Ppk ≥ 1.33 for continued process verification
This is a common CPV practice following FDA Process Validation Guidance Stage 3. It is not a
regulatory number, so **provenance is weaker**: it is company policy. The specification of
95.0–105.0 % label claim is a typical registered specification.

## C7: chargeback if the true defect rate exceeds 0.50 %
A contractual AQL-style clause. It is realistic, but it is a contract term invented for the task,
not an industry standard. Provenance is moderate.

## C9: σ_wafer-to-wafer > 1.2 nm triggers yield-model escalation
Derived from a lithography process-window budget. This is realistic but internal. **Weak**
provenance: an internal budget number is easy to suspect of being chosen for convenience.

**Ranking of threshold provenance:**
1. C1 (industry standard, fixed spec)
2. C7 (contract clause)
3. C2 (company CPV policy)
4. C9 (internal budget)
