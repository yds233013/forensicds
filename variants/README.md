# Paired instruction variants

To separate *fault-localization* difficulty from *implementation* difficulty, each task can be
run under two conditions that share the identical environment, verifier and oracle and differ
**only** in `instruction.md`:

| Condition | Instruction content |
|-----------|---------------------|
| A. Diagnosis (default task) | Business symptom and desired outcome only. |
| B. Localized | Additionally names the faulty relationship (for Task 01: account enrichment / canonical identity logic multiplies monetary rows). |

Variant instruction files live in `variants/<task>/<condition>.md`. Generate a runnable task
directory with:

```bash
python3 tools/make_variant.py candidates/01-revenue-reconciliation variants/01-revenue-reconciliation/localized.md
# -> candidates/01-revenue-reconciliation__localized/ (environment/tests/solution copied, instruction replaced,
#    task name suffixed, provenance recorded in task.toml metadata)
```

The script refuses to change anything but `instruction.md` and the task name, and records the
sha256 of the environment, tests and solution trees so paired results can be checked for
equivalence. Condition B texts are intentionally **not written yet**.
