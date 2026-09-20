"""G33: valid resolution families, pre-registered wrong methods, and the cheap-solve panel."""
from __future__ import annotations

import collections

import simulation as S

WINDOW = S.WINDOW


# ---------------------------------------------------------------- union-find
class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def _agg(pairs):
    out = collections.defaultdict(float)
    for k, a in pairs:
        out[k] += a
    return dict(out)


def _conc(ob, pairs):
    return S.concentration(_agg(pairs), ob["threshold"])


# ---------------------------------------------------------------- VALID
def _identity_uf(ob):
    """Codes joined by rename/merge are the same node. Split codes are deliberately NOT joined."""
    uf = UF()
    for r in ob["spend_lines"]:
        if r["asn_site_code"] != -1:
            uf.find(r["asn_site_code"])
    for e in ob["registry_events"]:
        if e["type"] in ("rename", "merge"):
            uf.union(e["new_code"], e["old_code"])
    return uf


def _split_maps(ob, uf):
    """For each split, the material groups that belong to the carved-out node, learned post-rework."""
    rp = ob["registry_period"]
    maps = []
    for e in ob["registry_events"]:
        if e["type"] != "split":
            continue
        mgs = {r["material_group"] for r in ob["spend_lines"]
               if r["period"] >= rp and r["asn_site_code"] == e["new_code"]}
        maps.append((uf.find(e["old_code"]), e["new_code"], mgs))
    return maps


def _resolve(ob):
    """Canonical node key per line, or None when the line carries no shipment evidence."""
    uf = _identity_uf(ob)
    splits = _split_maps(ob, uf)
    keys = []
    for r in ob["spend_lines"]:
        c = r["asn_site_code"]
        if c == -1:
            keys.append(None)
            continue
        k = uf.find(c)
        for root, new_code, mgs in splits:
            if k == root and r["material_group"] in mgs:
                k = new_code
                break
        keys.append(k)
    return keys


def _prorata_unattributed(ob, keys):
    """Documented rule: a line with no shipment record is spread over that vendor's observed
    ship-from mix in the same period."""
    mix = collections.defaultdict(lambda: collections.defaultdict(float))
    for r, k in zip(ob["spend_lines"], keys):
        if k is not None:
            mix[(r["vendor_code"], r["period"])][k] += r["amount"]
    glob = collections.defaultdict(float)
    for r, k in zip(ob["spend_lines"], keys):
        if k is not None:
            glob[k] += r["amount"]
    gtot = sum(glob.values()) or 1.0
    out = []
    for r, k in zip(ob["spend_lines"], keys):
        if r["period"] not in WINDOW:
            continue
        if k is not None:
            out.append((k, r["amount"]))
            continue
        m = mix.get((r["vendor_code"], r["period"])) or mix.get((r["vendor_code"], r["period"] - 1))
        if not m:
            m = {kk: vv / gtot for kk, vv in glob.items()}
        tot = sum(m.values()) or 1.0
        for kk, vv in m.items():
            out.append((kk, r["amount"] * vv / tot))
    return out


def V1_registry_graph(ob):
    """Union rename+merge, carve splits by material group, pro-rata the unattributed lines."""
    return _conc(ob, _prorata_unattributed(ob, _resolve(ob)))


def V2_two_pass(ob):
    """Same invariant, built the other way round: resolve post-rework first, carry the map back."""
    rp = ob["registry_period"]
    uf = _identity_uf(ob)
    post_mg = collections.defaultdict(set)
    for r in ob["spend_lines"]:
        if r["period"] >= rp and r["asn_site_code"] != -1:
            post_mg[uf.find(r["asn_site_code"])].add(r["material_group"])
    split_new = {uf.find(e["old_code"]): e["new_code"]
                 for e in ob["registry_events"] if e["type"] == "split"}
    keys = []
    for r in ob["spend_lines"]:
        c = r["asn_site_code"]
        if c == -1:
            keys.append(None)
            continue
        k = uf.find(c)
        if k in split_new:
            nc = split_new[k]
            if r["material_group"] in post_mg.get(uf.find(nc), set()):
                k = nc
        keys.append(k)
    return _conc(ob, _prorata_unattributed(ob, keys))


