# Episode ep-23e36eff0177 (evaluator-only)

Period 2026-08-01T00:00:00+00:00 .. 2026-09-01T00:00:00+00:00 (end exclusive), company timezone UTC+00:00, base USD, currencies USD, EUR, KZT. Records: {'ledger_rows': 349, 'invoices': 98, 'payments': 56, 'documents': 154, 'fx_rates': 528}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | INV-49040, INV-79320 | 58850.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (partial allocation) | INV-21104, PAY-88801 | 6513762.40 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (rate of the invoice date) | PAY-72354 | 266967.54 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | INV-38398 | 10050.00 USD | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_62e0765c7a["#1 duplicate_invoice<br/>58850.00 EUR"]
  nINV_49040(["INV-49040"]) --> nISS_62e0765c7a
  nINV_79320(["INV-79320"]) --> nISS_62e0765c7a
  nISS_62e0765c7a -.changed.-> nISS_62e0765c7ainvoices_add["invoices:add"]
  nISS_62e0765c7a -.changed.-> nISS_62e0765c7aledger_add["ledger:add"]
  nISS_d48382f3f0["#2 payment_allocation<br/>6513762.40 KZT"]
  nINV_21104(["INV-21104"]) --> nISS_d48382f3f0
  nPAY_88801(["PAY-88801"]) --> nISS_d48382f3f0
  nISS_d48382f3f0 -.changed.-> nISS_d48382f3f0ledger_add["ledger:add"]
  nISS_d48382f3f0 -.changed.-> nISS_d48382f3f0ledger_credit_minor["ledger:credit_minor"]
  nISS_d48382f3f0 -.changed.-> nISS_d48382f3f0payments_invoice_refs["payments:invoice_refs"]
  nISS_8bbcba4b71["#3 fx_error<br/>266967.54 KZT"]
  nPAY_72354(["PAY-72354"]) --> nISS_8bbcba4b71
  nISS_8bbcba4b71 -.changed.-> nISS_8bbcba4b71ledger_credit_minor["ledger:credit_minor"]
  nISS_8bbcba4b71 -.changed.-> nISS_8bbcba4b71ledger_debit_minor["ledger:debit_minor"]
  nISS_3b9c25efab["#4 period_cutoff<br/>10050.00 USD"]
  nINV_38398(["INV-38398"]) --> nISS_3b9c25efab
  nISS_3b9c25efab -.changed.-> nISS_3b9c25efabledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
