# Episode ep-f5dd33f3372c (evaluator-only)

Period 2026-07-01T00:00:00+02:00 .. 2026-09-01T00:00:00+02:00 (end exclusive), company timezone UTC+02:00, base GBP, currencies GBP, USD, EUR. Records: {'ledger_rows': 325, 'invoices': 82, 'payments': 51, 'documents': 133, 'fx_rates': 714}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | F-80740, F-89325 | 13935.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (partial allocation) | F-79685, P-41182 | 32074.58 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (rate of the invoice date) | P-01292 | 1035.77 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | F-06044 | 7210.00 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_958c9fd11e["#1 duplicate_invoice<br/>13935.00 USD"]
  nF_80740(["F-80740"]) --> nISS_958c9fd11e
  nF_89325(["F-89325"]) --> nISS_958c9fd11e
  nISS_958c9fd11e -.changed.-> nISS_958c9fd11einvoices_add["invoices:add"]
  nISS_958c9fd11e -.changed.-> nISS_958c9fd11eledger_add["ledger:add"]
  nISS_a3ec4b9427["#2 payment_allocation<br/>32074.58 GBP"]
  nF_79685(["F-79685"]) --> nISS_a3ec4b9427
  nP_41182(["P-41182"]) --> nISS_a3ec4b9427
  nISS_a3ec4b9427 -.changed.-> nISS_a3ec4b9427ledger_add["ledger:add"]
  nISS_a3ec4b9427 -.changed.-> nISS_a3ec4b9427ledger_credit_minor["ledger:credit_minor"]
  nISS_a3ec4b9427 -.changed.-> nISS_a3ec4b9427ledger_debit_minor["ledger:debit_minor"]
  nISS_3aa66409ff["#3 fx_error<br/>1035.77 EUR"]
  nP_01292(["P-01292"]) --> nISS_3aa66409ff
  nISS_3aa66409ff -.changed.-> nISS_3aa66409ffledger_credit_minor["ledger:credit_minor"]
  nISS_3aa66409ff -.changed.-> nISS_3aa66409ffledger_debit_minor["ledger:debit_minor"]
  nISS_45d0cd480c["#4 period_cutoff<br/>7210.00 GBP"]
  nF_06044(["F-06044"]) --> nISS_45d0cd480c
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
