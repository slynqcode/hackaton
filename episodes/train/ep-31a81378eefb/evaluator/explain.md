# Episode ep-31a81378eefb (evaluator-only)

Period 2026-07-01T00:00:00+05:00 .. 2026-09-01T00:00:00+05:00 (end exclusive), company timezone UTC+05:00, base JPY, currencies JPY, KZT, EUR. Records: {'ledger_rows': 313, 'invoices': 84, 'payments': 56, 'documents': 140, 'fx_rates': 714}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | period_cutoff | P-69759 | 15249349.01 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 2 | fx_error (rate of the (wrong) posting date) | P-69759 | 49064 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | duplicate_invoice | F-30316, F-41001 | 2009760 JPY | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 4 | payment_allocation (partial allocation) | F-78784, P-17184 | 7263.00 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (two digits of the rate swapped when keyed in) | P-40517 | 3003558 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | period_cutoff | P-42607 | 3924660 JPY | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_0286dbacb8["#1 period_cutoff<br/>15249349.01 KZT"]
  nP_69759(["P-69759"]) --> nISS_0286dbacb8
  nISS_0286dbacb8 -.changed.-> nISS_0286dbacb8ledger_credit_minor["ledger:credit_minor"]
  nISS_0286dbacb8 -.changed.-> nISS_0286dbacb8ledger_debit_minor["ledger:debit_minor"]
  nISS_0286dbacb8 -.changed.-> nISS_0286dbacb8ledger_timestamp["ledger:timestamp"]
  nISS_00fae3b2da["#2 fx_error<br/>49064 JPY"]
  nP_69759(["P-69759"]) --> nISS_00fae3b2da
  nISS_00fae3b2da -.changed.-> nISS_00fae3b2daledger_credit_minor["ledger:credit_minor"]
  nISS_00fae3b2da -.changed.-> nISS_00fae3b2daledger_debit_minor["ledger:debit_minor"]
  nISS_00fae3b2da -.changed.-> nISS_00fae3b2daledger_timestamp["ledger:timestamp"]
  nISS_ee232636cf["#3 duplicate_invoice<br/>2009760 JPY"]
  nF_30316(["F-30316"]) --> nISS_ee232636cf
  nF_41001(["F-41001"]) --> nISS_ee232636cf
  nISS_ee232636cf -.changed.-> nISS_ee232636cfinvoices_add["invoices:add"]
  nISS_ee232636cf -.changed.-> nISS_ee232636cfledger_add["ledger:add"]
  nISS_9fea75d1c7["#4 payment_allocation<br/>7263.00 EUR"]
  nF_78784(["F-78784"]) --> nISS_9fea75d1c7
  nP_17184(["P-17184"]) --> nISS_9fea75d1c7
  nISS_9fea75d1c7 -.changed.-> nISS_9fea75d1c7ledger_add["ledger:add"]
  nISS_9fea75d1c7 -.changed.-> nISS_9fea75d1c7ledger_credit_minor["ledger:credit_minor"]
  nISS_9fea75d1c7 -.changed.-> nISS_9fea75d1c7payments_invoice_refs["payments:invoice_refs"]
  nISS_17c9bce9b4["#5 fx_error<br/>3003558 JPY"]
  nP_40517(["P-40517"]) --> nISS_17c9bce9b4
  nISS_17c9bce9b4 -.changed.-> nISS_17c9bce9b4ledger_credit_minor["ledger:credit_minor"]
  nISS_17c9bce9b4 -.changed.-> nISS_17c9bce9b4ledger_debit_minor["ledger:debit_minor"]
  nISS_49cbc3c74a["#6 period_cutoff<br/>3924660 JPY"]
  nP_42607(["P-42607"]) --> nISS_49cbc3c74a
  nISS_49cbc3c74a -.changed.-> nISS_49cbc3c74aledger_timestamp["ledger:timestamp"]
  nISS_0286dbacb8 ==>|"cutoff_fx: causes"| nISS_00fae3b2da
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
