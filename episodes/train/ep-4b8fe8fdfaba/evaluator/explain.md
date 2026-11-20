# Episode ep-4b8fe8fdfaba (evaluator-only)

Period 2026-04-01T00:00:00+05:30 .. 2026-05-01T00:00:00+05:30 (end exclusive), company timezone UTC+05:30, base GBP, currencies GBP, USD, EUR. Records: {'ledger_rows': 319, 'invoices': 83, 'payments': 54, 'documents': 137, 'fx_rates': 522}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | INV-97594, PAY-51903 | 4076.39 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate taken for the UTC date instead of the local date) | PAY-51903 | 74.19 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | PAY-63327 | 44659.47 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | PAY-63327 | 494.97 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | INV-21052, INV-76653 | 47310.00 GBP | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | INV-30698, INV-80822 | 19480.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |

## Causal graph

```mermaid
flowchart LR
  nISS_dcc31aa52e["#1 payment_allocation<br/>4076.39 USD"]
  nINV_97594(["INV-97594"]) --> nISS_dcc31aa52e
  nPAY_51903(["PAY-51903"]) --> nISS_dcc31aa52e
  nISS_dcc31aa52e -.changed.-> nISS_dcc31aa52eledger_add["ledger:add"]
  nISS_dcc31aa52e -.changed.-> nISS_dcc31aa52eledger_credit_minor["ledger:credit_minor"]
  nISS_dcc31aa52e -.changed.-> nISS_dcc31aa52eledger_debit_minor["ledger:debit_minor"]
  nISS_f741d82245["#2 fx_error<br/>74.19 GBP"]
  nPAY_51903(["PAY-51903"]) --> nISS_f741d82245
  nISS_f741d82245 -.changed.-> nISS_f741d82245ledger_add["ledger:add"]
  nISS_f741d82245 -.changed.-> nISS_f741d82245ledger_credit_minor["ledger:credit_minor"]
  nISS_f741d82245 -.changed.-> nISS_f741d82245ledger_debit_minor["ledger:debit_minor"]
  nISS_e14d00804d["#3 period_cutoff<br/>44659.47 GBP"]
  nPAY_63327(["PAY-63327"]) --> nISS_e14d00804d
  nISS_e14d00804d -.changed.-> nISS_e14d00804dledger_credit_minor["ledger:credit_minor"]
  nISS_e14d00804d -.changed.-> nISS_e14d00804dledger_debit_minor["ledger:debit_minor"]
  nISS_e14d00804d -.changed.-> nISS_e14d00804dledger_timestamp["ledger:timestamp"]
  nISS_84aab0649f["#4 fx_error<br/>494.97 USD"]
  nPAY_63327(["PAY-63327"]) --> nISS_84aab0649f
  nISS_84aab0649f -.changed.-> nISS_84aab0649fledger_credit_minor["ledger:credit_minor"]
  nISS_84aab0649f -.changed.-> nISS_84aab0649fledger_debit_minor["ledger:debit_minor"]
  nISS_84aab0649f -.changed.-> nISS_84aab0649fledger_timestamp["ledger:timestamp"]
  nISS_2ec7c4270f["#5 duplicate_invoice<br/>47310.00 GBP"]
  nINV_21052(["INV-21052"]) --> nISS_2ec7c4270f
  nINV_76653(["INV-76653"]) --> nISS_2ec7c4270f
  nISS_2ec7c4270f -.changed.-> nISS_2ec7c4270finvoices_add["invoices:add"]
  nISS_2ec7c4270f -.changed.-> nISS_2ec7c4270fledger_add["ledger:add"]
  nISS_c23005366f["#6 duplicate_invoice<br/>19480.00 USD"]
  nINV_30698(["INV-30698"]) --> nISS_c23005366f
  nINV_80822(["INV-80822"]) --> nISS_c23005366f
  nISS_c23005366f -.changed.-> nISS_c23005366finvoices_add["invoices:add"]
  nISS_c23005366f -.changed.-> nISS_c23005366fledger_add["ledger:add"]
  nISS_dcc31aa52e ==>|"partial_fx: causes"| nISS_f741d82245
  nISS_e14d00804d ==>|"cutoff_fx: causes"| nISS_84aab0649f
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
