# Episode ep-c57048155e16 (evaluator-only)

Period 2026-08-01T00:00:00+05:00 .. 2026-11-01T00:00:00+05:00 (end exclusive), company timezone UTC+05:00, base KZT, currencies KZT, USD, EUR. Records: {'ledger_rows': 424, 'invoices': 102, 'payments': 76, 'documents': 178, 'fx_rates': 894}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | F-44150, F-63192 | 62205.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (missing allocation) | F-89491, P-18675 | 15581990.38 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (two digits of the rate swapped when keyed in) | P-16250 | 9796.82 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | F-94081 | 340225.00 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_5541519d49["#1 duplicate_invoice<br/>62205.00 EUR"]
  nF_44150(["F-44150"]) --> nISS_5541519d49
  nF_63192(["F-63192"]) --> nISS_5541519d49
  nISS_5541519d49 -.changed.-> nISS_5541519d49invoices_add["invoices:add"]
  nISS_5541519d49 -.changed.-> nISS_5541519d49ledger_add["ledger:add"]
  nISS_8833a06d96["#2 payment_allocation<br/>15581990.38 KZT"]
  nF_89491(["F-89491"]) --> nISS_8833a06d96
  nP_18675(["P-18675"]) --> nISS_8833a06d96
  nISS_8833a06d96 -.changed.-> nISS_8833a06d96ledger_add["ledger:add"]
  nISS_8833a06d96 -.changed.-> nISS_8833a06d96ledger_remove["ledger:remove"]
  nISS_8833a06d96 -.changed.-> nISS_8833a06d96payments_invoice_refs["payments:invoice_refs"]
  nISS_491ae9eb74["#3 fx_error<br/>9796.82 EUR"]
  nP_16250(["P-16250"]) --> nISS_491ae9eb74
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
