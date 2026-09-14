# G17: B2B customer entity resolution through resellers, shared trials and acquisitions (detailed design)

Status: generation-3 design. Not built. No model run. Fictional company, systems and vendors throughout.

## Workspace sketch

```
/workspace
  README.md                                  repo purpose, run command, owners
  CHANGELOG.md                               c360 2.0.0 "graph resolver" (neutral wording), earlier 1.x entries
  c360/                                      Python package (pandas + duckdb)
    cli.py                                   `python -m c360 run --through YYYY-MM`
    extract/billing.py, crm.py, product.py,  column-minimal SELECTs (see §22: tax id, transfers, SSO
      support.py, orggraph.py                  verification, deal register are NOT loaded)
    resolve/normalize.py                     email → registrable domain, lower-casing, punycode
    resolve/graph_resolver.py                FAULTY: union-find over BA–domain–workspace–CRM–support edges
    hierarchy/parents.py                     FAULTY: OrgGraph current `ultimate_parent_ogid`, all relationship types
    build/customer_month.py                  FAULTY: static ba→customer map joined to every month
    metrics/concentration.py                 top-20 ARR share per month (definition correct)
    metrics/enterprise_churn.py              FAULTY by omission: customer-id disappearance = churn
  config/resolver.yaml                       edge types on/off, free-email list path
  config/free_email_domains.txt              412 consumer mail domains
  data/warehouse.duckdb                      ~310 MB (tables in §7)
  data/orggraph/entities_2026-06-15.parquet  3,940 legal entities (vendor snapshot)
  data/orggraph/relationships_2026-06-15.parquet  2,210 parent edges with relationship_type
  data/orggraph/web_domains_2026-06-15.parquet    5,120 domain → ogid rows
  data/corpdev/deal_register.csv             CorpDev/Legal register, 17 rows
  data/partners/partner_directory.csv        enrolled resellers/agencies, 31 rows
  data/stewardship/review_decisions.csv      418 steward-reviewed node pairs
  docs/c360_data_catalog.md                  output schemas, customer_id scheme, source table grains
  docs/billing_data_dictionary.md            billing tables incl. tax id masking and ownership changes
  docs/finance/board_pack_methodology.md     FP&A definitions of customer group, concentration, enterprise churn
  docs/vendor/orggraph_guide.md              vendor field semantics, refresh cadence, relationship types
  docs/product/sso_domain_verification.md    help-centre article: DNS TXT verification
  docs/partners/partner_program.md           how partners are added to customer accounts
  docs/stewardship/process.md                how review pairs are queued and decided
  notebooks/resolver_v2_launch_eval.ipynb    precision/recall of v1 vs v2 on the steward sample (attractor)
  reports/board_pack/2026-Q2_customer_concentration.csv   v1 numbers (published)
  reports/board_pack/2026-08_preread_concentration.csv    v2 numbers (held)
  reports/board_pack/2026-08_preread_enterprise_churn.csv v2 (zero churn)
  notes/2026-08-21_cfo_email.md, notes/revops_slack_export.jsonl (generated, ~140 msgs)
  logs/resolver_runs.jsonl, logs/deployments.csv
```

Sizes: 2,400 billing accounts, 3,100 CRM accounts, 5,600 workspaces (1,900 trials), 61k workspace members, 2,050
support orgs, 28,800 billing-account-months of MRR (2025-09..2026-08).

## 1. Research question

When a customer entity must be resolved from conflicting weak keys (email domains, workspace membership, names) and
strong but incomplete keys (full, masked or missing tax ids; effective-dated ownership; dated corporate events), can an
agent reconstruct a **per-month** customer-group partition whose evidence semantics survive agencies, shared trials,
acquisitions and ownership transfers, and propagate it correctly into concentration and churn metrics? And can it tell
that a biased precision/recall sample does not validate its resolver?

## 2. Enterprise setting

Corvane (fictional) sells a workflow-automation SaaS to mid-market and enterprise companies. The RevOps analytics team
owns `c360`, which builds `customer_month` (billing account × month → customer group, ARR) from four operational
systems — billing, CRM, product workspaces, support — plus the OrgGraph firmographics vendor. FP&A uses it for the
board pack: top-20 customer concentration and enterprise logo churn. Partners (resellers, marketing agencies, managed
service providers) routinely appear as billing contacts and workspace admins on client accounts. Trials are often joint
pilots with several companies' staff in one workspace.

## 3. Visible symptom (instruction memo)

