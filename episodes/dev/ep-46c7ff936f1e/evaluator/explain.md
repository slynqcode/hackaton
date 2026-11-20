# Episode ep-46c7ff936f1e (evaluator-only)

Period 2026-08-01T00:00:00+05:00 .. 2026-11-01T00:00:00+05:00 (end exclusive), company timezone UTC+05:00, base KZT, currencies KZT, USD, EUR. Records: {'ledger_rows': 426, 'invoices': 102, 'payments': 76, 'documents': 178, 'fx_rates': 894}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | F-51399, F-99497 | 30505.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (missing allocation) | F-93996, P-52153 | 36793875.00 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (two digits of the rate swapped when keyed in) | P-10352 | 26192.80 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | F-94081 | 340225.00 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_5541519d49["#1 duplicate_invoice<br/>30505.00 EUR"]
  nF_51399(["F-51399"]) --> nISS_5541519d49
  nF_99497(["F-99497"]) --> nISS_5541519d49
  nISS_5541519d49 -.changed.-> nISS_5541519d49invoices_add["invoices:add"]
  nISS_5541519d49 -.changed.-> nISS_5541519d49ledger_add["ledger:add"]
  nISS_8833a06d96["#2 payment_allocation<br/>36793875.00 KZT"]
  nF_93996(["F-93996"]) --> nISS_8833a06d96
  nP_52153(["P-52153"]) --> nISS_8833a06d96
  nISS_8833a06d96 -.changed.-> nISS_8833a06d96ledger_add["ledger:add"]
  nISS_8833a06d96 -.changed.-> nISS_8833a06d96ledger_remove["ledger:remove"]
  nISS_8833a06d96 -.changed.-> nISS_8833a06d96payments_invoice_refs["payments:invoice_refs"]
  nISS_491ae9eb74["#3 fx_error<br/>26192.80 EUR"]
  nP_10352(["P-10352"]) --> nISS_491ae9eb74
  nISS_491ae9eb74 -.changed.-> nISS_491ae9eb74ledger_credit_minor["ledger:credit_minor"]
  nISS_491ae9eb74 -.changed.-> nISS_491ae9eb74ledger_debit_minor["ledger:debit_minor"]
  nISS_d84fa4c80d["#4 period_cutoff<br/>340225.00 KZT"]
  nF_94081(["F-94081"]) --> nISS_d84fa4c80d
  nISS_d84fa4c80d -.changed.-> nISS_d84fa4c80dledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
