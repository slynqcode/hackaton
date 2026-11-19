# Episode ep-310c5b5d46ce (evaluator-only)

Period 2026-06-01T00:00:00+02:00 .. 2026-09-01T00:00:00+02:00 (end exclusive), company timezone UTC+02:00, base JPY, currencies JPY, KZT, GBP. Records: {'ledger_rows': 325, 'invoices': 87, 'payments': 59, 'documents': 146, 'fx_rates': 894}.

## 8 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | F-34948, F-52266 | 47100.00 GBP | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | duplicate_invoice | F-67173, F-91909 | 1508320 JPY | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 3 | payment_allocation (partial allocation) | F-87681, P-43466 | 3795129 JPY | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 4 | payment_allocation (missing allocation) | F-10920, P-22171 | 68430.00 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (rate of the previous day) | P-69773 | 460580.21 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | fx_error (two digits of the rate swapped when keyed in) | P-89549 | 494319.60 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 7 | period_cutoff | F-68761 | 1258080 JPY | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 8 | period_cutoff | P-15311 | 14322.04 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_3d17eaf183["#1 duplicate_invoice<br/>47100.00 GBP"]
  nF_34948(["F-34948"]) --> nISS_3d17eaf183
  nF_52266(["F-52266"]) --> nISS_3d17eaf183
  nISS_3d17eaf183 -.changed.-> nISS_3d17eaf183invoices_add["invoices:add"]
  nISS_3d17eaf183 -.changed.-> nISS_3d17eaf183ledger_add["ledger:add"]
  nISS_bb698a902e["#2 duplicate_invoice<br/>1508320 JPY"]
  nF_67173(["F-67173"]) --> nISS_bb698a902e
  nF_91909(["F-91909"]) --> nISS_bb698a902e
  nISS_bb698a902e -.changed.-> nISS_bb698a902einvoices_add["invoices:add"]
  nISS_bb698a902e -.changed.-> nISS_bb698a902eledger_add["ledger:add"]
  nISS_cddbbd6d8d["#3 payment_allocation<br/>3795129 JPY"]
  nF_87681(["F-87681"]) --> nISS_cddbbd6d8d
  nP_43466(["P-43466"]) --> nISS_cddbbd6d8d
  nISS_cddbbd6d8d -.changed.-> nISS_cddbbd6d8dledger_add["ledger:add"]
  nISS_cddbbd6d8d -.changed.-> nISS_cddbbd6d8dledger_credit_minor["ledger:credit_minor"]
  nISS_cddbbd6d8d -.changed.-> nISS_cddbbd6d8dpayments_invoice_refs["payments:invoice_refs"]
  nISS_c533528bcf["#4 payment_allocation<br/>68430.00 GBP"]
  nF_10920(["F-10920"]) --> nISS_c533528bcf
  nP_22171(["P-22171"]) --> nISS_c533528bcf
  nISS_c533528bcf -.changed.-> nISS_c533528bcfledger_add["ledger:add"]
  nISS_c533528bcf -.changed.-> nISS_c533528bcfledger_remove["ledger:remove"]
  nISS_c533528bcf -.changed.-> nISS_c533528bcfpayments_invoice_refs["payments:invoice_refs"]
  nISS_9758d0cbb2["#5 fx_error<br/>460580.21 KZT"]
  nP_69773(["P-69773"]) --> nISS_9758d0cbb2
  nISS_9758d0cbb2 -.changed.-> nISS_9758d0cbb2ledger_credit_minor["ledger:credit_minor"]
  nISS_9758d0cbb2 -.changed.-> nISS_9758d0cbb2ledger_debit_minor["ledger:debit_minor"]
  nISS_fdf179a8a8["#6 fx_error<br/>494319.60 KZT"]
  nP_89549(["P-89549"]) --> nISS_fdf179a8a8
  nISS_fdf179a8a8 -.changed.-> nISS_fdf179a8a8ledger_credit_minor["ledger:credit_minor"]
  nISS_fdf179a8a8 -.changed.-> nISS_fdf179a8a8ledger_debit_minor["ledger:debit_minor"]
  nISS_cddd1a52e3["#7 period_cutoff<br/>1258080 JPY"]
  nF_68761(["F-68761"]) --> nISS_cddd1a52e3
  nISS_cddd1a52e3 -.changed.-> nISS_cddd1a52e3ledger_timestamp["ledger:timestamp"]
  nISS_8fcdc091ef["#8 period_cutoff<br/>14322.04 GBP"]
  nP_15311(["P-15311"]) --> nISS_8fcdc091ef
  nISS_8fcdc091ef -.changed.-> nISS_8fcdc091efledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