From the CFO: the August board pre-read shows top-20 customer concentration at 44.2% against 31.0% in the published Q2
pack, and zero enterprise logo churn for the trailing four quarters, where the Q2 pack reported 3–5 per quarter. Sales
says the Halvard Group expansion "explains a lot of it". The CFO does not know whether concentration really rose or
whether "the new customer matching" is wrong, and the pre-read is held.

Required: `python -m c360 run --through 2026-08` must write `out/customer_month.parquet`,
`out/concentration_monthly.csv` and `out/enterprise_churn_quarterly.csv` in the formats in `docs/c360_data_catalog.md`,
correct under Finance's board-pack definitions for every month in the extract; source data under `data/` is
authoritative and must not be modified; no special-casing of customers, domains, partners, deals or dates; validate
before handing over.

The memo does not mention domains, resellers, OrgGraph, acquisitions or tax ids.

## 4. Source distribution inspiration

- Customer-360 / master-data programmes that link CRM, billing and product identities; account-based B2B analytics
  where email domain is the default join key. Domain matching's weakness with agencies, MSPs and consultancies is folk
  knowledge among RevOps teams.
- Effective-dated corporate hierarchies from firmographics vendors (ultimate-parent fields, periodic refresh, stale
  M&A). Board concentration metrics that are usually presented "as at" period end.
- Entity-resolution practice: blocking keys vs matching keys, must-link/cannot-link constraints, clerical review
  samples and their selection bias (classic record-linkage literature on clerical review; *to verify* specific
  references — none are cited in agent-facing files).

## 5. Causal graph / ground truth

Generator (`build/world.py`, stdlib, seeded) creates, in order:

1. **Legal entities** (3,940, OrgGraph ids `og-XXXXXXX`), each with `country`, `registration_id`, `registered_postcode`,
   legal name, 1–3 web domains. 610 entities are Corvane customers; 1,400 are look-alike distractors (similar names).
2. **True parent timeline**: an operating-parent edge set that changes only through dated corporate events:
   - 9 acquisitions inside the period (close dates 2025-10-07 … 2026-07-22; one closes 2026-03-31, a month-end boundary;
     one two-level chain: Ferrow Labs acquired by Oakline 2025-11-18, Oakline acquired by Pellam Group 2026-04-09);
   - 2 divestitures (Talon Logistics leaves Halvard Group on 2026-03-02 to a financial sponsor);
   - 1 terminated deal (signed 2026-02-10, terminated 2026-07-20; never closed);
   - 3 deals with `sign_date` and `close_date` in different months;
   - 4 financial-sponsor ownership edges (`portfolio_investment`), which never combine groups.
