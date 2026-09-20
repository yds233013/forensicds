"""G33 pilot: supply-node concentration under entity measurement error (research only).

THE LATENT OBJECT
-----------------
A **production node**: one physical place where goods are made. Disruption risk attaches to the
node -- if it stops, all spend produced there stops, whatever vendor code, legal entity or parent
company the purchase order named.

WHY THE OBSERVED IDS ARE NOT THE NODE
-------------------------------------
  vendor code   a commercial relationship in the ERP. Many per node; some (distributors) span nodes.
  parent id     who owns the vendor code. Changes on acquisition; two parents can share one node
                (contract manufacturing).
  registry code what an ASN names as ship-from. Not 1:1 with the node, because of three events:
        rename  node keeps identity, code changes                     c -> c'
        merge   ONE node had been recorded under two codes             c1,c2 -> c1
        split   ONE code had been covering TWO nodes                   c -> c and c_new

Every one of those is recoverable from the artefacts:
  * merge: the registry event states the two codes refer to one node;
  * split: after the rework the two nodes report different codes, and their material groups are
    disjoint, so the post-rework mapping can be carried backward;
  * transfer: a material group's production moves node on a date, and ASNs name the new node from
    that date, so anyone attributing through shipments gets it right and anyone attributing
    through the vendor master does not.

Nothing in the graded truth requires a convention the analyst cannot observe.
"""
from __future__ import annotations

import copy

import numpy as np

N_PERIODS = 24
WINDOW = list(range(12, 24))          # trailing 12 months; the estimand's window

BASE = {
    "name": "visible",
    "n_parents": 9,
    "n_nodes": 24,
    "n_vendors": 70,
    "lines_per_period": 300,
    "p_distributor": 0.20,
    "p_no_asn": 0.08,
    "erp_migration_period": 9,
    "registry_period": 14,
    "n_renames": 5,
    "n_merges": 3,
    "n_splits": 3,
    "n_acquisitions": 2,
    "n_contract_mfg": 3,
    "n_transfers": 2,
    "conc_alpha": 0.55,               # Dirichlet concentration of node spend shares (lower = more concentrated)
    "top_node_boost": 3.2,
    "threshold": 0.25,
}

REGIMES = {
    "visible": {},
    "migration_heavy": {"n_renames": 9, "n_merges": 5, "n_splits": 5, "erp_migration_period": 6},
    "ownership_heavy": {"n_acquisitions": 4, "n_contract_mfg": 7},
    # concentration genuinely BELOW the board limit: the correct decision flips
    "fragmented_below_limit": {"top_node_boost": 0.9, "conc_alpha": 1.6, "n_vendors": 110},
    "thin_asn": {"p_no_asn": 0.22},
}


def regime(name: str) -> dict:
    s = copy.deepcopy(BASE)
    s.update(copy.deepcopy(REGIMES[name]))
    s["name"] = name
    return s


