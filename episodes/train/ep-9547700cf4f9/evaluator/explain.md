# Episode ep-9547700cf4f9 (evaluator-only)

Period 2026-06-01T00:00:00+09:00 .. 2026-07-01T00:00:00+09:00 (end exclusive), company timezone UTC+09:00, base JPY, currencies JPY, USD, KZT. Records: {'ledger_rows': 309, 'invoices': 85, 'payments': 53, 'documents': 138, 'fx_rates': 522}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | period_cutoff | P-20400 | 20879736.79 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 2 | fx_error (rate of the (wrong) posting date) | P-20400 | 903.97 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | duplicate_invoice | F-14157, F-38856 | 259290 JPY | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 4 | payment_allocation (partial allocation) | F-89082, P-09329 | 7765680.65 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (rate of the previous day) | P-29065 | 738.85 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | period_cutoff | F-24946 | 6736175 JPY | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_4c6610bd06["#1 period_cutoff<br/>20879736.79 KZT"]
  nP_20400(["P-20400"]) --> nISS_4c6610bd06
  nISS_4c6610bd06 -.changed.-> nISS_4c6610bd06ledger_credit_minor["ledger:credit_minor"]
  nISS_4c6610bd06 -.changed.-> nISS_4c6610bd06ledger_debit_minor["ledger:debit_minor"]
  nISS_4c6610bd06 -.changed.-> nISS_4c6610bd06ledger_timestamp["ledger:timestamp"]
  nISS_495e6df5c3["#2 fx_error<br/>903.97 USD"]
  nP_20400(["P-20400"]) --> nISS_495e6df5c3
  nISS_495e6df5c3 -.changed.-> nISS_495e6df5c3ledger_credit_minor["ledger:credit_minor"]
  nISS_495e6df5c3 -.changed.-> nISS_495e6df5c3ledger_debit_minor["ledger:debit_minor"]
  nISS_495e6df5c3 -.changed.-> nISS_495e6df5c3ledger_timestamp["ledger:timestamp"]
  nISS_a0a4b8f202["#3 duplicate_invoice<br/>259290 JPY"]
  nF_14157(["F-14157"]) --> nISS_a0a4b8f202
  nF_38856(["F-38856"]) --> nISS_a0a4b8f202
  nISS_a0a4b8f202 -.changed.-> nISS_a0a4b8f202invoices_add["invoices:add"]
  nISS_a0a4b8f202 -.changed.-> nISS_a0a4b8f202ledger_add["ledger:add"]
  nISS_fccefd16c3["#4 payment_allocation<br/>7765680.65 KZT"]
  nF_89082(["F-89082"]) --> nISS_fccefd16c3
  nP_09329(["P-09329"]) --> nISS_fccefd16c3
  nISS_fccefd16c3 -.changed.-> nISS_fccefd16c3ledger_add["ledger:add"]
  nISS_fccefd16c3 -.changed.-> nISS_fccefd16c3ledger_credit_minor["ledger:credit_minor"]
  nISS_fccefd16c3 -.changed.-> nISS_fccefd16c3ledger_debit_minor["ledger:debit_minor"]
  nISS_603f61fa16["#5 fx_error<br/>738.85 USD"]
  nP_29065(["P-29065"]) --> nISS_603f61fa16
  nISS_603f61fa16 -.changed.-> nISS_603f61fa16ledger_credit_minor["ledger:credit_minor"]
  nISS_603f61fa16 -.changed.-> nISS_603f61fa16ledger_debit_minor["ledger:debit_minor"]
  nISS_148129786c["#6 period_cutoff<br/>6736175 JPY"]
  nF_24946(["F-24946"]) --> nISS_148129786c
  nISS_148129786c -.changed.-> nISS_148129786cledger_timestamp["ledger:timestamp"]
  nISS_4c6610bd06 ==>|"cutoff_fx: causes"| nISS_495e6df5c3
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
