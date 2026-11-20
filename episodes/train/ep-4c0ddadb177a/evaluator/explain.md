# Episode ep-4c0ddadb177a (evaluator-only)

Period 2026-03-01T00:00:00+02:00 .. 2026-04-01T00:00:00+02:00 (end exclusive), company timezone UTC+02:00, base KZT, currencies KZT, EUR, USD. Records: {'ledger_rows': 297, 'invoices': 82, 'payments': 48, 'documents': 130, 'fx_rates': 528}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | SI/023806, SI/067973 | 11235.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (partial allocation) | RCP/068601, SI/042612 | 24405868.76 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (two digits of the rate swapped when keyed in) | RCP/075641 | 155807.03 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | SI/078415 | 6684175.00 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_eb016e3596["#1 duplicate_invoice<br/>11235.00 EUR"]
  nSI_023806(["SI/023806"]) --> nISS_eb016e3596
  nSI_067973(["SI/067973"]) --> nISS_eb016e3596
  nISS_eb016e3596 -.changed.-> nISS_eb016e3596invoices_add["invoices:add"]
  nISS_eb016e3596 -.changed.-> nISS_eb016e3596ledger_add["ledger:add"]
  nISS_867a2c77a7["#2 payment_allocation<br/>24405868.76 KZT"]
  nRCP_068601(["RCP/068601"]) --> nISS_867a2c77a7
  nSI_042612(["SI/042612"]) --> nISS_867a2c77a7
  nISS_867a2c77a7 -.changed.-> nISS_867a2c77a7ledger_add["ledger:add"]
  nISS_867a2c77a7 -.changed.-> nISS_867a2c77a7ledger_credit_minor["ledger:credit_minor"]
  nISS_867a2c77a7 -.changed.-> nISS_867a2c77a7ledger_debit_minor["ledger:debit_minor"]
  nISS_c9b23685f2["#3 fx_error<br/>155807.03 EUR"]
  nRCP_075641(["RCP/075641"]) --> nISS_c9b23685f2
  nISS_c9b23685f2 -.changed.-> nISS_c9b23685f2ledger_credit_minor["ledger:credit_minor"]
  nISS_c9b23685f2 -.changed.-> nISS_c9b23685f2ledger_debit_minor["ledger:debit_minor"]
  nISS_fda410ef38["#4 period_cutoff<br/>6684175.00 KZT"]
  nSI_078415(["SI/078415"]) --> nISS_fda410ef38
  nISS_fda410ef38 -.changed.-> nISS_fda410ef38ledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
