# Episode ep-318c5f5a9458 (evaluator-only)

Period 2026-07-01T00:00:00+02:00 .. 2026-09-01T00:00:00+02:00 (end exclusive), company timezone UTC+02:00, base GBP, currencies GBP, USD, EUR. Records: {'ledger_rows': 325, 'invoices': 82, 'payments': 51, 'documents': 133, 'fx_rates': 714}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | F-33585, F-55827 | 53010.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (partial allocation) | F-91663, P-60064 | 31058.64 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (rate of the previous day) | P-16453 | 601.59 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | F-38965 | 28550.00 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_958c9fd11e["#1 duplicate_invoice<br/>53010.00 USD"]
  nF_33585(["F-33585"]) --> nISS_958c9fd11e
  nF_55827(["F-55827"]) --> nISS_958c9fd11e
  nISS_958c9fd11e -.changed.-> nISS_958c9fd11einvoices_add["invoices:add"]
  nISS_958c9fd11e -.changed.-> nISS_958c9fd11eledger_add["ledger:add"]
  nISS_a3ec4b9427["#2 payment_allocation<br/>31058.64 EUR"]
  nF_91663(["F-91663"]) --> nISS_a3ec4b9427
  nP_60064(["P-60064"]) --> nISS_a3ec4b9427
  nISS_a3ec4b9427 -.changed.-> nISS_a3ec4b9427ledger_add["ledger:add"]
  nISS_a3ec4b9427 -.changed.-> nISS_a3ec4b9427ledger_credit_minor["ledger:credit_minor"]
  nISS_a3ec4b9427 -.changed.-> nISS_a3ec4b9427ledger_debit_minor["ledger:debit_minor"]
  nISS_3aa66409ff["#3 fx_error<br/>601.59 USD"]
  nP_16453(["P-16453"]) --> nISS_3aa66409ff
  nISS_3aa66409ff -.changed.-> nISS_3aa66409ffledger_credit_minor["ledger:credit_minor"]
  nISS_3aa66409ff -.changed.-> nISS_3aa66409ffledger_debit_minor["ledger:debit_minor"]
  nISS_45d0cd480c["#4 period_cutoff<br/>28550.00 GBP"]
  nF_38965(["F-38965"]) --> nISS_45d0cd480c
  nISS_45d0cd480c -.changed.-> nISS_45d0cd480cledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
