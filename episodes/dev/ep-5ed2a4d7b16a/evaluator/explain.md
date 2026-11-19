# Episode ep-5ed2a4d7b16a (evaluator-only)

Period 2026-09-01T00:00:00+03:00 .. 2026-11-01T00:00:00+03:00 (end exclusive), company timezone UTC+03:00, base GBP, currencies GBP, USD, KZT. Records: {'ledger_rows': 316, 'invoices': 81, 'payments': 54, 'documents': 135, 'fx_rates': 708}.

## 4 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | SI/001698, SI/002506 | 51870.00 GBP | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | payment_allocation (missing allocation) | RCP/027919, SI/020791 | 54946.75 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 3 | fx_error (rate of the invoice date) | RCP/039893 | 74207.16 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | SI/082531 | 9095.00 USD | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_7014cabb0e["#1 duplicate_invoice<br/>51870.00 GBP"]
  nSI_001698(["SI/001698"]) --> nISS_7014cabb0e
  nSI_002506(["SI/002506"]) --> nISS_7014cabb0e
  nISS_7014cabb0e -.changed.-> nISS_7014cabb0einvoices_add["invoices:add"]
  nISS_7014cabb0e -.changed.-> nISS_7014cabb0eledger_add["ledger:add"]
  nISS_eee7fbcb01["#2 payment_allocation<br/>54946.75 USD"]
  nRCP_027919(["RCP/027919"]) --> nISS_eee7fbcb01
  nSI_020791(["SI/020791"]) --> nISS_eee7fbcb01
  nISS_eee7fbcb01 -.changed.-> nISS_eee7fbcb01ledger_add["ledger:add"]
  nISS_eee7fbcb01 -.changed.-> nISS_eee7fbcb01ledger_remove["ledger:remove"]
  nISS_eee7fbcb01 -.changed.-> nISS_eee7fbcb01payments_invoice_refs["payments:invoice_refs"]
  nISS_6b92edec5c["#3 fx_error<br/>74207.16 KZT"]
  nRCP_039893(["RCP/039893"]) --> nISS_6b92edec5c
  nISS_6b92edec5c -.changed.-> nISS_6b92edec5cledger_credit_minor["ledger:credit_minor"]
  nISS_6b92edec5c -.changed.-> nISS_6b92edec5cledger_debit_minor["ledger:debit_minor"]
  nISS_e601ba6a01["#4 period_cutoff<br/>9095.00 USD"]
  nSI_082531(["SI/082531"]) --> nISS_e601ba6a01
  nISS_e601ba6a01 -.changed.-> nISS_e601ba6a01ledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
