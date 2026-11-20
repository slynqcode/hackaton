# Episode ep-9bfddc513e24 (evaluator-only)

Period 2026-07-01T00:00:00+02:00 .. 2026-08-01T00:00:00+02:00 (end exclusive), company timezone UTC+02:00, base GBP, currencies GBP, USD, EUR. Records: {'ledger_rows': 346, 'invoices': 86, 'payments': 63, 'documents': 149, 'fx_rates': 528}.

## 8 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | F-22602, F-29154 | 48300.00 GBP | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | duplicate_invoice | F-18243, F-53032 | 6840.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 3 | payment_allocation (partial allocation) | F-53363, P-68773 | 5597.70 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 4 | payment_allocation (partial allocation) | F-74330, P-56976 | 15714.26 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (rate of the invoice date) | P-73543 | 773.89 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | fx_error (two digits of the rate swapped when keyed in) | P-58584 | 4461.43 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 7 | period_cutoff | F-89553 | 26360.00 USD | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 8 | period_cutoff | P-91684 | 4720.72 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_28b289ce64["#1 duplicate_invoice<br/>48300.00 GBP"]
  nF_22602(["F-22602"]) --> nISS_28b289ce64
  nF_29154(["F-29154"]) --> nISS_28b289ce64
  nISS_28b289ce64 -.changed.-> nISS_28b289ce64invoices_add["invoices:add"]
  nISS_28b289ce64 -.changed.-> nISS_28b289ce64ledger_add["ledger:add"]
  nISS_c97cc0f44f["#2 duplicate_invoice<br/>6840.00 USD"]
  nF_18243(["F-18243"]) --> nISS_c97cc0f44f
  nF_53032(["F-53032"]) --> nISS_c97cc0f44f
  nISS_c97cc0f44f -.changed.-> nISS_c97cc0f44finvoices_add["invoices:add"]
  nISS_c97cc0f44f -.changed.-> nISS_c97cc0f44fledger_add["ledger:add"]
  nISS_31d9c6af8d["#3 payment_allocation<br/>5597.70 GBP"]
  nF_53363(["F-53363"]) --> nISS_31d9c6af8d
  nP_68773(["P-68773"]) --> nISS_31d9c6af8d
  nISS_31d9c6af8d -.changed.-> nISS_31d9c6af8dledger_add["ledger:add"]
  nISS_31d9c6af8d -.changed.-> nISS_31d9c6af8dledger_credit_minor["ledger:credit_minor"]
  nISS_31d9c6af8d -.changed.-> nISS_31d9c6af8dpayments_invoice_refs["payments:invoice_refs"]
  nISS_6162916ee1["#4 payment_allocation<br/>15714.26 GBP"]
  nF_74330(["F-74330"]) --> nISS_6162916ee1
  nP_56976(["P-56976"]) --> nISS_6162916ee1
  nISS_6162916ee1 -.changed.-> nISS_6162916ee1ledger_add["ledger:add"]
  nISS_6162916ee1 -.changed.-> nISS_6162916ee1ledger_credit_minor["ledger:credit_minor"]
  nISS_6162916ee1 -.changed.-> nISS_6162916ee1ledger_debit_minor["ledger:debit_minor"]
  nISS_f26dc548c4["#5 fx_error<br/>773.89 EUR"]
  nP_73543(["P-73543"]) --> nISS_f26dc548c4
  nISS_f26dc548c4 -.changed.-> nISS_f26dc548c4ledger_credit_minor["ledger:credit_minor"]
  nISS_f26dc548c4 -.changed.-> nISS_f26dc548c4ledger_debit_minor["ledger:debit_minor"]
  nISS_3c81413265["#6 fx_error<br/>4461.43 EUR"]
  nP_58584(["P-58584"]) --> nISS_3c81413265
  nISS_3c81413265 -.changed.-> nISS_3c81413265ledger_credit_minor["ledger:credit_minor"]
  nISS_3c81413265 -.changed.-> nISS_3c81413265ledger_debit_minor["ledger:debit_minor"]
  nISS_4e0b9d30f4["#7 period_cutoff<br/>26360.00 USD"]
  nF_89553(["F-89553"]) --> nISS_4e0b9d30f4
  nISS_4e0b9d30f4 -.changed.-> nISS_4e0b9d30f4ledger_timestamp["ledger:timestamp"]
  nISS_a5838ce0f7["#8 period_cutoff<br/>4720.72 EUR"]
  nP_91684(["P-91684"]) --> nISS_a5838ce0f7
  nISS_a5838ce0f7 -.changed.-> nISS_a5838ce0f7ledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
