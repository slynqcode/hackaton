# Episode ep-0a754439c92f (evaluator-only)

Period 2026-06-01T00:00:00+02:00 .. 2026-08-01T00:00:00+02:00 (end exclusive), company timezone UTC+02:00, base USD, currencies USD, EUR, GBP. Records: {'ledger_rows': 325, 'invoices': 84, 'payments': 57, 'documents': 141, 'fx_rates': 708}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | RCP/052229, SI/023691 | 8475.71 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate taken for the UTC date instead of the local date) | RCP/052229 | 51.82 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | RCP/075485 | 28945.42 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | RCP/075485 | 301.29 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | SI/068972, SI/085666 | 82410.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | SI/029172, SI/074494 | 9030.00 GBP | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |

## Causal graph

```mermaid
flowchart LR
  nISS_c4bfc3e089["#1 payment_allocation<br/>8475.71 GBP"]
  nRCP_052229(["RCP/052229"]) --> nISS_c4bfc3e089
  nSI_023691(["SI/023691"]) --> nISS_c4bfc3e089
  nISS_c4bfc3e089 -.changed.-> nISS_c4bfc3e089ledger_add["ledger:add"]
  nISS_c4bfc3e089 -.changed.-> nISS_c4bfc3e089ledger_credit_minor["ledger:credit_minor"]
  nISS_c4bfc3e089 -.changed.-> nISS_c4bfc3e089ledger_debit_minor["ledger:debit_minor"]
  nISS_4576948030["#2 fx_error<br/>51.82 USD"]
  nRCP_052229(["RCP/052229"]) --> nISS_4576948030
  nISS_4576948030 -.changed.-> nISS_4576948030ledger_add["ledger:add"]
  nISS_4576948030 -.changed.-> nISS_4576948030ledger_credit_minor["ledger:credit_minor"]
  nISS_4576948030 -.changed.-> nISS_4576948030ledger_debit_minor["ledger:debit_minor"]
  nISS_29df02f137["#3 period_cutoff<br/>28945.42 GBP"]
  nRCP_075485(["RCP/075485"]) --> nISS_29df02f137
  nISS_29df02f137 -.changed.-> nISS_29df02f137ledger_credit_minor["ledger:credit_minor"]
  nISS_29df02f137 -.changed.-> nISS_29df02f137ledger_debit_minor["ledger:debit_minor"]
  nISS_29df02f137 -.changed.-> nISS_29df02f137ledger_timestamp["ledger:timestamp"]
  nISS_acf1c31049["#4 fx_error<br/>301.29 USD"]
  nRCP_075485(["RCP/075485"]) --> nISS_acf1c31049
  nISS_acf1c31049 -.changed.-> nISS_acf1c31049ledger_credit_minor["ledger:credit_minor"]
  nISS_acf1c31049 -.changed.-> nISS_acf1c31049ledger_debit_minor["ledger:debit_minor"]
  nISS_acf1c31049 -.changed.-> nISS_acf1c31049ledger_timestamp["ledger:timestamp"]
  nISS_edb619e922["#5 duplicate_invoice<br/>82410.00 USD"]
  nSI_068972(["SI/068972"]) --> nISS_edb619e922
  nSI_085666(["SI/085666"]) --> nISS_edb619e922
  nISS_edb619e922 -.changed.-> nISS_edb619e922invoices_add["invoices:add"]
  nISS_edb619e922 -.changed.-> nISS_edb619e922ledger_add["ledger:add"]
  nISS_af21e3cff5["#6 duplicate_invoice<br/>9030.00 GBP"]
  nSI_029172(["SI/029172"]) --> nISS_af21e3cff5
  nSI_074494(["SI/074494"]) --> nISS_af21e3cff5
  nISS_af21e3cff5 -.changed.-> nISS_af21e3cff5invoices_add["invoices:add"]
  nISS_af21e3cff5 -.changed.-> nISS_af21e3cff5ledger_add["ledger:add"]
  nISS_c4bfc3e089 ==>|"partial_fx: causes"| nISS_4576948030
  nISS_29df02f137 ==>|"cutoff_fx: causes"| nISS_acf1c31049
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
