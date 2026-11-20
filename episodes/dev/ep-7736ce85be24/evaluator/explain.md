# Episode ep-7736ce85be24 (evaluator-only)

Period 2026-09-01T00:00:00+00:00 .. 2026-11-01T00:00:00+00:00 (end exclusive), company timezone UTC+00:00, base EUR, currencies EUR, GBP, KZT. Records: {'ledger_rows': 320, 'invoices': 83, 'payments': 58, 'documents': 141, 'fx_rates': 708}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | SI/031938, SI/086877 | 29490.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (missing allocation) | RCP/050374, SI/045402 | 16197.43 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (two digits of the rate swapped when keyed in) | RCP/005941 | 1190.75 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | SI/015864 | 60400.00 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_cbff12a548["#1 duplicate_invoice<br/>29490.00 EUR"]
  nSI_031938(["SI/031938"]) --> nISS_cbff12a548
  nSI_086877(["SI/086877"]) --> nISS_cbff12a548
  nISS_cbff12a548 -.changed.-> nISS_cbff12a548invoices_add["invoices:add"]
  nISS_cbff12a548 -.changed.-> nISS_cbff12a548ledger_add["ledger:add"]
  nISS_1a5e3fe2d2["#2 payment_allocation<br/>16197.43 GBP"]
  nRCP_050374(["RCP/050374"]) --> nISS_1a5e3fe2d2
  nSI_045402(["SI/045402"]) --> nISS_1a5e3fe2d2
  nISS_1a5e3fe2d2 -.changed.-> nISS_1a5e3fe2d2ledger_add["ledger:add"]
  nISS_1a5e3fe2d2 -.changed.-> nISS_1a5e3fe2d2ledger_remove["ledger:remove"]
  nISS_1a5e3fe2d2 -.changed.-> nISS_1a5e3fe2d2payments_invoice_refs["payments:invoice_refs"]
  nISS_12f567db1c["#3 fx_error<br/>1190.75 EUR"]
  nRCP_005941(["RCP/005941"]) --> nISS_12f567db1c
  nISS_12f567db1c -.changed.-> nISS_12f567db1cledger_credit_minor["ledger:credit_minor"]
  nISS_12f567db1c -.changed.-> nISS_12f567db1cledger_debit_minor["ledger:debit_minor"]
  nISS_5883e02846["#4 period_cutoff<br/>60400.00 EUR"]
  nSI_015864(["SI/015864"]) --> nISS_5883e02846
  nISS_5883e02846 -.changed.-> nISS_5883e02846ledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