def V3_drop_unattributed(ob):
    """Same resolution, but the unattributed lines are dropped rather than spread.
    Legitimate only if the missingness is unrelated to node - reported for comparison."""
    keys = _resolve(ob)
    return _conc(ob, [(k, r["amount"]) for r, k in zip(ob["spend_lines"], keys)
                      if k is not None and r["period"] in WINDOW])


VALID = {"V1_registry_graph": V1_registry_graph, "V2_two_pass": V2_two_pass,
         "V3_drop_unattributed": V3_drop_unattributed}


# ---------------------------------------------------------------- WRONG
def W1_raw_vendor(ob):
    return _conc(ob, [(r["vendor_code"], r["amount"]) for r in ob["spend_lines"] if r["period"] in WINDOW])


def W2_vendor_after_migration(ob):
    m = {e["old_vendor_code"]: e["new_vendor_code"] for e in ob["migration_log"]}
    return _conc(ob, [(m.get(r["vendor_code"], r["vendor_code"]), r["amount"])
                      for r in ob["spend_lines"] if r["period"] in WINDOW])


def W3_parent_rollup(ob):
    pm = {}
    for v in ob["vendor_master"]:
        pm[v["vendor_code"]] = v["parent_id"]
    return _conc(ob, [(pm.get(r["vendor_code"], -1), r["amount"])
                      for r in ob["spend_lines"] if r["period"] in WINDOW])


def W4_raw_site_code(ob):
    """Shipment codes taken at face value: no registry history at all."""
    return _conc(ob, [(r["asn_site_code"], r["amount"]) for r in ob["spend_lines"]
                      if r["period"] in WINDOW and r["asn_site_code"] != -1])


def W5_renames_only(ob):
    uf = UF()
    for e in ob["registry_events"]:
        if e["type"] == "rename":
            uf.union(e["new_code"], e["old_code"])
    return _conc(ob, [(uf.find(r["asn_site_code"]), r["amount"]) for r in ob["spend_lines"]
                      if r["period"] in WINDOW and r["asn_site_code"] != -1])


def W6_all_events_unioned(ob):
    """Every registry event treated as 'same node', splits included."""
    uf = UF()
    for e in ob["registry_events"]:
        uf.union(e["new_code"], e["old_code"])
    return _conc(ob, [(uf.find(r["asn_site_code"]), r["amount"]) for r in ob["spend_lines"]
                      if r["period"] in WINDOW and r["asn_site_code"] != -1])


def W7_transitive_closure_all(ob):
    """Connected components over every relationship edge: codes, vendors, parents."""
    uf = UF()
    pm = {v["vendor_code"]: v["parent_id"] for v in ob["vendor_master"]}
    for r in ob["spend_lines"]:
        uf.union(("v", r["vendor_code"]), ("p", pm.get(r["vendor_code"], -1)))
        if r["asn_site_code"] != -1:
            uf.union(("v", r["vendor_code"]), ("c", r["asn_site_code"]))
    for e in ob["registry_events"]:
        uf.union(("c", e["new_code"]), ("c", e["old_code"]))
    return _conc(ob, [(uf.find(("v", r["vendor_code"])), r["amount"])
                      for r in ob["spend_lines"] if r["period"] in WINDOW])


def W8_drop_unattributed_raw(ob):
    return _conc(ob, [(r["asn_site_code"], r["amount"]) for r in ob["spend_lines"]
                      if r["period"] in WINDOW and r["asn_site_code"] != -1])


def W9_unattributed_to_vendor_primary(ob):
    """Correct resolution, but unattributed lines all go to the vendor's single largest node."""
    keys = _resolve(ob)
    mix = collections.defaultdict(lambda: collections.defaultdict(float))
    for r, k in zip(ob["spend_lines"], keys):
        if k is not None:
            mix[r["vendor_code"]][k] += r["amount"]
    pairs = []
    for r, k in zip(ob["spend_lines"], keys):
        if r["period"] not in WINDOW:
            continue
        if k is not None:
            pairs.append((k, r["amount"]))
        else:
            m = mix.get(r["vendor_code"])
            if m:
                pairs.append((max(m, key=m.get), r["amount"]))
    return _conc(ob, pairs)


