# Episode ep-8a45a0fc10d2 (evaluator-only)

Period 2026-06-01T00:00:00+08:00 .. 2026-08-01T00:00:00+08:00 (end exclusive), company timezone UTC+08:00, base EUR, currencies EUR, USD, JPY. Records: {'ledger_rows': 334, 'invoices': 88, 'payments': 61, 'documents': 149, 'fx_rates': 708}.

## 8 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | F-08855, F-65393 | 48965.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | duplicate_invoice | F-32345, F-60333 | 4958970 JPY | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 3 | payment_allocation (partial allocation) | F-92568, P-82301 | 744.00 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 4 | payment_allocation (partial allocation) | F-80456, P-72887 | 8826.25 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (two digits of the rate swapped when keyed in) | P-51613 | 303534 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | fx_error (rate of the previous day) | P-45888 | 23261 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 7 | period_cutoff | F-86432 | 39685.00 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 8 | period_cutoff | F-66184 | 1298940 JPY | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_e6cded30e7["#1 duplicate_invoice<br/>48965.00 USD"]
  nF_08855(["F-08855"]) --> nISS_e6cded30e7
  nF_65393(["F-65393"]) --> nISS_e6cded30e7
  nISS_e6cded30e7 -.changed.-> nISS_e6cded30e7invoices_add["invoices:add"]
  nISS_e6cded30e7 -.changed.-> nISS_e6cded30e7ledger_add["ledger:add"]
  nISS_09b4aab0dd["#2 duplicate_invoice<br/>4958970 JPY"]
  nF_32345(["F-32345"]) --> nISS_09b4aab0dd
  nF_60333(["F-60333"]) --> nISS_09b4aab0dd
  nISS_09b4aab0dd -.changed.-> nISS_09b4aab0ddinvoices_add["invoices:add"]
  nISS_09b4aab0dd -.changed.-> nISS_09b4aab0ddledger_add["ledger:add"]
  nISS_d40bb8b65c["#3 payment_allocation<br/>744.00 EUR"]
  nF_92568(["F-92568"]) --> nISS_d40bb8b65c
  nP_82301(["P-82301"]) --> nISS_d40bb8b65c
  nISS_d40bb8b65c -.changed.-> nISS_d40bb8b65cledger_add["ledger:add"]
  nISS_d40bb8b65c -.changed.-> nISS_d40bb8b65cledger_credit_minor["ledger:credit_minor"]
  nISS_d40bb8b65c -.changed.-> nISS_d40bb8b65cpayments_invoice_refs["payments:invoice_refs"]
  nISS_98c9130eae["#4 payment_allocation<br/>8826.25 EUR"]
  nF_80456(["F-80456"]) --> nISS_98c9130eae
  nP_72887(["P-72887"]) --> nISS_98c9130eae
  nISS_98c9130eae -.changed.-> nISS_98c9130eaeledger_add["ledger:add"]
  nISS_98c9130eae -.changed.-> nISS_98c9130eaeledger_credit_minor["ledger:credit_minor"]
  nISS_98c9130eae -.changed.-> nISS_98c9130eaepayments_invoice_refs["payments:invoice_refs"]
  nISS_61b9bc3c77["#5 fx_error<br/>303534 JPY"]
  nP_51613(["P-51613"]) --> nISS_61b9bc3c77
  nISS_61b9bc3c77 -.changed.-> nISS_61b9bc3c77ledger_credit_minor["ledger:credit_minor"]
  nISS_61b9bc3c77 -.changed.-> nISS_61b9bc3c77ledger_debit_minor["ledger:debit_minor"]
  nISS_750a8033f6["#6 fx_error<br/>23261 JPY"]
  nP_45888(["P-45888"]) --> nISS_750a8033f6
  nISS_750a8033f6 -.changed.-> nISS_750a8033f6ledger_credit_minor["ledger:credit_minor"]
  nISS_750a8033f6 -.changed.-> nISS_750a8033f6ledger_debit_minor["ledger:debit_minor"]
  nISS_515c975ffd["#7 period_cutoff<br/>39685.00 EUR"]
  nF_86432(["F-86432"]) --> nISS_515c975ffd
  nISS_515c975ffd -.changed.-> nISS_515c975ffdledger_timestamp["ledger:timestamp"]
  nISS_a160daeb5d["#8 period_cutoff<br/>1298940 JPY"]
  nF_66184(["F-66184"]) --> nISS_a160daeb5d
  nISS_a160daeb5d -.changed.-> nISS_a160daeb5dledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
