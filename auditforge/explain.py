"""Human-readable, evaluator-side report of one episode: what was broken, how to see it, where the traps are,
plus a Mermaid causal graph (renders on GitHub). Never shown to the agent."""
from __future__ import annotations

from collections import defaultdict

from .generator import Episode
from .money import fmt_major

HOW = {
    "duplicate_invoice": "Same entity, same po_ref, same line items (in a different order) under a second invoice number.",
    "payment_allocation": "The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED.",
    "fx_error": "Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit.",
    "period_cutoff": "Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows.",
}
VARIANT = {"utc_date": "rate taken for the UTC date instead of the local date", "prev_day": "rate of the previous day",
           "invoice_date": "rate of the invoice date", "posting_date": "rate of the (wrong) posting date",
           "typo": "two digits of the rate swapped when keyed in"}
TRAPS = ["same amounts for the same customer with a different po_ref (legitimate repeat orders)",
         "monthly subscriptions with identical lines", "instalments and multi-invoice payments", "refunds (negative amounts)",
         "advance payments on account: legitimate UNAPPLIED cash, memo names no invoice",
         "documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)",
         "correct cross-currency receipts"]


def _node(x: str) -> str:
    return "n" + "".join(c if c.isalnum() else "_" for c in x)


def explain(ep: Episode) -> str:
    m, prov = ep.manifest, ep.provenance
    faults = {f["issue_id"]: f for f in prov.get("faults", [])}
    issues = ep.truth["issues"]
    L = [f"# Episode {ep.episode_id} (evaluator-only)", "",
         f"Period {m['period_start']} .. {m['period_end']} (end exclusive), company timezone {m['timezone']}, "
         f"base {m['base_currency']}, currencies {', '.join(m['currencies'])}. Records: {m['counts']}.", ""]
    if not issues:
        L += ["**Clean company: no errors.** The right answer is an empty findings list; every accusation is a false positive.", ""]
    else:
        L += [f"## {len(issues)} hidden errors", "", "| # | type | affected | amount | how to see it |", "|---|---|---|---|---|"]
        for n, i in enumerate(issues, 1):
            f = faults.get(i["issue_id"], {})
            extra = ""
            if i["type"] == "fx_error" and f.get("params", {}).get("variant"):
                extra = f" ({VARIANT[f['params']['variant']]})"
            if i["type"] == "payment_allocation" and f.get("params", {}).get("mode"):
                extra = f" ({f['params']['mode']} allocation)"
            L.append(f"| {n} | {i['type']}{extra} | {', '.join(i['affected_ids'])} | "
                     f"{fmt_major(i['expected_amount_minor'], i['currency'])} {i['currency']} | {HOW[i['type']]} |")
        L += ["", "## Causal graph", "", "```mermaid", "flowchart LR"]
        changes = defaultdict(set)
        for ch in prov.get("changes", []):
            for iid in ch.get("issue_ids", []):
                changes[iid].add(f"{ch['table']}:{ch.get('field', ch['op'])}")
        for n, i in enumerate(issues, 1):
            iid = i["issue_id"]
            L.append(f'  {_node(iid)}["#{n} {i["type"]}<br/>{fmt_major(i["expected_amount_minor"], i["currency"])} {i["currency"]}"]')
            for a in i["affected_ids"]:
                L.append(f'  {_node(a)}(["{a}"]) --> {_node(iid)}')
            for c in sorted(changes[iid])[:3]:
                L.append(f'  {_node(iid)} -.changed.-> {_node(iid + c)}["{c}"]')
        for link in prov.get("causal_links", []):
            L.append(f'  {_node(link["cause"])} ==>|"{link["scenario"]}: causes"| {_node(link["effect"])}')
        L += ["```", ""]
        if prov.get("causal_links"):
            L += ["## Interacting errors", ""] + [f"- **{l['scenario']}**: {l['mechanism']}." for l in prov["causal_links"]] + [""]
    L += ["## Legitimate look-alikes in this company (not errors)", ""] + [f"- {t}" for t in TRAPS] + [""]
    return "\n".join(L)