3. **Billing accounts** (2,400): owner legal entity at creation; 64 **ownership changes**
   (`ba_ownership_changes`): 40 agency-to-client handovers (agency bought on client's behalf, then assigned), 6
   spin-off assignments, 18 intra-group assignments. Billing's `billing_accounts.tax_id` shows the **current** owner.
4. **Tax id presence**: full for 70.4% of BAs, masked (`DE*******4471`: country + last 4, legacy billing migration) for
   10.8%, missing for 18.8% (self-serve card accounts). 9 masked (country, last4) collisions among registry entities,
   all separated by postcode. 31 full tax ids are not in OrgGraph (unregistered small entities).
5. **Contacts and domains**: billing contacts use the owner's domain with probability 0.83, a free-mail domain 0.09,
   a **partner domain** 0.08 (partner manages billing). 7 glue domains: 4 enrolled partners (`northbeam.io`,
   `vantagecloud.co`, …), 3 not enrolled (`brightlane.co` agency, `ostrava-it.cz` MSP, `kellerassoc.com`
   consultancy). Together they touch 212 BAs of 171 unrelated legal entities. Each partner is also a genuine customer
   with its own BA(s) under its own tax id.
6. **Workspaces**: enterprise workspaces link to BAs (`workspace_billing_links`, dated). 38 **shared trial
   workspaces** have members from 3–9 companies (joint pilots, partner sandboxes); 11 converted and link to one BA.
   `workspace_sso_domains` has DNS-verified domains (with `verified_at`, `removed_at`), always owned by the linked BA's
   owner entity at that time.
7. **Domain shared across entities**: after the Talon divestiture, Talon keeps `halvard.com` mailboxes for 4 months
   under a transition-services arrangement (contacts only, not SSO).
8. **MRR** per BA × month (`mrr_monthly`). Real **Halvard expansion**: +$2.38M ARR from 2026-07-01 (CRM
   closed-won opportunity, Slack celebration). Kestrel Analytics (acquired by Halvard 2026-05-14) migrates its
   subscriptions onto Halvard's master BA on 2026-06-01 (Kestrel BAs go to 0 MRR).
9. **Real enterprise churners**: 16 over four quarters; 7 had agency/partner billing contacts or shared-trial membership
   (e.g. Quillmark Media, billing contact `@brightlane.co`, churned 2026-02).
10. **Vendor snapshot** (OrgGraph 2026-06-15): current edges as of that date, *including* the pending (later
    terminated) deal edge, *excluding* the 2026-07-22 acquisition, and ultimate parents computed across all
    relationship types (so sponsor portfolios roll up to funds).
11. **CRM hierarchy** (`crm_accounts.parent_crm_account_id`) maintained by sales ops: realigned 1–5 months after
    deals; partner "book" umbrella accounts exist.
12. **Steward review sample** (418 pairs), drawn from the **v1 name-similarity queue** (score band 0.55–0.80) between
    2025-11 and 2026-08; decisions `same`/`different`/`unsure` are true **as of `review_date`**.

Headline truth (visible): top-20 concentration 2026-06 32.9%, 2026-07 35.1%, 2026-08 35.4%; enterprise churn 4/3/5/4
(Q3-25…Q2-26). v2 shows 44.2% and 0/0/1/0. v1 (published Q2) showed 31.0% for June.

## 6. Latent statistical/business invariant (oracle truth)

For each month `m` (state at the end of the last day of `m`) and each billing account `b` with any MRR row in `m`:

1. **Owner legal entity** `e(b,m)`: the owner in effect at month-end, replaying `ba_ownership_changes` backwards from
   the current `tax_id` (effective_date = first day the new owner is party).
2. **Entity identification**: full tax id → registry entity by (country, registration_id); if absent from the registry,
   entity key `tax:<CC>-<id>`. Masked tax id → unique registry entity with same country, last 4 and
   `registered_postcode = bill_to_postcode`; else unresolved. Missing tax id → entity owning a DNS-verified SSO domain
   (verified ≤ month-end < removed) of a workspace linked to `b` at month-end, via OrgGraph web domains; else unresolved.
   Unresolved → customer `ba:<ba_id>`.
   **Email domains, workspace membership, names, CRM hierarchy and partner status are never identity evidence.**
3. **Group** `g(e,m)`: follow operating-parent edges (`subsidiary`, `branch`; never `portfolio_investment`) in effect at
   month-end: the OrgGraph snapshot edges, minus edges from deals whose `close_date` is after month-end (restoring
   `prior_parent_registration_id`), minus edges of terminated deals, plus edges of closed deals absent from the
   snapshot. `close_date` governs; `sign_date` never does. `customer_id` = OrgGraph id of the top entity (or its
   `tax:` key).
4. **Downstream**: ARR = 12 × MRR. Concentration(m) = ARR of top-20 customers / total ARR. Enterprise customer at
   quarter start = customer with ARR ≥ $250k on the last month of the prior quarter; churned if its ARR on the quarter's
   last month is 0 **and** its top entity did not become part of another group through a closed acquisition during the
   quarter (M&A consolidation is not churn; FP&A definition).

## 7. Grains and state variables

| Grain | Key | State that varies |
|---|---|---|
| billing account × month | (`ba_id`, month) | owner entity, MRR, workspace links, SSO domains |
| legal entity × month | (ogid or tax key, month) | operating parent |
| customer group × month | (`customer_id`, month) | member BAs, ARR, rank |
| customer × quarter | (`customer_id`, quarter) | enterprise flag, churn/consolidation status |
| node pair (steward) | (left, right, review_date) | same/different as of date |
| deal | `deal_id` | sign, close, status |

The trap grain: v2's and most repairs' `ba_id → customer_id` is **static**. Correctness requires state per
(BA, month) and (entity, month) — the Task 02 lesson transposed to identity.

## 8. Evidence graph

| Artifact | Shows | On natural path? |
|---|---|---|
| CFO memo + held pre-read CSVs | 44.2% vs 31.0%; zero churn | yes |
| `reports/board_pack/2026-08_preread_concentration.csv` | top-20 list: "Northbeam Partners" #2 ($9.1M), "Brightlane" #5 | yes |
| `graph_resolver.py` + `resolver.yaml` | edges: contact domain, workspace member domain, support domain, CRM link; free-mail blocklist | yes |
| `logs/resolver_runs.jsonl` | largest component sizes per run (v2: 96 BAs) | likely |
| `warehouse.duckdb` billing tables | tax id full/masked/missing; `ba_ownership_changes` | yes, once clusters are inspected |
| `docs/billing_data_dictionary.md` | masking format; ownership change semantics; `tax_id` is current owner | yes |
| `workspace_members`, `workspace_sso_domains` | multi-company trials; verified domains | yes |
| `docs/product/sso_domain_verification.md` | verification requires DNS TXT control of the domain | medium |
| `docs/partners/partner_program.md` | partners may be billing contacts and workspace admins for clients; order form names contracting party | medium |
| `partner_directory.csv` | 31 enrolled partners (not the 3 informal glue domains) | yes (attractor for list-based un-merge) |
| OrgGraph snapshot + guide | ultimate parent, relationship types, snapshot date, "reflects announced transactions" | yes (attractor: retroactive) |
| `corpdev/deal_register.csv` | sign/close/status, registration ids, prior parent | medium (must be found) |
| `docs/finance/board_pack_methodology.md` | customer group = operating group of contracting legal entity at period end; sponsors don't combine; M&A consolidation not churn | yes |
| Q1-2026 board pack footnote (in `2026-Q2_customer_concentration.csv` header comment) | "Talon Logistics included in Halvard Group for January–February; separate from March" — a presentation precedent, not a rule; the same v1 pack keeps Kestrel separate in June because CRM was not yet realigned (a v1 error) | medium |
| `review_decisions.csv` + launch notebook | v2 precision 0.97 / recall 0.94 on the sample | yes (attractor: biased validation) |
| Halvard CRM opportunity + Slack | real +$2.38M expansion | yes (attractor: "concentration is real") |

## 9. Evidence authority hierarchy

| Conflict | Governs | Why |
|---|---|---|
| Billing `tax_id` (current) vs historical ownership | `ba_ownership_changes` for months before a change | billing dictionary: current row shows current party; changes table is the audit of assignment |
| Email/workspace domains vs tax id | tax id | a domain identifies a mailbox operator; partner programme doc shows partners on client accounts; tax id identifies the contracting legal entity named by methodology |
| DNS-verified SSO domain vs contact domain | verified SSO | verification proves domain control by the workspace's organisation; contact domains are unverified |
| OrgGraph current parent vs deal register | deal register for dates/status; OrgGraph for long-standing edges | vendor guide: snapshot, reflects announced deals, refreshed quarterly; register is Legal's record of close |
| OrgGraph `ultimate_parent_ogid` vs relationship types | operating edges only | methodology: financial sponsors do not combine customers |
| CRM parent hierarchy | never for grouping | sales territory structure, realigned late, includes partner books |
| Steward decisions | pairwise truth as of `review_date` only | process doc: queue is v1 low-confidence name matches; decisions record the group at review time |
| Launch notebook P/R | not evidence of correctness | computed on the biased sample |
| Published Q2 pack (v1) | not an answer key | v1 used CRM hierarchy (known stale) |

## 10. Plausible hypotheses

| # | Hypothesis | For | Against |
|---|---|---|---|
| H1 | Concentration really rose (Halvard expansion + Kestrel acquisition) | CRM $2.38M closed-won; Slack; Halvard is #1 | explains ~2.5 pts, not 13; Northbeam/Brightlane in top 5 are agencies |
| H2 | Resolver over-merges via partner/agency domains | top-5 contains partners; 96-BA component | also needs shared trials and the 3 non-enrolled domains |
| H3 | Retroactive/incorrect hierarchy | OrgGraph snapshot applied to all months; terminated deal edge | changes history, barely changes August |
| H4 | Churn metric broken independently | zero churn even in quarters with known lost logos | mostly caused by glue absorption; but also M&A consolidation must be handled |
| H5 | Billing data/MRR error (e.g. Kestrel migration double-counting) | Kestrel BAs → 0 and Halvard master up in June | totals tie to billing; migration is real |
| H6 | v1 was right, revert | published and familiar | v1 misses acquisitions, CRM stale, no self-serve resolution |

## 11. Why each wrong hypothesis is plausible

- **H1** has a real, large, recent deal and a plausible narrative from Sales; the "right" August number (35.4%) is
  itself higher than Q2's 31.0%, so a repair landing at 35–37% "confirms" part of H1.
- **H5**: Kestrel's migration creates a visible MRR discontinuity exactly in the window of interest.
- **H6**: reverting to published history is exactly the Task 04 failure pattern (trusting a published number).
- **H3 alone**: the agent that finds OrgGraph staleness first may believe hierarchy is the whole story.

## 12. Investigation path (expected 45–75 actions)

1. (1–6) Memo, README, pre-read CSVs, CHANGELOG, deployments: v2 went live 2026-08-05 and restated history.
2. (7–12) Read resolver, config, customer_month builder, metrics. Run pipeline, reproduce 44.2%.
3. (13–18) Inspect largest components: Northbeam component contains 41 legal names and 38 distinct full tax ids.
   **Discovery 1**: domain glue. Look at edge provenance → partner billing contacts.
4. (19–24) Remove partner edges via directory → Brightlane still glued (not enrolled). **Discovery 2**: lists are
   incomplete; tax-id conflicts show which components are impure. Shared-trial workspaces glue a second family of
   components (member domains of 3–9 companies). **Discovery 3**.
5. (25–32) Read billing dictionary: masked tax ids and ownership changes. Find agency→client handovers:
   the current `tax_id` is the client for accounts that the agency paid for until handover. **Discovery 4**: owner
   is month-dependent.
6. (33–40) Self-serve BAs without tax id: contact domains are weak; SSO doc and `workspace_sso_domains` give a
   verified link. Check steward notes on agency-managed pairs.
7. (41–50) Hierarchy: OrgGraph guide (snapshot date, announced deals, relationship types); methodology (period end,
   sponsors); find deal register; reconcile terminated deal and post-snapshot acquisition. **Discovery 5**: effective
   dating; sponsor portfolios.
8. (51–58) Rebuild per-month map; rewrite churn with M&A consolidation. **Discovery 6** (only if churn is checked at
   customer level): Kestrel appears as churn in Q2-26.
9. (59–75) Validate: cluster purity (no component with ≥2 registry entities lacking an operating-parent path in that
   month), BA-month coverage equals MRR rows, ARR totals equal billing, steward sample agreement *restricted to
   review-date months*, top-20 list reviewed by name, churn list reviewed, re-run determinism.

## 13. Natural wrong implementation

After Discovery 1, the natural repair is in `graph_resolver.py`:

```python
EDGE_TYPES = ["billing_contact_domain", "support_domain", "crm_link"]   # drop workspace_member_domain
blocked = free_email | set(partner_directory.domain)                    # add partner domains
# keep union-find, keep OrgGraph ultimate_parent for the cluster, keep static map
```

Numerically (visible): August concentration 37.9%; the three non-enrolled glue domains keep 2 of the top-20 wrong;
Talon's `halvard.com` TSA contacts re-glue Talon into Halvard after divestiture; all 64 ownership changes are
assigned to the current owner for all months; Kestrel is merged into Halvard for 2025-09..2026-04; the terminated
deal merges two unrelated customers for all 12 months; enterprise churn 2/1/3/1. Cluster-month mismatches: 3,420 of
28,800 BA-months.

A second, equally natural implementation is **domain + fuzzy name** (`rapidfuzz` token-set ≥ 90 within
country): 36.2% in August, merges "Bluebird Dental – Austin" franchisees (independent legal entities, 14 BAs) and
"Meridian Partners LLC" with "Meridian Health Partners"; misses Kestrel→Halvard; 2,960 mismatches.

Both keep the faulty `build/customer_month.py` shape: one `ba_id → customer_id` map joined to all months.

## 14. Second-order failure modes

| After rejecting… | Next natural repair | What it still gets wrong (visible) |
|---|---|---|
| partner-list blocking | "domain is a key unless its component contains conflicting full tax ids" (cannot-link split) | splits glue components but reassigns tax-id-less BAs with agency contacts to the agency entity (via OrgGraph web domain `brightlane.co`); 212 → 58 wrong BAs; still static and retroactive |
| cannot-link split | tax id as primary key, domain fallback for missing/masked | masked BAs matched by last-4 only (9 collisions wrong); missing-tax-id BAs with partner/TSA contact domains mis-grouped; 410 BA-months |
| domain fallback | tax id + verified SSO, but **current** `tax_id` for all months | 64 transferred BAs wrong before their change date (agency months attributed to clients): 1,020 BA-months; Brightlane's own ARR history understated |
| static owner | per-month owner, OrgGraph `ultimate_parent` for all months (retroactive) | August concentration exactly right (35.4%) but 2025-09..2026-05 wrong; terminated deal merges two customers; sponsor fund "Arden Peak III" combines 4 portfolio companies; churn: Kestrel absorbed pre-close hides nothing but sponsor roll-up hides one real churn |
| retroactive hierarchy | per-month hierarchy using `sign_date` | 3 deals a month early; boundary deal (close 2026-03-31) handled either way by chance |
| per-month hierarchy | churn left as "customer id disappears" | Kestrel counted as enterprise churn in Q2-26 (4 → 5); Talon divestiture does not create churn but a naive "group ARR dropped ≥90%" heuristic would |
| everything | steward overrides applied as time-invariant must-links | 3 acquired pairs reviewed after close forced together in pre-close months |
| everything | tune fuzzy threshold to maximise steward-sample F1 | picks 0.93; sample is name-similar pairs, so the threshold is irrelevant to agency/trial glue |

## 15. Correct repair properties

- Identity from legal-entity evidence only (full tax id; masked tax id confirmed by postcode; verified SSO domain for
  tax-id-less BAs); domains, names, membership, CRM hierarchy and partner status are not identity keys.
- Ownership evaluated per month through `ba_ownership_changes`.
- Group membership per month from operating-parent edges, adjusted by deal-register close dates and statuses, with
  sponsor edges excluded.
- Output at BA × month grain; downstream metrics consume that grain.
- Enterprise churn excludes M&A consolidation identified from closed acquisitions within the quarter.
- No hard-coded domains, partners, entities, deals or dates; the free-mail list becomes irrelevant, not extended.

## 16. Repair surfaces

| File | Why it must change |
|---|---|
| `extract/billing.py` | must load `tax_id`, `tax_id_masked`, `bill_to_postcode`, `ba_ownership_changes` (currently not selected) |
| `extract/product.py` | must load `workspace_billing_links` dates and `workspace_sso_domains` |
| new or rewritten `resolve/` | entity identification replaces graph union-find |
| `hierarchy/parents.py` | per-month operating-parent graph from snapshot + deal register; relationship types |
| `build/customer_month.py` | static map → (BA, month) map |
| `metrics/enterprise_churn.py` | M&A consolidation exception |

Five of six are required; a single-file edit cannot pass.

## 17. Validation requirements

Aggregate checks that are necessary but **not** sufficient: ARR total per month equals billing (true for every
variant, because every BA-month is assigned somewhere); August concentration in 34–38% (several wrong variants land
there); steward-sample precision/recall (non-discriminating, see §9).

Checks aggregates cannot replace:
- **Component purity per month**: for every customer-month, all member entities share an operating-parent path in that
  month; list violations (should be 0).
- **Transfer audit**: for each ownership change, customer before/after change date differs as expected.
- **Deal audit**: for each deal, target's customer_id in the month before and after `close_date`; terminated deal
  never merges.
- **Churn list review** by name: each churned customer has zero ARR and no closed acquisition in quarter; Kestrel is
  consolidation.
- **Steward sample restricted to `review_date` month**: agreement should be 100% on `same`/`different` pairs.
- **Top-20 by name** for June–August: no partners/agencies except where they contract directly.

## 18. Hidden fixture strategy

All fixtures are regenerated by the same generator with different seeds, id ranges and names; they vary only
documented mechanisms.

| Fixture | Invariant tested | Surface changes | Overfit caught | Same distribution because |
|---|---|---|---|---|
| `hidden_a` (2024-03..2025-02) | domain/trial non-identity; masked tax id | 11 glue domains, 7 not enrolled, glue mainly through **support-org domains** and shared trials rather than billing contacts; 22 masked collisions; a partner that contracts directly for 5 BAs (its own tax id) | partner-directory blocklists; hard-coded glue domains; "never assign BAs to partner entities" | same edge types and fields; partner-as-customer exists visibly (partners' own BAs) |
| `hidden_b` (2025-01..2025-12) | effective-dated hierarchy | two-level chain (acquirer itself acquired later), acquisition closing on a month's last day, deal signed in one quarter and closed next, two divestitures, a terminated deal, snapshot dated mid-period | `sign_date`; OrgGraph current parents; snapshot-date branch; hard-coded Halvard/Kestrel ids | all event types present visibly; month-end boundary present visibly (2026-03-31) |
| `hidden_c` (2026-01..2026-12) | ownership transfers; churn semantics | 190 ownership changes, no acquisitions except one consolidation within a quarter, enterprise churners with partner contacts, self-serve BAs with removed SSO domains mid-period | current `tax_id` for all months; churn without M&A exception; SSO without `removed_at` | transfers, SSO removal and consolidation all present visibly |

Generator constraints enforced in every fixture (listed in §23): verified SSO domains are always owned by the linked
BA's owner; no unregistered masked entity with multiple BAs; every parent change within the period is in the register;
no top-20 ARR tie.

## 19. Mutation strategy

| Mutation | Expected |
|---|---|
| `nop` | 0 |
| `oracle` | 1 |
| `alt_sql_duckdb` (full SQL implementation with recursive CTE hierarchy) | 1 |
| `alt_python_event_replay` (replays ownership and deal events month by month) | 1 |
| `alt_customer_id_singletons_uuid` (stable non-catalog ids for unresolved BAs) | 1 |
| `domain_minus_free_email` (= v2 without trial edges) | 0 |
| `domain_minus_partner_directory` | 0 (visible) |
| `domain_cannot_link_taxid` | 0 |
| `fuzzy_name_plus_domain` | 0 |
| `taxid_last4_only` | 0 |
| `current_taxid_static` | 0 |
| `retroactive_orggraph` | 0 (history, churn) |
| `sign_date_effective` | 0 (visible: 3 deals) |
| `include_sponsor_edges` | 0 |
| `crm_hierarchy_grouping` (v1 revert) | 0 |
| `churn_without_ma_exception` (everything else correct) | 0 |
| `steward_overrides_time_invariant` | 0 |
| `partial_identity_only` / `partial_hierarchy_only` | 0 |
| `overfit_hardcoded_glue_domains` (blocks the 7 visible domains, else oracle) | visible 1 on clusters, **hidden_a 0** |
| `overfit_visible_deal_dates` (hard-codes the visible register instead of reading it) | **hidden_b 0** |
| `overfit_transfer_ids` | **hidden_c 0** |
| `output_patch` / `edit_source_data` / `import_reference` | 0 |

## 20. Alternative valid implementations

- SQL vs pandas vs graph libraries: graded on outputs only.
- Customer ids: registry-resolved groups must use the catalog scheme (`og-…`, `tax:CC-…`), which the existing v2
  output already uses; unresolved BAs may use any id stable across months and unique per BA (verifier canonicalises).
- Resolving a masked tax id by postcode vs by postcode + legal-name normalisation: equivalent on all fixtures
  (generator guarantees postcode uniqueness within collisions and name consistency).
- Using `workspace_billing_links` at month-end vs any time in month: generator changes links only on the 1st.
- Deriving past hierarchy by rolling the snapshot back vs building forward from the register plus long-standing
  snapshot edges: identical by construction.

## 21. Verifier design

- Integrity: logical digests of `data/` vs regenerated pristine extract.
- Run `python -m c360 run --through 2026-08` twice as unprivileged user; outputs byte-stable after canonical sorting.
- `customer_month`: row set = MRR rows; per month, partition of BAs equals ground truth (canonicalised ids for
  singletons; exact ids otherwise). Report first 20 mismatches with evidence type.
- `concentration_monthly`: all 12 months within 0.0005 absolute (derived from exact partition; tolerance covers float).
- `enterprise_churn_quarterly`: exact churned customer sets per quarter.
- Hidden a/b/c: same three checks against generator ground truth.
- Reference: `tests/reference.py`, independent stdlib implementation of §6; also checked equal to generator truth.
- Binary reward.

## 22. Answer-key leakage audit

| Artifact | Could it be transcribed or matched? | Mitigation |
|---|---|---|
| `review_decisions.csv` | Pairwise truth on 418 pairs (~2% of BAs) as of review date; not a partition, not per month | biased to name-similar pairs; overrides alone fail; hidden fixtures have different samples |
| launch notebook | reports v2 as 0.97/0.94 — a *wrong* key | intentionally non-discriminating |
| board pack Q2 (v1) | published history, wrong (CRM stale) | matching it fails; Talon footnote is one precedent, not a rule |
| methodology doc | defines customer group (operating group of contracting entity at period end), sponsors, M&A-not-churn | no identity algorithm, no mention of domains/tax ids/SSO/ownership changes/deal register |
| billing dictionary | masking format, ownership change semantics | describes fields; does not say to replay changes for reporting |
| SSO help article | product fact (DNS TXT) | does not mention c360 or customers |
| partner programme | partners can be contacts/admins | does not mention matching |
| OrgGraph guide | snapshot, announced deals, relationship types | vendor language; no instruction to discount |
| code | no tax-id loader, no deal register reader, no per-month map, no unused helper, no comments naming the fix | reviewed in build |
| CHANGELOG | "2.0.0: graph-based resolver improves coverage of self-serve accounts" | neutral |
| Slack export | RevOps chatter on Halvard, one "why is Brightlane so big?" message with no answer | symptom, not rule |

**Cheap-solve audit.**
- *One grep*: `grep -ri reseller` finds the partner doc and directory → leads to list blocking (fails).
- *One doc*: methodology gives definitions, not keys; not sufficient.
- *One SQL*: `GROUP BY tax_id` yields the current-owner static map — fails transfers, masked, missing, hierarchy.
- *One filter*: drop partner or free-mail domains — fails.
- *Helper*: none.
- *Old report*: v1 is wrong; reverting fails.
- *Restoring behaviour*: v1 code is not in the repo; CRM hierarchy grouping fails.
- *Remaining risk*: an agent that immediately adopts "tax id is the identity" is 30–40% of the way; the rest is
  per-month state, masked/missing handling, hierarchy and churn — five independent surfaces.

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| Is a reseller-billed account the reseller's or the end client's? | Contracting party per tax id / ownership; partner doc says order form names contracting party; visible has both cases |
| Tax-id-less BA with a company-domain contact but no SSO: shadow-IT account of that company? | Generator never creates this case (only free-mail, partner or unregistered-domain contacts); documented constraint. Risk: an agent may argue for domain fallback — equivalent on all fixtures because the case is absent |
| Month-end vs month-start state | methodology "at period end"; boundary deal visible |
| `close_date` vs `sign_date` | register dictionary: "close_date: legal completion"; methodology "part of a group"; visible has 3 split deals |
| Sponsors | methodology states; OrgGraph relationship type visible |
| Unresolved masked tax id | singleton; generator ensures one BA per unregistered masked entity |
| Churn when a group divests a sub | group ARR > 0 → not churn; Talon visible |
| Churn when a customer is acquired *by a non-customer* | not churn (still has ARR under new group id). Definition based on top entity of quarter-start customer: generator includes one visible case |
| Customer id change of a group when its top entity is itself acquired | churn exception covers "top entity became part of another group through a closed acquisition"; the visible Ferrow → Oakline → Pellam chain exercises it, so hidden_b's chain adds no new rule |
| Workspaces linked to multiple BAs | generator: SSO-verified workspaces link to one BA |
| TSA domain sharing | irrelevant to correct rule; exists to break domain variants |
| ARR definition, rounding | 12 × MRR in cents; unchanged from existing code |

## 24. Expected trajectory length

50–80 actions, 15–30 minutes. Six discoveries are spread over four source families (billing, product, vendor, CorpDev),
each needing data inspection rather than a single doc; validation needs custom audits. The rebuild touches five
modules.

## 25. Why harder than Tasks 03/05/06

| Task 06 failure | G17 |
|---|---|
| target cutoff already implemented | no per-month state, no tax-id reader, no hierarchy dating in code |
| adjustment summary implemented | churn exception absent |
| natural group/merge design correct | natural "fix domains" and "group by tax id" are wrong |
| attractor optional | OrgGraph parents, partner directory and steward notebook sit on the resolver path |
| traps on unchosen paths | traps sit on the two most natural repairs (blocklist; fuzzy/tax-id static) |
| one-customer check enough | Halvard/Kestrel checks pass for retroactive variant; errors distributed across 7 domains, 38 trials, 64 transfers |

## 26. Comparison with Task 02

Same core hardness shape: state keyed per (entity, time), not per entity. Task 02 agents collapsed per-example state to
per-entity; here the static `ba_id → customer_id` map is the equivalent collapse. G17 adds an epistemic layer Task 02
lacked — conflicting identity keys with a biased validation sample — and a downstream metric whose definition must be
extended. It is less statistical than Task 02 (no model), and its partition grading is stricter than an AUC band.

## 27. Benchmark risks

- **Implementation cost: high.** Coherent names, domains, tax ids, OrgGraph snapshot, register and MRR; many generator
  constraints. ~2.5k lines of generator.
- **Overlap with Task 01**: identity reconciliation again. Differentiation: Task 01 had one authoritative owner
  column and a register-described lineage; G17 has no authoritative customer key, conflicting weak keys, and a time
  dimension on both ownership and hierarchy. Still a moderate overlap reviewers will flag.
- **Underspecification**: shadow-IT accounts and the "tax id is truth" premise are policy choices; the generator
  constraints remove the contested cases, which reduces realism slightly.
- **Headroom risk**: frontier agents know "domains are bad keys"; if they go straight to tax id and read the
  dictionary, the remaining difficulty is per-month state plus hierarchy dating — Task 02 evidence suggests that is
  where they fail, but it is not proven for this domain.
- **Gradability**: exact partition is strict; any missed generator constraint yields a rejected defensible solution.
  Mitigation: two independent alt implementations in the mutation suite, and a fresh-context review for contested cases.
- **Realism**: tax ids for 70% plus masked tax ids is plausible for EU/UK-heavy B2B billing; US-heavy companies would
  use EIN less consistently — fixed by making Corvane EU/UK-headquartered.
