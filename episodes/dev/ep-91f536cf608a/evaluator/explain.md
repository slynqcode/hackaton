# Episode ep-91f536cf608a (evaluator-only)

Period 2026-01-01T00:00:00+09:00 .. 2026-02-01T00:00:00+09:00 (end exclusive), company timezone UTC+09:00, base USD, currencies USD, KZT, GBP. Records: {'ledger_rows': 298, 'invoices': 82, 'payments': 50, 'documents': 132, 'fx_rates': 528}.

## 5 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (missing allocation) | RCP/087759, SI/032715 | 61090.00 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate of the previous day) | RCP/095716 | 354723.50 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | fx_error (rate of the previous day) | RCP/011546 | 18483.63 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | SI/062351 | 23282620.00 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 5 | period_cutoff | SI/078889 | 23165.00 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_68f9d750ab["#1 payment_allocation<br/>61090.00 USD"]
  nRCP_087759(["RCP/087759"]) --> nISS_68f9d750ab
  nSI_032715(["SI/032715"]) --> nISS_68f9d750ab
  nISS_68f9d750ab -.changed.-> nISS_68f9d750abledger_add["ledger:add"]
  nISS_68f9d750ab -.changed.-> nISS_68f9d750abledger_remove["ledger:remove"]
  nISS_68f9d750ab -.changed.-> nISS_68f9d750abpayments_invoice_refs["payments:invoice_refs"]
  nISS_330f00c97e["#2 fx_error<br/>354723.50 KZT"]
  nRCP_095716(["RCP/095716"]) --> nISS_330f00c97e
  nISS_330f00c97e -.changed.-> nISS_330f00c97eledger_credit_minor["ledger:credit_minor"]
  nISS_330f00c97e -.changed.-> nISS_330f00c97eledger_debit_minor["ledger:debit_minor"]
  nISS_7661e75db0["#3 fx_error<br/>18483.63 KZT"]
  nRCP_011546(["RCP/011546"]) --> nISS_7661e75db0
  nISS_7661e75db0 -.changed.-> nISS_7661e75db0ledger_credit_minor["ledger:credit_minor"]
  nISS_7661e75db0 -.changed.-> nISS_7661e75db0ledger_debit_minor["ledger:debit_minor"]
  nISS_db6c170fb5["#4 period_cutoff<br/>23282620.00 KZT"]
  nSI_062351(["SI/062351"]) --> nISS_db6c170fb5
  nISS_db6c170fb5 -.changed.-> nISS_db6c170fb5ledger_timestamp["ledger:timestamp"]
  nISS_3bf23d7ef6["#5 period_cutoff<br/>23165.00 GBP"]
  nSI_078889(["SI/078889"]) --> nISS_3bf23d7ef6
  nISS_3bf23d7ef6 -.changed.-> nISS_3bf23d7ef6ledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
