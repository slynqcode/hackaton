# Episode ep-e7cc0f532a88 (evaluator-only)

Period 2026-04-01T00:00:00-05:00 .. 2026-05-01T00:00:00-05:00 (end exclusive), company timezone UTC-05:00, base JPY, currencies JPY, USD, EUR. Records: {'ledger_rows': 314, 'invoices': 89, 'payments': 51, 'documents': 140, 'fx_rates': 522}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | INV-67824, PAY-52892 | 15360.37 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate taken for the UTC date instead of the local date) | PAY-52892 | 10682 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | duplicate_invoice | INV-63748, INV-69221 | 388410 JPY | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 4 | payment_allocation (partial allocation) | INV-30544, PAY-24368 | 1978.00 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (rate of the invoice date) | PAY-59609 | 12779 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | period_cutoff | PAY-77965 | 16362.54 USD | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_f569036de3["#1 payment_allocation<br/>15360.37 USD"]
  nINV_67824(["INV-67824"]) --> nISS_f569036de3
  nPAY_52892(["PAY-52892"]) --> nISS_f569036de3
  nISS_f569036de3 -.changed.-> nISS_f569036de3ledger_add["ledger:add"]
  nISS_f569036de3 -.changed.-> nISS_f569036de3ledger_credit_minor["ledger:credit_minor"]
  nISS_f569036de3 -.changed.-> nISS_f569036de3ledger_debit_minor["ledger:debit_minor"]
  nISS_2ee96c76f1["#2 fx_error<br/>10682 JPY"]
  nPAY_52892(["PAY-52892"]) --> nISS_2ee96c76f1
  nISS_2ee96c76f1 -.changed.-> nISS_2ee96c76f1ledger_add["ledger:add"]
  nISS_2ee96c76f1 -.changed.-> nISS_2ee96c76f1ledger_credit_minor["ledger:credit_minor"]
  nISS_2ee96c76f1 -.changed.-> nISS_2ee96c76f1ledger_debit_minor["ledger:debit_minor"]
  nISS_9d63145c58["#3 duplicate_invoice<br/>388410 JPY"]
  nINV_63748(["INV-63748"]) --> nISS_9d63145c58
  nINV_69221(["INV-69221"]) --> nISS_9d63145c58
  nISS_9d63145c58 -.changed.-> nISS_9d63145c58invoices_add["invoices:add"]
  nISS_9d63145c58 -.changed.-> nISS_9d63145c58ledger_add["ledger:add"]
  nISS_025c3598b2["#4 payment_allocation<br/>1978.00 USD"]
  nINV_30544(["INV-30544"]) --> nISS_025c3598b2
  nPAY_24368(["PAY-24368"]) --> nISS_025c3598b2
  nISS_025c3598b2 -.changed.-> nISS_025c3598b2ledger_add["ledger:add"]
  nISS_025c3598b2 -.changed.-> nISS_025c3598b2ledger_credit_minor["ledger:credit_minor"]
  nISS_025c3598b2 -.changed.-> nISS_025c3598b2payments_invoice_refs["payments:invoice_refs"]
  nISS_57a02ca56e["#5 fx_error<br/>12779 JPY"]
  nPAY_59609(["PAY-59609"]) --> nISS_57a02ca56e
  nISS_57a02ca56e -.changed.-> nISS_57a02ca56eledger_credit_minor["ledger:credit_minor"]
  nISS_57a02ca56e -.changed.-> nISS_57a02ca56eledger_debit_minor["ledger:debit_minor"]
  nISS_d164108865["#6 period_cutoff<br/>16362.54 USD"]
  nPAY_77965(["PAY-77965"]) --> nISS_d164108865
  nISS_d164108865 -.changed.-> nISS_d164108865ledger_timestamp["ledger:timestamp"]
  nISS_f569036de3 ==>|"partial_fx: causes"| nISS_2ee96c76f1
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
