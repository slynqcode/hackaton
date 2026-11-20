# Episode ep-2043b82c11cc (evaluator-only)

Period 2026-06-01T00:00:00+05:30 .. 2026-07-01T00:00:00+05:30 (end exclusive), company timezone UTC+05:30, base JPY, currencies JPY, GBP, EUR. Records: {'ledger_rows': 293, 'invoices': 82, 'payments': 50, 'documents': 132, 'fx_rates': 522}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | INV-18867, INV-69993 | 3907115 JPY | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (partial allocation) | INV-04401, PAY-19056 | 2664.00 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (two digits of the rate swapped when keyed in) | PAY-57654 | 12668112 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | PAY-04623 | 14602.89 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_b25827fc24["#1 duplicate_invoice<br/>3907115 JPY"]
  nINV_18867(["INV-18867"]) --> nISS_b25827fc24
  nINV_69993(["INV-69993"]) --> nISS_b25827fc24
  nISS_b25827fc24 -.changed.-> nISS_b25827fc24invoices_add["invoices:add"]
  nISS_b25827fc24 -.changed.-> nISS_b25827fc24ledger_add["ledger:add"]
  nISS_1b07494938["#2 payment_allocation<br/>2664.00 GBP"]
  nINV_04401(["INV-04401"]) --> nISS_1b07494938
  nPAY_19056(["PAY-19056"]) --> nISS_1b07494938
  nISS_1b07494938 -.changed.-> nISS_1b07494938ledger_add["ledger:add"]
  nISS_1b07494938 -.changed.-> nISS_1b07494938ledger_credit_minor["ledger:credit_minor"]
  nISS_1b07494938 -.changed.-> nISS_1b07494938payments_invoice_refs["payments:invoice_refs"]
  nISS_4702de3aa2["#3 fx_error<br/>12668112 JPY"]
  nPAY_57654(["PAY-57654"]) --> nISS_4702de3aa2
  nISS_4702de3aa2 -.changed.-> nISS_4702de3aa2ledger_credit_minor["ledger:credit_minor"]
  nISS_4702de3aa2 -.changed.-> nISS_4702de3aa2ledger_debit_minor["ledger:debit_minor"]
  nISS_40e3ab0de9["#4 period_cutoff<br/>14602.89 GBP"]
  nPAY_04623(["PAY-04623"]) --> nISS_40e3ab0de9
  nISS_40e3ab0de9 -.changed.-> nISS_40e3ab0de9ledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
