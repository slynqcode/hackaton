# Episode ep-8d38a1b75293 (evaluator-only)

Period 2026-08-01T00:00:00+08:00 .. 2026-10-01T00:00:00+08:00 (end exclusive), company timezone UTC+08:00, base EUR, currencies EUR, JPY, GBP. Records: {'ledger_rows': 325, 'invoices': 86, 'payments': 57, 'documents': 143, 'fx_rates': 708}.

## 5 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | F-98994, P-27066 | 39305.00 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate of the invoice date) | P-05767 | 373.27 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | fx_error (two digits of the rate swapped when keyed in) | P-91880 | 10729944 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | F-52831 | 7740.00 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 5 | period_cutoff | P-84141 | 13448.45 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_2bb9723548["#1 payment_allocation<br/>39305.00 EUR"]
  nF_98994(["F-98994"]) --> nISS_2bb9723548
  nP_27066(["P-27066"]) --> nISS_2bb9723548
  nISS_2bb9723548 -.changed.-> nISS_2bb9723548ledger_add["ledger:add"]
  nISS_2bb9723548 -.changed.-> nISS_2bb9723548ledger_credit_minor["ledger:credit_minor"]
  nISS_2bb9723548 -.changed.-> nISS_2bb9723548payments_invoice_refs["payments:invoice_refs"]
  nISS_b5d6c3cea2["#2 fx_error<br/>373.27 EUR"]
  nP_05767(["P-05767"]) --> nISS_b5d6c3cea2
  nISS_b5d6c3cea2 -.changed.-> nISS_b5d6c3cea2ledger_credit_minor["ledger:credit_minor"]
  nISS_b5d6c3cea2 -.changed.-> nISS_b5d6c3cea2ledger_debit_minor["ledger:debit_minor"]
  nISS_a17692aa70["#3 fx_error<br/>10729944 JPY"]
  nP_91880(["P-91880"]) --> nISS_a17692aa70
  nISS_a17692aa70 -.changed.-> nISS_a17692aa70ledger_credit_minor["ledger:credit_minor"]
  nISS_a17692aa70 -.changed.-> nISS_a17692aa70ledger_debit_minor["ledger:debit_minor"]
  nISS_332f37edbc["#4 period_cutoff<br/>7740.00 EUR"]
  nF_52831(["F-52831"]) --> nISS_332f37edbc
  nISS_332f37edbc -.changed.-> nISS_332f37edbcledger_timestamp["ledger:timestamp"]
  nISS_cc966a8715["#5 period_cutoff<br/>13448.45 GBP"]
  nP_84141(["P-84141"]) --> nISS_cc966a8715
  nISS_cc966a8715 -.changed.-> nISS_cc966a8715ledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