def W10_ignore_transfers_vendor_attrib(ob):
    """Attribute through the vendor master's primary node instead of the shipment record."""
    keys = _resolve(ob)
    prim = collections.defaultdict(lambda: collections.defaultdict(float))
    for r, k in zip(ob["spend_lines"], keys):
        if k is not None:
            prim[r["vendor_code"]][k] += r["amount"]
    pairs = []
    for r in ob["spend_lines"]:
        if r["period"] not in WINDOW:
            continue
        m = prim.get(r["vendor_code"])
        if m:
            pairs.append((max(m, key=m.get), r["amount"]))
    return _conc(ob, pairs)


def W11_acquisition_as_identity(ob):
    """Correct node resolution, then nodes sharing a post-acquisition parent merged together."""
    keys = _resolve(ob)
    pm = {v["vendor_code"]: v["parent_id"] for v in ob["vendor_master"]}
    acq = {e["acquired"]: e["acquirer"] for e in ob["ownership_events"]}
    node_parent = {}
    for r, k in zip(ob["spend_lines"], keys):
        if k is not None:
            p = pm.get(r["vendor_code"], -1)
            node_parent.setdefault(k, acq.get(p, p))
    return _conc(ob, [(node_parent.get(k, k), r["amount"])
                      for r, k in zip(ob["spend_lines"], keys)
                      if k is not None and r["period"] in WINDOW])


WRONG = {"W1_raw_vendor": W1_raw_vendor, "W2_vendor_after_migration": W2_vendor_after_migration,
         "W3_parent_rollup": W3_parent_rollup, "W4_raw_site_code": W4_raw_site_code,
         "W5_renames_only": W5_renames_only, "W6_all_events_unioned": W6_all_events_unioned,
         "W7_transitive_closure_all": W7_transitive_closure_all,
         "W8_drop_unattributed_raw": W8_drop_unattributed_raw,
         "W9_unattributed_to_vendor_primary": W9_unattributed_to_vendor_primary,
         "W10_ignore_transfers_vendor_attrib": W10_ignore_transfers_vendor_attrib,
         "W11_acquisition_as_identity": W11_acquisition_as_identity}


# ---------------------------------------------------------------- CHEAP-SOLVE PANEL
def C_material_group(ob):
    return _conc(ob, [(r["material_group"], r["amount"]) for r in ob["spend_lines"] if r["period"] in WINDOW])


def C_line_counts_raw_code(ob):
    return _conc(ob, [(r["asn_site_code"], 1.0) for r in ob["spend_lines"]
                      if r["period"] in WINDOW and r["asn_site_code"] != -1])


def C_code_prefix(ob):
    return _conc(ob, [(str(r["asn_site_code"])[0], r["amount"]) for r in ob["spend_lines"]
                      if r["period"] in WINDOW and r["asn_site_code"] != -1])


def C_post_rework_only(ob):
    """Use only data after the registry rework, where codes are already clean, then extrapolate."""
    rp = ob["registry_period"]
    return _conc(ob, [(r["asn_site_code"], r["amount"]) for r in ob["spend_lines"]
                      if r["period"] >= rp and r["asn_site_code"] != -1])


def C_constant_breach(ob):
    return {"top1_share": float("nan"), "top3_share": float("nan"), "hhi": float("nan"),
            "n_nodes": 0, "decision": "breach"}


def C_constant_within(ob):
    return {"top1_share": float("nan"), "top3_share": float("nan"), "hhi": float("nan"),
            "n_nodes": 0, "decision": "within_limit"}


def C_full_history_window(ob):
    """Correct resolution but the whole 24 months instead of the trailing 12."""
    keys = _resolve(ob)
    return _conc(ob, [(k, r["amount"]) for r, k in zip(ob["spend_lines"], keys) if k is not None])


CHEAP = {"C_material_group": C_material_group, "C_line_counts_raw_code": C_line_counts_raw_code,
         "C_code_prefix": C_code_prefix, "C_post_rework_only": C_post_rework_only,
         "C_constant_breach": C_constant_breach, "C_constant_within": C_constant_within,
         "C_full_history_window": C_full_history_window,
         "C_raw_vendor": W1_raw_vendor, "C_raw_site": W4_raw_site_code, "C_parent": W3_parent_rollup}
