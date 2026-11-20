# Episode ep-cd91c75a7ecc (evaluator-only)

Period 2026-06-01T00:00:00+08:00 .. 2026-08-01T00:00:00+08:00 (end exclusive), company timezone UTC+08:00, base EUR, currencies EUR, USD, JPY. Records: {'ledger_rows': 334, 'invoices': 88, 'payments': 61, 'documents': 149, 'fx_rates': 708}.

## 8 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | F-32748, F-83165 | 6650880 JPY | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | duplicate_invoice | F-27502, F-99297 | 83315.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 3 | payment_allocation (partial allocation) | F-27036, P-64814 | 2628.80 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 4 | payment_allocation (partial allocation) | F-08855, P-01013 | 11261.95 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (two digits of the rate swapped when keyed in) | P-51613 | 303534 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | fx_error (rate of the invoice date) | P-00157 | 124596 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 7 | period_cutoff | F-66184 | 1298940 JPY | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 8 | period_cutoff | F-38409 | 3457660 JPY | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_e6cded30e7["#1 duplicate_invoice<br/>6650880 JPY"]
  nF_32748(["F-32748"]) --> nISS_e6cded30e7
  nF_83165(["F-83165"]) --> nISS_e6cded30e7
  nISS_e6cded30e7 -.changed.-> nISS_e6cded30e7invoices_add["invoices:add"]
  nISS_e6cded30e7 -.changed.-> nISS_e6cded30e7ledger_add["ledger:add"]
  nISS_09b4aab0dd["#2 duplicate_invoice<br/>83315.00 USD"]
  nF_27502(["F-27502"]) --> nISS_09b4aab0dd
  nF_99297(["F-99297"]) --> nISS_09b4aab0dd
  nISS_09b4aab0dd -.changed.-> nISS_09b4aab0ddinvoices_add["invoices:add"]
  nISS_09b4aab0dd -.changed.-> nISS_09b4aab0ddledger_add["ledger:add"]
  nISS_d40bb8b65c["#3 payment_allocation<br/>2628.80 EUR"]
  nF_27036(["F-27036"]) --> nISS_d40bb8b65c
  nP_64814(["P-64814"]) --> nISS_d40bb8b65c
  nISS_d40bb8b65c -.changed.-> nISS_d40bb8b65cledger_add["ledger:add"]
  nISS_d40bb8b65c -.changed.-> nISS_d40bb8b65cledger_credit_minor["ledger:credit_minor"]
  nISS_d40bb8b65c -.changed.-> nISS_d40bb8b65cpayments_invoice_refs["payments:invoice_refs"]
  nISS_98c9130eae["#4 payment_allocation<br/>11261.95 USD"]
  nF_08855(["F-08855"]) --> nISS_98c9130eae
  nP_01013(["P-01013"]) --> nISS_98c9130eae
  nISS_98c9130eae -.changed.-> nISS_98c9130eaeledger_add["ledger:add"]
  nISS_98c9130eae -.changed.-> nISS_98c9130eaeledger_credit_minor["ledger:credit_minor"]
  nISS_98c9130eae -.changed.-> nISS_98c9130eaepayments_invoice_refs["payments:invoice_refs"]
  nISS_61b9bc3c77["#5 fx_error<br/>303534 JPY"]
  nP_51613(["P-51613"]) --> nISS_61b9bc3c77
  nISS_61b9bc3c77 -.changed.-> nISS_61b9bc3c77ledger_credit_minor["ledger:credit_minor"]
  nISS_61b9bc3c77 -.changed.-> nISS_61b9bc3c77ledger_debit_minor["ledger:debit_minor"]
  nISS_750a8033f6["#6 fx_error<br/>124596 JPY"]
  nP_00157(["P-00157"]) --> nISS_750a8033f6
  nISS_750a8033f6 -.changed.-> nISS_750a8033f6ledger_credit_minor["ledger:credit_minor"]
  nISS_750a8033f6 -.changed.-> nISS_750a8033f6ledger_debit_minor["ledger:debit_minor"]
  nISS_515c975ffd["#7 period_cutoff<br/>1298940 JPY"]
  nF_66184(["F-66184"]) --> nISS_515c975ffd
  nISS_515c975ffd -.changed.-> nISS_515c975ffdledger_timestamp["ledger:timestamp"]
  nISS_a160daeb5d["#8 period_cutoff<br/>3457660 JPY"]
  nF_38409(["F-38409"]) --> nISS_a160daeb5d
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
