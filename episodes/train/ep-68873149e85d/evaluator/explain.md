# Episode ep-68873149e85d (evaluator-only)

Period 2026-07-01T00:00:00+00:00 .. 2026-10-01T00:00:00+00:00 (end exclusive), company timezone UTC+00:00, base GBP, currencies GBP, EUR, KZT. Records: {'ledger_rows': 355, 'invoices': 86, 'payments': 68, 'documents': 154, 'fx_rates': 894}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | INV-92050, PAY-41431 | 20321.20 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate of the previous day) | PAY-41431 | 163.21 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | duplicate_invoice | INV-24174, INV-98745 | 14800.00 GBP | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 4 | payment_allocation (missing allocation) | INV-15302, PAY-68246 | 65965.23 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (two digits of the rate swapped when keyed in) | PAY-61836 | 2925.31 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | period_cutoff | INV-37585 | 22613210.00 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_4664a48d31["#1 payment_allocation<br/>20321.20 EUR"]
  nINV_92050(["INV-92050"]) --> nISS_4664a48d31
  nPAY_41431(["PAY-41431"]) --> nISS_4664a48d31
  nISS_4664a48d31 -.changed.-> nISS_4664a48d31ledger_add["ledger:add"]
  nISS_4664a48d31 -.changed.-> nISS_4664a48d31ledger_credit_minor["ledger:credit_minor"]
  nISS_4664a48d31 -.changed.-> nISS_4664a48d31ledger_debit_minor["ledger:debit_minor"]
  nISS_8d40e67781["#2 fx_error<br/>163.21 GBP"]
  nPAY_41431(["PAY-41431"]) --> nISS_8d40e67781
  nISS_8d40e67781 -.changed.-> nISS_8d40e67781ledger_add["ledger:add"]
  nISS_8d40e67781 -.changed.-> nISS_8d40e67781ledger_credit_minor["ledger:credit_minor"]
  nISS_8d40e67781 -.changed.-> nISS_8d40e67781ledger_debit_minor["ledger:debit_minor"]
  nISS_3764af58df["#3 duplicate_invoice<br/>14800.00 GBP"]
  nINV_24174(["INV-24174"]) --> nISS_3764af58df
  nINV_98745(["INV-98745"]) --> nISS_3764af58df
  nISS_3764af58df -.changed.-> nISS_3764af58dfinvoices_add["invoices:add"]
  nISS_3764af58df -.changed.-> nISS_3764af58dfledger_add["ledger:add"]
  nISS_3901d8950b["#4 payment_allocation<br/>65965.23 EUR"]
  nINV_15302(["INV-15302"]) --> nISS_3901d8950b
  nPAY_68246(["PAY-68246"]) --> nISS_3901d8950b
  nISS_3901d8950b -.changed.-> nISS_3901d8950bledger_add["ledger:add"]
  nISS_3901d8950b -.changed.-> nISS_3901d8950bledger_remove["ledger:remove"]
  nISS_3901d8950b -.changed.-> nISS_3901d8950bpayments_invoice_refs["payments:invoice_refs"]
  nISS_f72be7b8cc["#5 fx_error<br/>2925.31 GBP"]
  nPAY_61836(["PAY-61836"]) --> nISS_f72be7b8cc
  nISS_f72be7b8cc -.changed.-> nISS_f72be7b8ccledger_credit_minor["ledger:credit_minor"]
  nISS_f72be7b8cc -.changed.-> nISS_f72be7b8ccledger_debit_minor["ledger:debit_minor"]
  nISS_50ba70a3a8["#6 period_cutoff<br/>22613210.00 KZT"]
  nINV_37585(["INV-37585"]) --> nISS_50ba70a3a8
  nISS_50ba70a3a8 -.changed.-> nISS_50ba70a3a8ledger_timestamp["ledger:timestamp"]
  nISS_4664a48d31 ==>|"partial_fx: causes"| nISS_8d40e67781
```

## Interacting errors

- **partial_fx**: FX conversion applied to the allocated part; wrong rate date taken from the UTC date of the payment.

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
