# Episode ep-2aa0aede9dd5 (evaluator-only)

Period 2026-03-01T00:00:00-07:00 .. 2026-04-01T00:00:00-07:00 (end exclusive), company timezone UTC-07:00, base KZT, currencies KZT, GBP, EUR. Records: {'ledger_rows': 309, 'invoices': 83, 'payments': 52, 'documents': 135, 'fx_rates': 528}.

## 8 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | INV-60477, INV-97194 | 11814560.00 KZT | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | duplicate_invoice | INV-05527, INV-50757 | 9110.00 GBP | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 3 | payment_allocation (partial allocation) | INV-81469, PAY-86932 | 4654902.60 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 4 | payment_allocation (missing allocation) | INV-68721, PAY-13731 | 25277.63 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (two digits of the rate swapped when keyed in) | PAY-14088 | 4797885.60 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | fx_error (rate of the previous day) | PAY-83421 | 66850.20 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 7 | period_cutoff | INV-36875 | 19647480.00 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 8 | period_cutoff | PAY-72381 | 21460.39 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_6712cfe53d["#1 duplicate_invoice<br/>11814560.00 KZT"]
  nINV_60477(["INV-60477"]) --> nISS_6712cfe53d
  nINV_97194(["INV-97194"]) --> nISS_6712cfe53d
  nISS_6712cfe53d -.changed.-> nISS_6712cfe53dinvoices_add["invoices:add"]
  nISS_6712cfe53d -.changed.-> nISS_6712cfe53dledger_add["ledger:add"]
  nISS_c9554200be["#2 duplicate_invoice<br/>9110.00 GBP"]
  nINV_05527(["INV-05527"]) --> nISS_c9554200be
  nINV_50757(["INV-50757"]) --> nISS_c9554200be
  nISS_c9554200be -.changed.-> nISS_c9554200beinvoices_add["invoices:add"]
  nISS_c9554200be -.changed.-> nISS_c9554200beledger_add["ledger:add"]
  nISS_2dbdcd789a["#3 payment_allocation<br/>4654902.60 KZT"]
  nINV_81469(["INV-81469"]) --> nISS_2dbdcd789a
  nPAY_86932(["PAY-86932"]) --> nISS_2dbdcd789a
  nISS_2dbdcd789a -.changed.-> nISS_2dbdcd789aledger_add["ledger:add"]
  nISS_2dbdcd789a -.changed.-> nISS_2dbdcd789aledger_credit_minor["ledger:credit_minor"]
  nISS_2dbdcd789a -.changed.-> nISS_2dbdcd789apayments_invoice_refs["payments:invoice_refs"]
  nISS_e63a9e36c7["#4 payment_allocation<br/>25277.63 GBP"]
  nINV_68721(["INV-68721"]) --> nISS_e63a9e36c7
  nPAY_13731(["PAY-13731"]) --> nISS_e63a9e36c7
  nISS_e63a9e36c7 -.changed.-> nISS_e63a9e36c7ledger_add["ledger:add"]
  nISS_e63a9e36c7 -.changed.-> nISS_e63a9e36c7ledger_remove["ledger:remove"]
  nISS_e63a9e36c7 -.changed.-> nISS_e63a9e36c7payments_invoice_refs["payments:invoice_refs"]
  nISS_36ddff5c3e["#5 fx_error<br/>4797885.60 KZT"]
  nPAY_14088(["PAY-14088"]) --> nISS_36ddff5c3e
  nISS_36ddff5c3e -.changed.-> nISS_36ddff5c3eledger_credit_minor["ledger:credit_minor"]
  nISS_36ddff5c3e -.changed.-> nISS_36ddff5c3eledger_debit_minor["ledger:debit_minor"]
  nISS_8109f61b51["#6 fx_error<br/>66850.20 KZT"]
  nPAY_83421(["PAY-83421"]) --> nISS_8109f61b51
  nISS_8109f61b51 -.changed.-> nISS_8109f61b51ledger_credit_minor["ledger:credit_minor"]
  nISS_8109f61b51 -.changed.-> nISS_8109f61b51ledger_debit_minor["ledger:debit_minor"]
  nISS_f3904da280["#7 period_cutoff<br/>19647480.00 KZT"]
  nINV_36875(["INV-36875"]) --> nISS_f3904da280
  nISS_f3904da280 -.changed.-> nISS_f3904da280ledger_timestamp["ledger:timestamp"]
  nISS_b835c776b2["#8 period_cutoff<br/>21460.39 EUR"]
  nPAY_72381(["PAY-72381"]) --> nISS_b835c776b2
  nISS_b835c776b2 -.changed.-> nISS_b835c776b2ledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
