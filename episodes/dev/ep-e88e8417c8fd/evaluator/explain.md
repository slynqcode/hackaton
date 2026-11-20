# Episode ep-e88e8417c8fd (evaluator-only)

Period 2026-02-01T00:00:00+01:00 .. 2026-03-01T00:00:00+01:00 (end exclusive), company timezone UTC+01:00, base JPY, currencies JPY, GBP, KZT. Records: {'ledger_rows': 324, 'invoices': 90, 'payments': 53, 'documents': 143, 'fx_rates': 510}.

## 12 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | F-10620, P-13046 | 3956747.25 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate taken for the UTC date instead of the local date) | P-13046 | 3676 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | P-54956 | 10906441 JPY | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | P-54956 | 671.00 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | F-37091, F-64571 | 9631055.00 KZT | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | F-15682, F-87401 | 355400 JPY | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 7 | payment_allocation (missing allocation) | F-52135, P-31860 | 29480036.74 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 8 | payment_allocation (partial allocation) | F-61813, P-27072 | 1456200 JPY | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 9 | fx_error (rate of the invoice date) | P-01638 | 2976.69 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 10 | fx_error (two digits of the rate swapped when keyed in) | P-05638 | 8261.93 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 11 | period_cutoff | F-83116 | 14597370.00 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 12 | period_cutoff | F-97679 | 6971745 JPY | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_48098e3a1f["#1 payment_allocation<br/>3956747.25 KZT"]
  nF_10620(["F-10620"]) --> nISS_48098e3a1f
  nP_13046(["P-13046"]) --> nISS_48098e3a1f
  nISS_48098e3a1f -.changed.-> nISS_48098e3a1fledger_add["ledger:add"]
  nISS_48098e3a1f -.changed.-> nISS_48098e3a1fledger_credit_minor["ledger:credit_minor"]
  nISS_48098e3a1f -.changed.-> nISS_48098e3a1fledger_debit_minor["ledger:debit_minor"]
  nISS_7ffc330187["#2 fx_error<br/>3676 JPY"]
  nP_13046(["P-13046"]) --> nISS_7ffc330187
  nISS_7ffc330187 -.changed.-> nISS_7ffc330187ledger_add["ledger:add"]
  nISS_7ffc330187 -.changed.-> nISS_7ffc330187ledger_credit_minor["ledger:credit_minor"]
  nISS_7ffc330187 -.changed.-> nISS_7ffc330187ledger_debit_minor["ledger:debit_minor"]
  nISS_8cda3ce121["#3 period_cutoff<br/>10906441 JPY"]
  nP_54956(["P-54956"]) --> nISS_8cda3ce121
  nISS_8cda3ce121 -.changed.-> nISS_8cda3ce121ledger_credit_minor["ledger:credit_minor"]
  nISS_8cda3ce121 -.changed.-> nISS_8cda3ce121ledger_debit_minor["ledger:debit_minor"]
  nISS_8cda3ce121 -.changed.-> nISS_8cda3ce121ledger_timestamp["ledger:timestamp"]
  nISS_0bcd5ba5c0["#4 fx_error<br/>671.00 GBP"]
  nP_54956(["P-54956"]) --> nISS_0bcd5ba5c0
  nISS_0bcd5ba5c0 -.changed.-> nISS_0bcd5ba5c0ledger_credit_minor["ledger:credit_minor"]
  nISS_0bcd5ba5c0 -.changed.-> nISS_0bcd5ba5c0ledger_debit_minor["ledger:debit_minor"]
  nISS_0bcd5ba5c0 -.changed.-> nISS_0bcd5ba5c0ledger_timestamp["ledger:timestamp"]
  nISS_1ca5b7ac8b["#5 duplicate_invoice<br/>9631055.00 KZT"]
  nF_37091(["F-37091"]) --> nISS_1ca5b7ac8b
  nF_64571(["F-64571"]) --> nISS_1ca5b7ac8b
  nISS_1ca5b7ac8b -.changed.-> nISS_1ca5b7ac8binvoices_add["invoices:add"]
  nISS_1ca5b7ac8b -.changed.-> nISS_1ca5b7ac8bledger_add["ledger:add"]
  nISS_0d5b094cee["#6 duplicate_invoice<br/>355400 JPY"]
  nF_15682(["F-15682"]) --> nISS_0d5b094cee
  nF_87401(["F-87401"]) --> nISS_0d5b094cee
  nISS_0d5b094cee -.changed.-> nISS_0d5b094ceeinvoices_add["invoices:add"]
  nISS_0d5b094cee -.changed.-> nISS_0d5b094ceeledger_add["ledger:add"]
  nISS_7e808fcad3["#7 payment_allocation<br/>29480036.74 KZT"]
  nF_52135(["F-52135"]) --> nISS_7e808fcad3
  nP_31860(["P-31860"]) --> nISS_7e808fcad3
  nISS_7e808fcad3 -.changed.-> nISS_7e808fcad3ledger_add["ledger:add"]
  nISS_7e808fcad3 -.changed.-> nISS_7e808fcad3ledger_remove["ledger:remove"]
  nISS_7e808fcad3 -.changed.-> nISS_7e808fcad3payments_invoice_refs["payments:invoice_refs"]
  nISS_05bdec413d["#8 payment_allocation<br/>1456200 JPY"]
  nF_61813(["F-61813"]) --> nISS_05bdec413d
  nP_27072(["P-27072"]) --> nISS_05bdec413d
  nISS_05bdec413d -.changed.-> nISS_05bdec413dledger_add["ledger:add"]
  nISS_05bdec413d -.changed.-> nISS_05bdec413dledger_credit_minor["ledger:credit_minor"]
  nISS_05bdec413d -.changed.-> nISS_05bdec413dpayments_invoice_refs["payments:invoice_refs"]
  nISS_f92b3116dc["#9 fx_error<br/>2976.69 GBP"]
  nP_01638(["P-01638"]) --> nISS_f92b3116dc
  nISS_f92b3116dc -.changed.-> nISS_f92b3116dcledger_credit_minor["ledger:credit_minor"]
  nISS_f92b3116dc -.changed.-> nISS_f92b3116dcledger_debit_minor["ledger:debit_minor"]
  nISS_75c735a01a["#10 fx_error<br/>8261.93 GBP"]
  nP_05638(["P-05638"]) --> nISS_75c735a01a
  nISS_75c735a01a -.changed.-> nISS_75c735a01aledger_credit_minor["ledger:credit_minor"]
  nISS_75c735a01a -.changed.-> nISS_75c735a01aledger_debit_minor["ledger:debit_minor"]
  nISS_26702a4b1c["#11 period_cutoff<br/>14597370.00 KZT"]
  nF_83116(["F-83116"]) --> nISS_26702a4b1c
  nISS_26702a4b1c -.changed.-> nISS_26702a4b1cledger_timestamp["ledger:timestamp"]
  nISS_55871a2422["#12 period_cutoff<br/>6971745 JPY"]
  nF_97679(["F-97679"]) --> nISS_55871a2422
  nISS_55871a2422 -.changed.-> nISS_55871a2422ledger_timestamp["ledger:timestamp"]
  nISS_48098e3a1f ==>|"partial_fx: causes"| nISS_7ffc330187
  nISS_8cda3ce121 ==>|"cutoff_fx: causes"| nISS_0bcd5ba5c0
```

## Interacting errors

- **partial_fx**: FX conversion applied to the allocated part; wrong rate date taken from the UTC date of the payment.
- **cutoff_fx**: misposted entry converted at the rate of its (wrong) posting date.

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
