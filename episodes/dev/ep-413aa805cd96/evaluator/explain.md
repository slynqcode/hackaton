# Episode ep-413aa805cd96 (evaluator-only)

Period 2026-08-01T00:00:00-03:00 .. 2026-10-01T00:00:00-03:00 (end exclusive), company timezone UTC-03:00, base JPY, currencies JPY, KZT, GBP. Records: {'ledger_rows': 295, 'invoices': 84, 'payments': 48, 'documents': 132, 'fx_rates': 708}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | period_cutoff | PAY-20924 | 25699.03 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 2 | fx_error (rate of the (wrong) posting date) | PAY-20924 | 11864.76 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | duplicate_invoice | INV-83910, INV-96713 | 14478905.00 KZT | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 4 | payment_allocation (partial allocation) | INV-97581, PAY-61554 | 656052 JPY | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (rate of the previous day) | PAY-94102 | 24644 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | period_cutoff | PAY-09433 | 25612963.72 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_c8845e2940["#1 period_cutoff<br/>25699.03 GBP"]
  nPAY_20924(["PAY-20924"]) --> nISS_c8845e2940
  nISS_c8845e2940 -.changed.-> nISS_c8845e2940ledger_credit_minor["ledger:credit_minor"]
  nISS_c8845e2940 -.changed.-> nISS_c8845e2940ledger_debit_minor["ledger:debit_minor"]
  nISS_c8845e2940 -.changed.-> nISS_c8845e2940ledger_timestamp["ledger:timestamp"]
  nISS_b066224e9f["#2 fx_error<br/>11864.76 KZT"]
  nPAY_20924(["PAY-20924"]) --> nISS_b066224e9f
  nISS_b066224e9f -.changed.-> nISS_b066224e9fledger_credit_minor["ledger:credit_minor"]
  nISS_b066224e9f -.changed.-> nISS_b066224e9fledger_debit_minor["ledger:debit_minor"]
  nISS_b066224e9f -.changed.-> nISS_b066224e9fledger_timestamp["ledger:timestamp"]
  nISS_0bc0b573c1["#3 duplicate_invoice<br/>14478905.00 KZT"]
  nINV_83910(["INV-83910"]) --> nISS_0bc0b573c1
  nINV_96713(["INV-96713"]) --> nISS_0bc0b573c1
  nISS_0bc0b573c1 -.changed.-> nISS_0bc0b573c1invoices_add["invoices:add"]
  nISS_0bc0b573c1 -.changed.-> nISS_0bc0b573c1ledger_add["ledger:add"]
  nISS_1dc209d51e["#4 payment_allocation<br/>656052 JPY"]
  nINV_97581(["INV-97581"]) --> nISS_1dc209d51e
  nPAY_61554(["PAY-61554"]) --> nISS_1dc209d51e
  nISS_1dc209d51e -.changed.-> nISS_1dc209d51eledger_add["ledger:add"]
  nISS_1dc209d51e -.changed.-> nISS_1dc209d51eledger_credit_minor["ledger:credit_minor"]
  nISS_1dc209d51e -.changed.-> nISS_1dc209d51epayments_invoice_refs["payments:invoice_refs"]
  nISS_ee2300ef7f["#5 fx_error<br/>24644 JPY"]
  nPAY_94102(["PAY-94102"]) --> nISS_ee2300ef7f
  nISS_ee2300ef7f -.changed.-> nISS_ee2300ef7fledger_credit_minor["ledger:credit_minor"]
  nISS_ee2300ef7f -.changed.-> nISS_ee2300ef7fledger_debit_minor["ledger:debit_minor"]
  nISS_e8bdd7b03d["#6 period_cutoff<br/>25612963.72 KZT"]
  nPAY_09433(["PAY-09433"]) --> nISS_e8bdd7b03d
  nISS_e8bdd7b03d -.changed.-> nISS_e8bdd7b03dledger_timestamp["ledger:timestamp"]
  nISS_c8845e2940 ==>|"cutoff_fx: causes"| nISS_b066224e9f
```

## Interacting errors

- **cutoff_fx**: misposted entry converted at the rate of its (wrong) posting date.

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
