# Episode ep-9323875db342 (evaluator-only)

Period 2026-02-01T00:00:00+08:00 .. 2026-03-01T00:00:00+08:00 (end exclusive), company timezone UTC+08:00, base KZT, currencies KZT, USD, EUR. Records: {'ledger_rows': 387, 'invoices': 99, 'payments': 70, 'documents': 169, 'fx_rates': 510}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | SI/031930, SI/052177 | 2890020.00 KZT | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (partial allocation) | RCP/048265, SI/060144 | 5787151.50 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (two digits of the rate swapped when keyed in) | RCP/024016 | 35567059.50 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | RCP/052504 | 4531695.00 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_519522a5a7["#1 duplicate_invoice<br/>2890020.00 KZT"]
  nSI_031930(["SI/031930"]) --> nISS_519522a5a7
  nSI_052177(["SI/052177"]) --> nISS_519522a5a7
  nISS_519522a5a7 -.changed.-> nISS_519522a5a7invoices_add["invoices:add"]
  nISS_519522a5a7 -.changed.-> nISS_519522a5a7ledger_add["ledger:add"]
  nISS_9b26e35117["#2 payment_allocation<br/>5787151.50 KZT"]
  nRCP_048265(["RCP/048265"]) --> nISS_9b26e35117
  nSI_060144(["SI/060144"]) --> nISS_9b26e35117
  nISS_9b26e35117 -.changed.-> nISS_9b26e35117ledger_add["ledger:add"]
  nISS_9b26e35117 -.changed.-> nISS_9b26e35117ledger_credit_minor["ledger:credit_minor"]
  nISS_9b26e35117 -.changed.-> nISS_9b26e35117payments_invoice_refs["payments:invoice_refs"]
  nISS_b6a615e0a8["#3 fx_error<br/>35567059.50 KZT"]
  nRCP_024016(["RCP/024016"]) --> nISS_b6a615e0a8
  nISS_b6a615e0a8 -.changed.-> nISS_b6a615e0a8ledger_credit_minor["ledger:credit_minor"]
  nISS_b6a615e0a8 -.changed.-> nISS_b6a615e0a8ledger_debit_minor["ledger:debit_minor"]
  nISS_c871f5e03e["#4 period_cutoff<br/>4531695.00 KZT"]
  nRCP_052504(["RCP/052504"]) --> nISS_c871f5e03e
  nISS_c871f5e03e -.changed.-> nISS_c871f5e03eledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
