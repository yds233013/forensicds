"""The two fill-rate definitions, and the four things they differ about.

Schedule 2 §7 of the customer supply agreement defines a **line** fill measured at the **confirmed** quantity,
windowed on **requested delivery date**, with returns excluded and customer-cancelled lines excluded, and with
a line carrying **no confirmation** counted as not filled (§7.2).

The supplier's methodology appendix defines a **case** fill measured at the **requested** quantity, windowed on
**despatch date**, with returns deducted from delivered quantity.

Parameterising both over the four differences makes the bridge between them a sequence of single changes.

Schedule 4 records the amended quantity on a line the customer amended after confirmation, and leaves the basis
of measurement for such a line **to be agreed**. Both readings are therefore available and neither can be
preferred; `amended_basis` selects one.
"""
CONTRACT = dict(denominator="confirmed", net_returns=False, on_despatch=False, unit_weighted=False)
SUPPLIER = dict(denominator="requested", net_returns=True, on_despatch=True, unit_weighted=True)

BRIDGE_STEPS = (("aggregation", "unit_weighted", True),
                ("denominator", "denominator", "requested"),
                ("returns_treatment", "net_returns", True),
                ("date_window", "on_despatch", True))


def load(con):
    """Order lines with returned quantity attached, once."""
    rows = con.execute(
        "SELECT l.*, COALESCE(r.qty, 0) AS returned_qty FROM order_lines l "
        "LEFT JOIN (SELECT line_id, SUM(return_qty) AS qty FROM returns GROUP BY line_id) r "
        "ON r.line_id = l.line_id").fetchall()
    return [dict(x) for x in rows]


def _target(ln, denominator, amended_basis):
    return ln["requested_qty"]
    if denominator == "requested":
        return ln["requested_qty"]
    if ln["amended_qty"] is not None and amended_basis == "amended":
        return ln["amended_qty"]
    return ln["confirmed_qty"]          # None where no confirmation was recorded


def rate_pct(lines, period, *, denominator, net_returns, on_despatch, unit_weighted,
             amended_basis="confirmed", account_id=None):
    lo, hi = period
    sel = []
    for ln in lines:
        if ln["cancelled_by_customer"]:
            continue
        if account_id is not None and ln["account_id"] != account_id:
            continue
        key = ln["despatch_date"] if on_despatch else ln["requested_delivery_date"]
        if key is None or not (lo <= key < hi):
            continue
        sel.append(ln)
    if not sel:
        return None, 0, 0
    if unit_weighted:
        num = den = 0
        for ln in sel:
            tgt = _target(ln, denominator, amended_basis)
            if tgt is None:
                continue
            got = ln["delivered_qty"] - (ln["returned_qty"] if net_returns else 0)
            num += min(max(got, 0), tgt)
            den += tgt
        return (100.0 * num / den if den else None), den, num
    filled = 0
    for ln in sel:
        tgt = _target(ln, denominator, amended_basis)
        if tgt is None:
            continue                     # a line with no confirmation cannot be shown to be filled (§7.2)
        got = ln["delivered_qty"] - (ln["returned_qty"] if net_returns else 0)
        if got >= tgt:
            filled += 1
    return 100.0 * filled / len(sel), len(sel), filled


def contract_pct(lines, period, amended_basis="confirmed", account_id=None):
    return rate_pct(lines, period, amended_basis=amended_basis, account_id=account_id, **CONTRACT)


def supplier_pct(lines, period, amended_basis="confirmed"):
    return rate_pct(lines, period, amended_basis=amended_basis, **SUPPLIER)


def bridge_pp(lines, period, amended_basis="confirmed"):
    """The four single-change steps from the agreement's definition to the supplier's."""
    step = dict(CONTRACT)
    prev = rate_pct(lines, period, amended_basis=amended_basis, **step)[0]
    out = {}
    for name, key, val in BRIDGE_STEPS:
        step[key] = val
        cur = rate_pct(lines, period, amended_basis=amended_basis, **step)[0]
        out[name] = cur - prev
        prev = cur
    out["other"] = 0.0
    return out
