# Episode ep-b36c75d178cb (evaluator-only)

Period 2026-01-01T00:00:00-07:00 .. 2026-03-01T00:00:00-07:00 (end exclusive), company timezone UTC-07:00, base KZT, currencies KZT, EUR, USD. Records: {'ledger_rows': 386, 'invoices': 100, 'payments': 68, 'documents': 168, 'fx_rates': 696}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | SI/066321, SI/069388 | 6300.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (missing allocation) | RCP/057890, SI/079689 | 5876.79 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (rate of the previous day) | RCP/097509 | 36847.04 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | RCP/047036 | 2569400.00 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_7113728429["#1 duplicate_invoice<br/>6300.00 EUR"]
  nSI_066321(["SI/066321"]) --> nISS_7113728429
  nSI_069388(["SI/069388"]) --> nISS_7113728429
  nISS_7113728429 -.changed.-> nISS_7113728429invoices_add["invoices:add"]
  nISS_7113728429 -.changed.-> nISS_7113728429ledger_add["ledger:add"]
  nISS_3840a1963a["#2 payment_allocation<br/>5876.79 EUR"]
  nRCP_057890(["RCP/057890"]) --> nISS_3840a1963a
  nSI_079689(["SI/079689"]) --> nISS_3840a1963a
  nISS_3840a1963a -.changed.-> nISS_3840a1963aledger_add["ledger:add"]
  nISS_3840a1963a -.changed.-> nISS_3840a1963aledger_remove["ledger:remove"]
  nISS_3840a1963a -.changed.-> nISS_3840a1963apayments_invoice_refs["payments:invoice_refs"]
  nISS_f174e5a798["#3 fx_error<br/>36847.04 KZT"]
  nRCP_097509(["RCP/097509"]) --> nISS_f174e5a798
  nISS_f174e5a798 -.changed.-> nISS_f174e5a798ledger_credit_minor["ledger:credit_minor"]
  nISS_f174e5a798 -.changed.-> nISS_f174e5a798ledger_debit_minor["ledger:debit_minor"]
  nISS_cb95bf51da["#4 period_cutoff<br/>2569400.00 KZT"]
  nRCP_047036(["RCP/047036"]) --> nISS_cb95bf51da
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
