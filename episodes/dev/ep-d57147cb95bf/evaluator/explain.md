# Episode ep-d57147cb95bf (evaluator-only)

Period 2026-09-01T00:00:00+00:00 .. 2026-11-01T00:00:00+00:00 (end exclusive), company timezone UTC+00:00, base EUR, currencies EUR, GBP, KZT. Records: {'ledger_rows': 322, 'invoices': 83, 'payments': 58, 'documents': 141, 'fx_rates': 708}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | SI/002286, SI/044193 | 41195.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (missing allocation) | RCP/034788, SI/093654 | 41200.00 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (two digits of the rate swapped when keyed in) | RCP/067088 | 4635.51 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | SI/015864 | 60400.00 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_cbff12a548["#1 duplicate_invoice<br/>41195.00 EUR"]
  nSI_002286(["SI/002286"]) --> nISS_cbff12a548
  nSI_044193(["SI/044193"]) --> nISS_cbff12a548
  nISS_cbff12a548 -.changed.-> nISS_cbff12a548invoices_add["invoices:add"]
  nISS_cbff12a548 -.changed.-> nISS_cbff12a548ledger_add["ledger:add"]
  nISS_1a5e3fe2d2["#2 payment_allocation<br/>41200.00 EUR"]
  nRCP_034788(["RCP/034788"]) --> nISS_1a5e3fe2d2
  nSI_093654(["SI/093654"]) --> nISS_1a5e3fe2d2
  nISS_1a5e3fe2d2 -.changed.-> nISS_1a5e3fe2d2ledger_add["ledger:add"]
  nISS_1a5e3fe2d2 -.changed.-> nISS_1a5e3fe2d2ledger_remove["ledger:remove"]
  nISS_1a5e3fe2d2 -.changed.-> nISS_1a5e3fe2d2payments_invoice_refs["payments:invoice_refs"]
  nISS_12f567db1c["#3 fx_error<br/>4635.51 EUR"]
  nRCP_067088(["RCP/067088"]) --> nISS_12f567db1c
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
