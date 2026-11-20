# Episode ep-879e4e329a01 (evaluator-only)

Period 2026-03-01T00:00:00-03:00 .. 2026-05-01T00:00:00-03:00 (end exclusive), company timezone UTC-03:00, base GBP, currencies GBP, KZT, USD. Records: {'ledger_rows': 322, 'invoices': 87, 'payments': 54, 'documents': 141, 'fx_rates': 708}.

## 8 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | INV-65437, INV-69070 | 31315.00 GBP | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | duplicate_invoice | INV-18448, INV-19080 | 38585.00 GBP | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 3 | payment_allocation (partial allocation) | INV-35262, PAY-90846 | 13861.10 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 4 | payment_allocation (partial allocation) | INV-31968, PAY-26669 | 7286.20 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (two digits of the rate swapped when keyed in) | PAY-81493 | 104923.32 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | fx_error (rate of the invoice date) | PAY-31550 | 3040.87 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 7 | period_cutoff | INV-74114 | 27405.00 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 8 | period_cutoff | PAY-83363 | 59115.00 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_1ececbf22c["#1 duplicate_invoice<br/>31315.00 GBP"]
  nINV_65437(["INV-65437"]) --> nISS_1ececbf22c
  nINV_69070(["INV-69070"]) --> nISS_1ececbf22c
  nISS_1ececbf22c -.changed.-> nISS_1ececbf22cinvoices_add["invoices:add"]
  nISS_1ececbf22c -.changed.-> nISS_1ececbf22cledger_add["ledger:add"]
  nISS_d000265a2c["#2 duplicate_invoice<br/>38585.00 GBP"]
  nINV_18448(["INV-18448"]) --> nISS_d000265a2c
  nINV_19080(["INV-19080"]) --> nISS_d000265a2c
  nISS_d000265a2c -.changed.-> nISS_d000265a2cinvoices_add["invoices:add"]
  nISS_d000265a2c -.changed.-> nISS_d000265a2cledger_add["ledger:add"]
  nISS_f137bf9309["#3 payment_allocation<br/>13861.10 USD"]
  nINV_35262(["INV-35262"]) --> nISS_f137bf9309
  nPAY_90846(["PAY-90846"]) --> nISS_f137bf9309
  nISS_f137bf9309 -.changed.-> nISS_f137bf9309ledger_add["ledger:add"]
  nISS_f137bf9309 -.changed.-> nISS_f137bf9309ledger_credit_minor["ledger:credit_minor"]
  nISS_f137bf9309 -.changed.-> nISS_f137bf9309payments_invoice_refs["payments:invoice_refs"]
  nISS_47426d7f80["#4 payment_allocation<br/>7286.20 GBP"]
  nINV_31968(["INV-31968"]) --> nISS_47426d7f80
  nPAY_26669(["PAY-26669"]) --> nISS_47426d7f80
  nISS_47426d7f80 -.changed.-> nISS_47426d7f80ledger_add["ledger:add"]
  nISS_47426d7f80 -.changed.-> nISS_47426d7f80ledger_credit_minor["ledger:credit_minor"]
  nISS_47426d7f80 -.changed.-> nISS_47426d7f80payments_invoice_refs["payments:invoice_refs"]
  nISS_a235d24726["#5 fx_error<br/>104923.32 GBP"]
  nPAY_81493(["PAY-81493"]) --> nISS_a235d24726
  nISS_a235d24726 -.changed.-> nISS_a235d24726ledger_credit_minor["ledger:credit_minor"]
  nISS_a235d24726 -.changed.-> nISS_a235d24726ledger_debit_minor["ledger:debit_minor"]
  nISS_7b20bc6869["#6 fx_error<br/>3040.87 GBP"]
  nPAY_31550(["PAY-31550"]) --> nISS_7b20bc6869
  nISS_7b20bc6869 -.changed.-> nISS_7b20bc6869ledger_credit_minor["ledger:credit_minor"]
  nISS_7b20bc6869 -.changed.-> nISS_7b20bc6869ledger_debit_minor["ledger:debit_minor"]
  nISS_1b050282f2["#7 period_cutoff<br/>27405.00 GBP"]
  nINV_74114(["INV-74114"]) --> nISS_1b050282f2
  nISS_1b050282f2 -.changed.-> nISS_1b050282f2ledger_timestamp["ledger:timestamp"]
  nISS_acbcc312a7["#8 period_cutoff<br/>59115.00 GBP"]
  nPAY_83363(["PAY-83363"]) --> nISS_acbcc312a7
  nISS_acbcc312a7 -.changed.-> nISS_acbcc312a7ledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
