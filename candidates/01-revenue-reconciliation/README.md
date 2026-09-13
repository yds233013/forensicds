# forensicds/revenue-reconciliation-01

Enterprise revenue reconciliation under staged account migrations.

- **Agent sees:** a Finance memo (August recognized revenue ~8.5% above billing, July tied) and a
  realistic revenue-analytics workspace at `/workspace`.
- **Hidden root cause:** customer attribution joins revenue rows to a CRM export whose grain is
  (account record version × billing link) using an as-of predicate. Staged migrations in August
  leave legacy records open while successors carry `legacy` links to the same billing accounts,
  so the join becomes one-to-many and silently multiplies monetary rows. The same logic attributes
  pre-migration history to legacy accounts instead of the canonical account.
- **Correct repair:** one-row-per-billing-account canonical mapping (billing owner → migration
  register lineage → canonical current CRM attributes), grain-preserving join.
- **Verifier:** 28 behavioural checks on the visible snapshot and three hidden generated snapshots;
  binary reward.

Design: `research/task01_design.md`. Validation evidence: `report/task01_validation.md`.
Dev tooling: `tools/task01/`.
