# Episode ep-17dce96f44fb (evaluator-only)

Period 2026-09-01T00:00:00+01:00 .. 2026-10-01T00:00:00+01:00 (end exclusive), company timezone UTC+01:00, base KZT, currencies KZT, EUR, USD. Records: {'ledger_rows': 310, 'invoices': 84, 'payments': 54, 'documents': 138, 'fx_rates': 522}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | period_cutoff | P-47769 | 20357.45 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 2 | fx_error (rate of the (wrong) posting date) | P-47769 | 98508.65 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | duplicate_invoice | F-22401, F-76900 | 55870.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 4 | payment_allocation (missing allocation) | F-53005, P-91579 | 39186.31 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (rate of the invoice date) | P-01262 | 1114.19 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | period_cutoff | P-84155 | 18369.89 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_27a3314daa["#1 period_cutoff<br/>20357.45 EUR"]
  nP_47769(["P-47769"]) --> nISS_27a3314daa
  nISS_27a3314daa -.changed.-> nISS_27a3314daaledger_credit_minor["ledger:credit_minor"]
  nISS_27a3314daa -.changed.-> nISS_27a3314daaledger_debit_minor["ledger:debit_minor"]
  nISS_27a3314daa -.changed.-> nISS_27a3314daaledger_timestamp["ledger:timestamp"]
  nISS_24196c5d77["#2 fx_error<br/>98508.65 KZT"]
  nP_47769(["P-47769"]) --> nISS_24196c5d77
  nISS_24196c5d77 -.changed.-> nISS_24196c5d77ledger_credit_minor["ledger:credit_minor"]
  nISS_24196c5d77 -.changed.-> nISS_24196c5d77ledger_debit_minor["ledger:debit_minor"]
  nISS_24196c5d77 -.changed.-> nISS_24196c5d77ledger_timestamp["ledger:timestamp"]
  nISS_449f8f7d99["#3 duplicate_invoice<br/>55870.00 USD"]
  nF_22401(["F-22401"]) --> nISS_449f8f7d99
  nF_76900(["F-76900"]) --> nISS_449f8f7d99
  nISS_449f8f7d99 -.changed.-> nISS_449f8f7d99invoices_add["invoices:add"]
  nISS_449f8f7d99 -.changed.-> nISS_449f8f7d99ledger_add["ledger:add"]
  nISS_034623171f["#4 payment_allocation<br/>39186.31 USD"]
  nF_53005(["F-53005"]) --> nISS_034623171f
  nP_91579(["P-91579"]) --> nISS_034623171f
  nISS_034623171f -.changed.-> nISS_034623171fledger_add["ledger:add"]
  nISS_034623171f -.changed.-> nISS_034623171fledger_remove["ledger:remove"]
  nISS_034623171f -.changed.-> nISS_034623171fpayments_invoice_refs["payments:invoice_refs"]
  nISS_2ea0bf50eb["#5 fx_error<br/>1114.19 EUR"]
  nP_01262(["P-01262"]) --> nISS_2ea0bf50eb
  nISS_2ea0bf50eb -.changed.-> nISS_2ea0bf50ebledger_credit_minor["ledger:credit_minor"]
  nISS_2ea0bf50eb -.changed.-> nISS_2ea0bf50ebledger_debit_minor["ledger:debit_minor"]
  nISS_5b50766cde["#6 period_cutoff<br/>18369.89 EUR"]
  nP_84155(["P-84155"]) --> nISS_5b50766cde
  nISS_5b50766cde -.changed.-> nISS_5b50766cdeledger_timestamp["ledger:timestamp"]
  nISS_27a3314daa ==>|"cutoff_fx: causes"| nISS_24196c5d77
```

## Interacting errors

- **cutoff_fx**: misposted entry converted at the rate of its (wrong) posting date.

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
