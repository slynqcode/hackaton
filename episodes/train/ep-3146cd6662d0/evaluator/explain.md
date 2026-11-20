# Episode ep-3146cd6662d0 (evaluator-only)

Period 2026-07-01T00:00:00+00:00 .. 2026-09-01T00:00:00+00:00 (end exclusive), company timezone UTC+00:00, base USD, currencies USD, JPY, KZT. Records: {'ledger_rows': 379, 'invoices': 102, 'payments': 71, 'documents': 173, 'fx_rates': 714}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | INV-25564, INV-44687 | 28341735.00 KZT | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (partial allocation) | INV-02281, PAY-80487 | 21182297.50 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (rate of the previous day) | PAY-46495 | 358.74 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | INV-51779 | 2445.00 USD | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_784fdb8825["#1 duplicate_invoice<br/>28341735.00 KZT"]
  nINV_25564(["INV-25564"]) --> nISS_784fdb8825
  nINV_44687(["INV-44687"]) --> nISS_784fdb8825
  nISS_784fdb8825 -.changed.-> nISS_784fdb8825invoices_add["invoices:add"]
  nISS_784fdb8825 -.changed.-> nISS_784fdb8825ledger_add["ledger:add"]
  nISS_28ae9d8f81["#2 payment_allocation<br/>21182297.50 KZT"]
  nINV_02281(["INV-02281"]) --> nISS_28ae9d8f81
  nPAY_80487(["PAY-80487"]) --> nISS_28ae9d8f81
  nISS_28ae9d8f81 -.changed.-> nISS_28ae9d8f81ledger_add["ledger:add"]
  nISS_28ae9d8f81 -.changed.-> nISS_28ae9d8f81ledger_credit_minor["ledger:credit_minor"]
  nISS_28ae9d8f81 -.changed.-> nISS_28ae9d8f81payments_invoice_refs["payments:invoice_refs"]
  nISS_a8c3500467["#3 fx_error<br/>358.74 USD"]
  nPAY_46495(["PAY-46495"]) --> nISS_a8c3500467
  nISS_a8c3500467 -.changed.-> nISS_a8c3500467ledger_credit_minor["ledger:credit_minor"]
  nISS_a8c3500467 -.changed.-> nISS_a8c3500467ledger_debit_minor["ledger:debit_minor"]
  nISS_a7e0ab614f["#4 period_cutoff<br/>2445.00 USD"]
  nINV_51779(["INV-51779"]) --> nISS_a7e0ab614f
  nISS_a7e0ab614f -.changed.-> nISS_a7e0ab614fledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
