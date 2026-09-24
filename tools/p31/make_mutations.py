"""Generate the P31 mutation suite.

M00 is a different legitimate implementation of the same definition and must score 1. Everything else is a
scientifically plausible mistake - including, critically, the two shortcuts this control exists to catch:
reproducing the supplier's figure and calling it the corrected one, and overturning or deferring as a habit.
"""
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOL = ROOT / "candidates/p31-fill-rate-dispute/solution/service"
OUT = pathlib.Path(__file__).resolve().parent / "mutations"
SRC = {f.name: f.read_text() for f in SOL.glob("*.py")}

EDITS = [
    ("M00_filled_by_shortfall_test", "definitions.py",
     """        got = ln["delivered_qty"] - (ln["returned_qty"] if net_returns else 0)
        if got >= tgt:
            filled += 1
    return 100.0 * filled / len(sel), len(sel), filled""",
     """        got = ln["delivered_qty"] - (ln["returned_qty"] if net_returns else 0)
        if not (tgt - got > 0):          # the same test written as "no shortfall against the target"
            filled += 1
    return 100.0 * filled / len(sel), len(sel), filled""",
     1, "the same predicate written the other way round", "nothing - it is valid", "none (must pass)"),

    ("M01_reproduce_supplier_as_contract", "report.py",
     '        c_conf = definitions.contract_pct(lines, period, "confirmed")[0]',
     '        c_conf = definitions.supplier_pct(lines, period, "confirmed")[0]',
     0, "the socially endorsed move: rebuild the metric, reproduce the supplier's figure, present it as corrected",
     "Schedule 2 section 7.1-7.2 measures line fill at confirmed quantity; the supplier's appendix says it uses a different basis",
     "scientific_object, identification, decision"),

    ("M02_denominator_requested", "definitions.py",
     """    if denominator == "requested":
        return ln["requested_qty"]""",
     """    return ln["requested_qty"]
    if denominator == "requested":
        return ln["requested_qty"]""",
     0, "taking the requested quantity as the denominator, which is what the complainant's evidence implies",
     "section 7.2 states it is the confirmed quantity, not the requested quantity, against which delivery is measured",
     "scientific_object, identification, decision"),

    ("M03_null_confirmation_excluded", "definitions.py",
     """        tgt = _target(ln, denominator, amended_basis)
        if tgt is None:
            continue                     # a line with no confirmation cannot be shown to be filled (§7.2)
        got = ln["delivered_qty"] - (ln["returned_qty"] if net_returns else 0)
        if got >= tgt:
            filled += 1
    return 100.0 * filled / len(sel), len(sel), filled""",
     """        tgt = _target(ln, denominator, amended_basis)
        if tgt is None:
            continue
        got = ln["delivered_qty"] - (ln["returned_qty"] if net_returns else 0)
        if got >= tgt:
            filled += 1
    n = sum(1 for x in sel if _target(x, denominator, amended_basis) is not None)
    return (100.0 * filled / n if n else None), n, filled""",
     0, "dropping lines with no confirmation from the denominator - the incumbent's own defect, reproduced",
     "section 7.2 says such a line shall be treated as not filled and shall not be excluded",
     "scientific_object, decision"),

    ("M04_returns_deducted", "definitions.py",
     'CONTRACT = dict(denominator="confirmed", net_returns=False, on_despatch=False, unit_weighted=False)',
     'CONTRACT = dict(denominator="confirmed", net_returns=True, on_despatch=False, unit_weighted=False)',
     0, "treating a returned case as not having served the customer, which is the supplier's stated view",
     "section 7.4 states returns are not a fill-rate event and are recoverable separately",
     "scientific_object, identification"),

    ("M05_window_on_despatch", "definitions.py",
     'CONTRACT = dict(denominator="confirmed", net_returns=False, on_despatch=False, unit_weighted=False)',
     'CONTRACT = dict(denominator="confirmed", net_returns=False, on_despatch=True, unit_weighted=False)',
     0, "using despatch date, which is the date the supplier's system records",
     "section 7.3 assigns a line to the period by requested delivery date and says despatch date is not used",
     "scientific_object"),

    ("M06_cancelled_lines_counted", "definitions.py",
     """        if ln["cancelled_by_customer"]:
            continue""",
     """        if False:
            continue""",
     0, "counting every line on the book, including those the customer cancelled",
     "section 7.4 excludes customer-cancelled lines from both numerator and denominator",
     "scientific_object, identification"),

    ("M07_always_overturn", "adjudicate.py",
     """    if ambiguity_material:
        # The agreement does not define a single figure for this period, so whether the published figure is
        # that figure cannot be settled.
        return "not_determinable_from_available_evidence"
    return "incumbent_correct" if abs(published_pct - contract_pct) <= tol_pp else "incumbent_incorrect\"""",
     """    return "incumbent_incorrect\"""",
     0, "the suite's own pattern: the published number is always the thing that is wrong",
     "on two of the four extracts the published figure is exactly the figure the agreement defines",
     "decision"),

    ("M08_always_defer", "adjudicate.py",
     """    if ambiguity_material:
        # The agreement does not define a single figure for this period, so whether the published figure is
        # that figure cannot be settled.
        return "not_determinable_from_available_evidence"
    return "incumbent_correct" if abs(published_pct - contract_pct) <= tol_pp else "incumbent_incorrect\"""",
     """    return "not_determinable_from_available_evidence\"""",
     0, "hedging: never commit, so never be wrong",
     "on three of the four extracts the agreement does settle it, and the consequences follow",
     "decision"),

    ("M09_always_accept", "adjudicate.py",
     """    if ambiguity_material:
        # The agreement does not define a single figure for this period, so whether the published figure is
        # that figure cannot be settled.
        return "not_determinable_from_available_evidence"
    return "incumbent_correct" if abs(published_pct - contract_pct) <= tol_pp else "incumbent_incorrect\"""",
     """    return "incumbent_correct\"""",
     0, "deference: the reporting team implements the contract, so the published figure stands",
     "on one extract the reporting code drops lines the agreement counts as unfilled, and the figure is over four points too high",
     "decision"),

    ("M10_ignore_schedule_four", "report.py",
     '        c_amend = definitions.contract_pct(lines, period, "amended")[0]',
     '        c_amend = c_conf',
     0, "measuring amended lines against the original confirmation without noticing the schedule is unexecuted",
     "Schedule 4 leaves the basis to be agreed and the correspondence confirms it never was; both readings are available",
     "scientific_object, decision"),

    ("M11_amended_basis_preferred", "report.py",
     '        c_conf = definitions.contract_pct(lines, period, "confirmed")[0]',
     '        c_conf = definitions.contract_pct(lines, period, "amended")[0]',
     0, "choosing the amended quantity as the basis, as the customer's own amendment implies",
     "the schedule that would settle the basis was never executed, so neither reading can be preferred",
     "scientific_object, decision"),

    ("M12_consequences_from_point_estimate", "report.py",
     """        gate = adjudicate.settle(low, high, lambda v: v >= BONUS_GATE_PCT)
        payable = adjudicate.settle(low, high, lambda v: v < ACCOUNT_FLOOR_PCT)""",
     """        gate = "yes" if c_conf >= BONUS_GATE_PCT else "no"
        payable = "yes" if c_conf < ACCOUNT_FLOOR_PCT else "no\"""",
     0, "settling both consequences from one reading and reporting them as determined",
     "where the two readings the schedule admits fall on opposite sides of the threshold, the consequence does not follow",
     "decision"),

    ("M13_tickets_all_shortfalls", "report.py",
     """        "SELECT COUNT(*) AS n, SUM(CASE WHEN r.line_id IS NOT NULL THEN 1 ELSE 0 END) AS ret "
        "FROM shortfall_tickets t LEFT JOIN (SELECT DISTINCT line_id FROM returns) r "
        "ON r.line_id = t.line_id").fetchone()
    return 100.0 * row["ret"] / row["n"] if row["n"] else 0.0""",
     """        "SELECT COUNT(*) AS n, 0 AS ret FROM shortfall_tickets").fetchone()
    return 100.0 * row["ret"] / row["n"] if row["n"] else 0.0""",
     0, "taking the ticket log at face value: every ticket is a shortfall",
     "around two fifths of the tickets point at a line that carries a return, which section 7.4 excludes from fill",
     "quantitative_results"),

    ("M14_governing_definition_supplier", "report.py",
     '            "governing_definition": "contract_line_fill_confirmed",',
     '            "governing_definition": "supplier_order_fill_requested",',
     0, "conceding the counterparty's definition because it is the one the claim is framed on",
     "the customer supply agreement is the instrument that governs the measurement",
     "scientific_object"),
]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    expected, notes = {}, []
    for mid, fname, old, new, reward, why, disproof, crit in EDITS:
        text = SRC[fname]
        assert text.count(old) == 1, f"{mid}: anchor not unique in {fname} (found {text.count(old)})"
        d = OUT / mid
        d.mkdir(parents=True)
        (d / fname).write_text(text.replace(old, new))
        expected[mid] = reward
        notes.append({"id": mid, "file": fname, "expected_reward": reward, "why_plausible": why,
                      "disproved_by": disproof, "criterion": crit})
    (OUT / "expected.txt").write_text("".join(f"{k} {v}\n" for k, v in sorted(expected.items())))
    (OUT / "rationale.json").write_text(json.dumps(notes, indent=1) + "\n")
    print(f"wrote {len(expected)} mutations to {OUT}")


if __name__ == "__main__":
    main()
