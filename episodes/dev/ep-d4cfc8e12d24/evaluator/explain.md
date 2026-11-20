# Episode ep-d4cfc8e12d24 (evaluator-only)

Period 2026-01-01T00:00:00+08:00 .. 2026-04-01T00:00:00+08:00 (end exclusive), company timezone UTC+08:00, base USD, currencies USD, KZT, GBP. Records: {'ledger_rows': 336, 'invoices': 88, 'payments': 64, 'documents': 152, 'fx_rates': 882}.

## 5 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (missing allocation) | RCP/028040, SI/087817 | 31130.00 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate of the invoice date) | RCP/037185 | 130.83 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | fx_error (two digits of the rate swapped when keyed in) | RCP/082722 | 18942.66 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 4 | period_cutoff | SI/084546 | 57655.00 USD | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 5 | period_cutoff | RCP/091099 | 83625.00 USD | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_b4c9f4850e["#1 payment_allocation<br/>31130.00 USD"]
  nRCP_028040(["RCP/028040"]) --> nISS_b4c9f4850e
  nSI_087817(["SI/087817"]) --> nISS_b4c9f4850e
  nISS_b4c9f4850e -.changed.-> nISS_b4c9f4850eledger_add["ledger:add"]
  nISS_b4c9f4850e -.changed.-> nISS_b4c9f4850eledger_remove["ledger:remove"]
  nISS_b4c9f4850e -.changed.-> nISS_b4c9f4850epayments_invoice_refs["payments:invoice_refs"]
  nISS_1b21d4856f["#2 fx_error<br/>130.83 GBP"]
  nRCP_037185(["RCP/037185"]) --> nISS_1b21d4856f
  nISS_1b21d4856f -.changed.-> nISS_1b21d4856fledger_credit_minor["ledger:credit_minor"]
  nISS_1b21d4856f -.changed.-> nISS_1b21d4856fledger_debit_minor["ledger:debit_minor"]
  nISS_0e3e7ae761["#3 fx_error<br/>18942.66 GBP"]
  nRCP_082722(["RCP/082722"]) --> nISS_0e3e7ae761
  nISS_0e3e7ae761 -.changed.-> nISS_0e3e7ae761ledger_credit_minor["ledger:credit_minor"]
  nISS_0e3e7ae761 -.changed.-> nISS_0e3e7ae761ledger_debit_minor["ledger:debit_minor"]
  nISS_aab62c0301["#4 period_cutoff<br/>57655.00 USD"]
  nSI_084546(["SI/084546"]) --> nISS_aab62c0301
  nISS_aab62c0301 -.changed.-> nISS_aab62c0301ledger_timestamp["ledger:timestamp"]
  nISS_135ca0a6fe["#5 period_cutoff<br/>83625.00 USD"]
  nRCP_091099(["RCP/091099"]) --> nISS_135ca0a6fe
  nISS_135ca0a6fe -.changed.-> nISS_135ca0a6feledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
