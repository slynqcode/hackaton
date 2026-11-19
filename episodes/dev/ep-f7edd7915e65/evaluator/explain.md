# Episode ep-f7edd7915e65 (evaluator-only)

Period 2026-02-01T00:00:00+08:00 .. 2026-04-01T00:00:00+08:00 (end exclusive), company timezone UTC+08:00, base JPY, currencies JPY, EUR, GBP. Records: {'ledger_rows': 339, 'invoices': 83, 'payments': 61, 'documents': 144, 'fx_rates': 696}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | INV-46709, PAY-70963 | 13738.08 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate taken for the UTC date instead of the local date) | PAY-70963 | 31277 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | PAY-24245 | 11013.71 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | PAY-24245 | 14726 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | INV-35638, INV-54607 | 28190.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | INV-17813, INV-44627 | 3933100 JPY | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |

## Causal graph

```mermaid
flowchart LR
  nISS_2b4cce1e07["#1 payment_allocation<br/>13738.08 EUR"]
  nINV_46709(["INV-46709"]) --> nISS_2b4cce1e07
  nPAY_70963(["PAY-70963"]) --> nISS_2b4cce1e07
  nISS_2b4cce1e07 -.changed.-> nISS_2b4cce1e07ledger_add["ledger:add"]
  nISS_2b4cce1e07 -.changed.-> nISS_2b4cce1e07ledger_credit_minor["ledger:credit_minor"]
  nISS_2b4cce1e07 -.changed.-> nISS_2b4cce1e07ledger_debit_minor["ledger:debit_minor"]
  nISS_b25f7e75e1["#2 fx_error<br/>31277 JPY"]
  nPAY_70963(["PAY-70963"]) --> nISS_b25f7e75e1
  nISS_b25f7e75e1 -.changed.-> nISS_b25f7e75e1ledger_add["ledger:add"]
  nISS_b25f7e75e1 -.changed.-> nISS_b25f7e75e1ledger_credit_minor["ledger:credit_minor"]
  nISS_b25f7e75e1 -.changed.-> nISS_b25f7e75e1ledger_debit_minor["ledger:debit_minor"]
  nISS_dc8d23f3fb["#3 period_cutoff<br/>11013.71 EUR"]
  nPAY_24245(["PAY-24245"]) --> nISS_dc8d23f3fb
  nISS_dc8d23f3fb -.changed.-> nISS_dc8d23f3fbledger_credit_minor["ledger:credit_minor"]
  nISS_dc8d23f3fb -.changed.-> nISS_dc8d23f3fbledger_debit_minor["ledger:debit_minor"]
  nISS_dc8d23f3fb -.changed.-> nISS_dc8d23f3fbledger_timestamp["ledger:timestamp"]
  nISS_9849c7f601["#4 fx_error<br/>14726 JPY"]
  nPAY_24245(["PAY-24245"]) --> nISS_9849c7f601
  nISS_9849c7f601 -.changed.-> nISS_9849c7f601ledger_credit_minor["ledger:credit_minor"]
  nISS_9849c7f601 -.changed.-> nISS_9849c7f601ledger_debit_minor["ledger:debit_minor"]
  nISS_9849c7f601 -.changed.-> nISS_9849c7f601ledger_timestamp["ledger:timestamp"]
  nISS_53dccdea47["#5 duplicate_invoice<br/>28190.00 EUR"]
  nINV_35638(["INV-35638"]) --> nISS_53dccdea47
  nINV_54607(["INV-54607"]) --> nISS_53dccdea47
  nISS_53dccdea47 -.changed.-> nISS_53dccdea47invoices_add["invoices:add"]
  nISS_53dccdea47 -.changed.-> nISS_53dccdea47ledger_add["ledger:add"]
  nISS_974bb94029["#6 duplicate_invoice<br/>3933100 JPY"]
  nINV_17813(["INV-17813"]) --> nISS_974bb94029
  nINV_44627(["INV-44627"]) --> nISS_974bb94029
  nISS_974bb94029 -.changed.-> nISS_974bb94029invoices_add["invoices:add"]
  nISS_974bb94029 -.changed.-> nISS_974bb94029ledger_add["ledger:add"]
  nISS_2b4cce1e07 ==>|"partial_fx: causes"| nISS_b25f7e75e1
  nISS_dc8d23f3fb ==>|"cutoff_fx: causes"| nISS_9849c7f601
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
