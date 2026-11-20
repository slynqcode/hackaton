# Episode ep-dc78573232db (evaluator-only)

Period 2026-04-01T00:00:00-05:00 .. 2026-07-01T00:00:00-05:00 (end exclusive), company timezone UTC-05:00, base GBP, currencies GBP, USD, KZT. Records: {'ledger_rows': 331, 'invoices': 86, 'payments': 61, 'documents': 147, 'fx_rates': 888}.

## 5 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | RCP/036480, SI/090654 | 13598.14 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate of the invoice date) | RCP/037246 | 531.35 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | fx_error (rate of the previous day) | RCP/055881 | 153.74 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | RCP/022475 | 51216.14 USD | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 5 | period_cutoff | SI/008777 | 17520.00 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_0011a6c6bf["#1 payment_allocation<br/>13598.14 USD"]
  nRCP_036480(["RCP/036480"]) --> nISS_0011a6c6bf
  nSI_090654(["SI/090654"]) --> nISS_0011a6c6bf
  nISS_0011a6c6bf -.changed.-> nISS_0011a6c6bfledger_add["ledger:add"]
  nISS_0011a6c6bf -.changed.-> nISS_0011a6c6bfledger_credit_minor["ledger:credit_minor"]
  nISS_0011a6c6bf -.changed.-> nISS_0011a6c6bfledger_debit_minor["ledger:debit_minor"]
  nISS_d03d70c0af["#2 fx_error<br/>531.35 GBP"]
  nRCP_037246(["RCP/037246"]) --> nISS_d03d70c0af
  nISS_d03d70c0af -.changed.-> nISS_d03d70c0afledger_credit_minor["ledger:credit_minor"]
  nISS_d03d70c0af -.changed.-> nISS_d03d70c0afledger_debit_minor["ledger:debit_minor"]
  nISS_b825d2cc09["#3 fx_error<br/>153.74 GBP"]
  nRCP_055881(["RCP/055881"]) --> nISS_b825d2cc09
  nISS_b825d2cc09 -.changed.-> nISS_b825d2cc09ledger_credit_minor["ledger:credit_minor"]
  nISS_b825d2cc09 -.changed.-> nISS_b825d2cc09ledger_debit_minor["ledger:debit_minor"]
  nISS_b027f6a57f["#4 period_cutoff<br/>51216.14 USD"]
  nRCP_022475(["RCP/022475"]) --> nISS_b027f6a57f
  nISS_b027f6a57f -.changed.-> nISS_b027f6a57fledger_timestamp["ledger:timestamp"]
  nISS_b7f6f35965["#5 period_cutoff<br/>17520.00 GBP"]
  nSI_008777(["SI/008777"]) --> nISS_b7f6f35965
  nISS_b7f6f35965 -.changed.-> nISS_b7f6f35965ledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
