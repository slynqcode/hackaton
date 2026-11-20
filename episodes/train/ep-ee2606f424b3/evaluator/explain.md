# Episode ep-ee2606f424b3 (evaluator-only)

Period 2026-01-01T00:00:00-07:00 .. 2026-03-01T00:00:00-07:00 (end exclusive), company timezone UTC-07:00, base KZT, currencies KZT, EUR, USD. Records: {'ledger_rows': 388, 'invoices': 100, 'payments': 68, 'documents': 168, 'fx_rates': 696}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | SI/021718, SI/073492 | 2569400.00 KZT | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (missing allocation) | RCP/024787, SI/081293 | 14012170.00 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (rate of the previous day) | RCP/028156 | 151524.27 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | RCP/043631 | 21408035.00 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_7113728429["#1 duplicate_invoice<br/>2569400.00 KZT"]
  nSI_021718(["SI/021718"]) --> nISS_7113728429
  nSI_073492(["SI/073492"]) --> nISS_7113728429
  nISS_7113728429 -.changed.-> nISS_7113728429invoices_add["invoices:add"]
  nISS_7113728429 -.changed.-> nISS_7113728429ledger_add["ledger:add"]
  nISS_3840a1963a["#2 payment_allocation<br/>14012170.00 KZT"]
  nRCP_024787(["RCP/024787"]) --> nISS_3840a1963a
  nSI_081293(["SI/081293"]) --> nISS_3840a1963a
  nISS_3840a1963a -.changed.-> nISS_3840a1963aledger_add["ledger:add"]
  nISS_3840a1963a -.changed.-> nISS_3840a1963aledger_remove["ledger:remove"]
  nISS_3840a1963a -.changed.-> nISS_3840a1963apayments_invoice_refs["payments:invoice_refs"]
  nISS_f174e5a798["#3 fx_error<br/>151524.27 KZT"]
  nRCP_028156(["RCP/028156"]) --> nISS_f174e5a798
  nISS_f174e5a798 -.changed.-> nISS_f174e5a798ledger_credit_minor["ledger:credit_minor"]
  nISS_f174e5a798 -.changed.-> nISS_f174e5a798ledger_debit_minor["ledger:debit_minor"]
  nISS_cb95bf51da["#4 period_cutoff<br/>21408035.00 KZT"]
  nRCP_043631(["RCP/043631"]) --> nISS_cb95bf51da
  nISS_cb95bf51da -.changed.-> nISS_cb95bf51daledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