def draw_world(spec: dict, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    nn, nv, npar = spec["n_nodes"], spec["n_vendors"], spec["n_parents"]
    rp, mp = spec["registry_period"], spec["erp_migration_period"]

    # ---------- latent nodes ----------
    share = rng.dirichlet(np.full(nn, spec["conc_alpha"]))
    share[0] *= spec["top_node_boost"]
    share = share / share.sum()
    node_parent = rng.integers(0, npar, nn)
    # material groups: disjoint across the node pairs that a registry split must separate
    mg_pool = list(range(40))
    rng.shuffle(mg_pool)
    node_mg = {}
    cur = 0
    for s in range(nn):
        k = int(rng.integers(2, 5))
        node_mg[s] = mg_pool[cur:cur + k] or [mg_pool[0]]
        cur = (cur + k) % (len(mg_pool) - 5)

    # ---------- registry codes ----------
    # canon[] collapses nodes that the registry later reveals were always ONE node.
    canon = {s: s for s in range(nn)}
    code_pre, code_post, legacy_alias = {}, {}, {}
    for s in range(nn):
        code_pre[s], code_post[s] = 500 + s, 500 + s
    reg_events = []
    pool = [int(x) for x in rng.permutation(nn)]
    p = 0

    # rename: same node, new code from the rework onward
    for s in pool[p:p + spec["n_renames"]]:
        code_post[s] = 700 + s
        reg_events.append({"old_code": 500 + s, "new_code": 700 + s, "period": rp, "type": "rename"})
    p += spec["n_renames"]

    # merge: node b was never a separate place - it is node a under a second legacy code.
    merged_nodes = []
    for _ in range(spec["n_merges"]):
        if p + 1 >= len(pool):
            break
        a, b = pool[p], pool[p + 1]; p += 2
        canon[b] = a
        legacy_alias.setdefault(a, []).append(500 + b)     # a's lines may carry b's legacy code
        merged_nodes.append((a, b))
        reg_events.append({"old_code": 500 + b, "new_code": code_post[a], "period": rp, "type": "merge"})

    # split: one legacy code covered two genuinely different nodes; disjoint material groups.
    split_pairs = []
    for i in range(spec["n_splits"]):
        if p + 1 >= len(pool):
            break
        x, y = pool[p], pool[p + 1]; p += 2
        node_mg[y] = [m for m in node_mg[y] if m not in set(node_mg[x])] or [mg_pool[-(i + 1)]]
        code_pre[y] = code_pre[x]                          # indistinguishable before the rework
        code_post[y] = 800 + y
        split_pairs.append((x, y))
        reg_events.append({"old_code": code_pre[x], "new_code": 800 + y, "period": rp, "type": "split"})

    # ---------- ownership ----------
    acquisitions = []
    for _ in range(spec["n_acquisitions"]):
        a, b = rng.choice(npar, 2, replace=False)
        acquisitions.append({"acquirer": int(a), "acquired": int(b), "period": int(rng.integers(3, 20))})

    def parent_at(node, period):
        q = int(node_parent[node])
        for ev in sorted(acquisitions, key=lambda e: e["period"]):
            if period >= ev["period"] and q == ev["acquired"]:
                q = ev["acquirer"]
        return q

    # ---------- vendors ----------
    vendors = []
    for v in range(nv):
        k = int(rng.integers(2, 4)) if rng.random() < spec["p_distributor"] else 1
        nodes = rng.choice(nn, size=k, replace=False, p=share).tolist()
        vendors.append({"vendor": v, "nodes": [int(x) for x in nodes],
                        "parent": parent_at(int(nodes[0]), 0)})
    # contract manufacturing: a node served by a vendor belonging to a DIFFERENT parent
    cm = []
    for s in rng.choice(nn, size=min(spec["n_contract_mfg"], nn), replace=False).tolist():
        other = [q for q in range(npar) if q != parent_at(int(s), 0)]
        v = int(rng.integers(0, nv))
        vendors[v]["nodes"] = [int(s)]
        vendors[v]["parent"] = int(rng.choice(other))
        cm.append(int(s))

    node_vendors = {s: [v["vendor"] for v in vendors if s in v["nodes"]] for s in range(nn)}
    for s in range(nn):
        if not node_vendors[s]:
            v = int(rng.integers(0, nv))
            vendors[v]["nodes"].append(s)
            node_vendors[s] = [v]

    # ---------- production transfers ----------
    transfers = []
    for _ in range(spec["n_transfers"]):
        x, y = rng.choice(nn, 2, replace=False)
        x, y = int(x), int(y)
        if not node_mg[x]:
            continue
        mg = int(rng.choice(node_mg[x]))
        t = int(rng.integers(13, 22))
        transfers.append({"from_code_at_event": code_post[x], "to_code_at_event": code_post[y],
                          "material_group": mg, "period": t, "_from": x, "_to": y})

    def effective_node(node, mg, period):
        for t in transfers:
            if period >= t["period"] and node == t["_from"] and mg == t["material_group"]:
                return t["_to"]
        return node

    # ---------- ERP vendor renumbering ----------
    code_new = {v: 1000 + v for v in range(nv)}
    migration_log = []
    cand = list(rng.permutation(nv))
    for i in range(0, min(6, len(cand) - 1), 2):        # many-to-one on vendors serving the same node set
        a, b = int(cand[i]), int(cand[i + 1])
        if vendors[a]["nodes"] == vendors[b]["nodes"] and vendors[a]["parent"] == vendors[b]["parent"]:
            code_new[b] = code_new[a]
            migration_log.append({"old_vendor_code": 1000 + b, "new_vendor_code": code_new[a],
                                  "period": mp, "type": "many_to_one"})
    for i in range(6, min(10, len(cand))):              # one-to-many
        a = int(cand[i])
        code_new[a] = 2000 + a
        migration_log.append({"old_vendor_code": 1000 + a, "new_vendor_code": 2000 + a,
                              "period": mp, "type": "renumber"})

    # ---------- spend lines ----------
    rows = []
    for period in range(N_PERIODS):
        picks = rng.choice(nn, size=spec["lines_per_period"], p=share)
        for node in picks:
            node = int(node)
            mg = int(rng.choice(node_mg[node])) if node_mg[node] else 0
            eff = effective_node(node, mg, period)          # where it is actually produced now
            v = int(rng.choice(node_vendors[node]))         # the commercial relationship is unchanged
            code = (1000 + v) if period < mp else code_new[v]
            amount = float(np.round(rng.lognormal(9.2, 0.8), 2))
            c = canon[eff]
            if rng.random() > spec["p_no_asn"]:
                if period < rp:
                    opts = [code_pre[c]] + legacy_alias.get(c, [])
                    asn = int(rng.choice(opts)) if len(opts) > 1 else code_pre[c]
                else:
                    asn = code_post[c]
            else:
                asn = -1
            rows.append({"period": period, "vendor_code": code, "amount": amount,
                         "material_group": mg, "asn_site_code": asn, "_node": canon[eff], "_vendor": v})

    rows = [rows[i] for i in rng.permutation(len(rows))]     # defeat row-order leakage

    vendor_master = []
    for v in range(nv):
        vendor_master.append({"vendor_code": 1000 + v, "valid_from": 0, "valid_to": mp - 1,
                              "parent_id": vendors[v]["parent"]})
        vendor_master.append({"vendor_code": code_new[v], "valid_from": mp, "valid_to": N_PERIODS,
                              "parent_id": vendors[v]["parent"]})

    return dict(spec=spec, seed=seed, rows=rows, vendors=vendors, node_parent=node_parent,
                acquisitions=acquisitions, transfers=transfers, migration_log=migration_log,
                reg_events=reg_events, legacy_alias=legacy_alias, split_pairs=split_pairs, canon=canon,
                merged_nodes=merged_nodes, code_pre=code_pre, code_post=code_post,
                node_mg=node_mg, vendor_master=vendor_master, nn=nn, cm=cm,
                registry_period=rp, migration_period=mp, share=share)


# ------------------------------------------------------------------ metrics
def concentration(agg: dict, threshold: float) -> dict:
    tot = sum(agg.values())
    if tot <= 0:
        return {"top1_share": float("nan"), "top3_share": float("nan"), "hhi": float("nan"),
                "n_nodes": 0, "decision": "unknown"}
    sh = sorted((v / tot for v in agg.values()), reverse=True)
    return {"top1_share": float(sh[0]), "top3_share": float(sum(sh[:3])),
            "hhi": float(sum(x * x for x in sh)), "n_nodes": len(agg),
            "decision": "breach" if sh[0] > threshold else "within_limit"}


def truth(world: dict) -> dict:
    agg = {}
    for r in world["rows"]:
        if r["period"] in WINDOW:
            agg[r["_node"]] = agg.get(r["_node"], 0.0) + r["amount"]
    return concentration(agg, world["spec"]["threshold"])


def observed(world: dict) -> dict:
    """Exactly what an analyst can see. No _node, no _vendor, no share vector."""
    rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in world["rows"]]
    reg = [{k: v for k, v in e.items() if not k.startswith("_")} for e in world["reg_events"]]
    tr = [{k: v for k, v in t.items() if not k.startswith("_")} for t in world["transfers"]]
    return dict(spec=world["spec"], spend_lines=rows, vendor_master=world["vendor_master"],
                migration_log=world["migration_log"], registry_events=reg,
                ownership_events=world["acquisitions"], transfer_log=tr,
                registry_period=world["registry_period"],
                migration_period=world["migration_period"], threshold=world["spec"]["threshold"])
