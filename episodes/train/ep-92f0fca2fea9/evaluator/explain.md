# Episode ep-92f0fca2fea9 (evaluator-only)

Period 2026-01-01T00:00:00+00:00 .. 2026-04-01T00:00:00+00:00 (end exclusive), company timezone UTC+00:00, base JPY, currencies JPY, KZT, EUR. Records: {'ledger_rows': 354, 'invoices': 86, 'payments': 64, 'documents': 150, 'fx_rates': 882}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | RCP/030812, SI/093680 | 9138.39 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate of the previous day) | RCP/030812 | 13761 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | duplicate_invoice | SI/064883, SI/082010 | 1944990 JPY | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 4 | payment_allocation (partial allocation) | RCP/094696, SI/054096 | 10098.02 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (rate of the previous day) | RCP/015754 | 231500.69 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | period_cutoff | RCP/065211 | 4930218 JPY | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_4fe2a2afe4["#1 payment_allocation<br/>9138.39 EUR"]
  nRCP_030812(["RCP/030812"]) --> nISS_4fe2a2afe4
  nSI_093680(["SI/093680"]) --> nISS_4fe2a2afe4
  nISS_4fe2a2afe4 -.changed.-> nISS_4fe2a2afe4ledger_add["ledger:add"]
  nISS_4fe2a2afe4 -.changed.-> nISS_4fe2a2afe4ledger_credit_minor["ledger:credit_minor"]
  nISS_4fe2a2afe4 -.changed.-> nISS_4fe2a2afe4ledger_debit_minor["ledger:debit_minor"]
  nISS_1a418d985b["#2 fx_error<br/>13761 JPY"]
  nRCP_030812(["RCP/030812"]) --> nISS_1a418d985b
  nISS_1a418d985b -.changed.-> nISS_1a418d985bledger_add["ledger:add"]
  nISS_1a418d985b -.changed.-> nISS_1a418d985bledger_credit_minor["ledger:credit_minor"]
  nISS_1a418d985b -.changed.-> nISS_1a418d985bledger_debit_minor["ledger:debit_minor"]
  nISS_042359f61e["#3 duplicate_invoice<br/>1944990 JPY"]
  nSI_064883(["SI/064883"]) --> nISS_042359f61e
  nSI_082010(["SI/082010"]) --> nISS_042359f61e
  nISS_042359f61e -.changed.-> nISS_042359f61einvoices_add["invoices:add"]
  nISS_042359f61e -.changed.-> nISS_042359f61eledger_add["ledger:add"]
  nISS_a41c50377a["#4 payment_allocation<br/>10098.02 EUR"]
  nRCP_094696(["RCP/094696"]) --> nISS_a41c50377a
  nSI_054096(["SI/054096"]) --> nISS_a41c50377a
  nISS_a41c50377a -.changed.-> nISS_a41c50377aledger_add["ledger:add"]
  nISS_a41c50377a -.changed.-> nISS_a41c50377aledger_credit_minor["ledger:credit_minor"]
  nISS_a41c50377a -.changed.-> nISS_a41c50377aledger_debit_minor["ledger:debit_minor"]
  nISS_5f158bcc1e["#5 fx_error<br/>231500.69 KZT"]
  nRCP_015754(["RCP/015754"]) --> nISS_5f158bcc1e
  nISS_5f158bcc1e -.changed.-> nISS_5f158bcc1eledger_credit_minor["ledger:credit_minor"]
  nISS_5f158bcc1e -.changed.-> nISS_5f158bcc1eledger_debit_minor["ledger:debit_minor"]
  nISS_8511bde991["#6 period_cutoff<br/>4930218 JPY"]
  nRCP_065211(["RCP/065211"]) --> nISS_8511bde991
  nISS_8511bde991 -.changed.-> nISS_8511bde991ledger_timestamp["ledger:timestamp"]
  nISS_4fe2a2afe4 ==>|"partial_fx: causes"| nISS_1a418d985b
```

## Interacting errors

- **partial_fx**: FX conversion applied to the allocated part; wrong rate date taken from the UTC date of the payment.

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
