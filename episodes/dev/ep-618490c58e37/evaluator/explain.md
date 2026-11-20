# Episode ep-618490c58e37 (evaluator-only)

Period 2026-06-01T00:00:00-05:00 .. 2026-08-01T00:00:00-05:00 (end exclusive), company timezone UTC-05:00, base EUR, currencies EUR, GBP, JPY. Records: {'ledger_rows': 351, 'invoices': 86, 'payments': 65, 'documents': 151, 'fx_rates': 708}.

## 8 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | SI/008030, SI/066012 | 54220.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | duplicate_invoice | SI/068238, SI/081287 | 960.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 3 | payment_allocation (missing allocation) | RCP/055889, SI/074640 | 21409.81 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 4 | payment_allocation (partial allocation) | RCP/051681, SI/008673 | 22206.60 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (rate of the invoice date) | RCP/002888 | 135.45 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | fx_error (rate of the previous day) | RCP/080198 | 99423 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 7 | period_cutoff | SI/073779 | 38870.00 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 8 | period_cutoff | RCP/074428 | 55246.66 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_403974f668["#1 duplicate_invoice<br/>54220.00 EUR"]
  nSI_008030(["SI/008030"]) --> nISS_403974f668
  nSI_066012(["SI/066012"]) --> nISS_403974f668
  nISS_403974f668 -.changed.-> nISS_403974f668invoices_add["invoices:add"]
  nISS_403974f668 -.changed.-> nISS_403974f668ledger_add["ledger:add"]
  nISS_ecc0495363["#2 duplicate_invoice<br/>960.00 EUR"]
  nSI_068238(["SI/068238"]) --> nISS_ecc0495363
  nSI_081287(["SI/081287"]) --> nISS_ecc0495363
  nISS_ecc0495363 -.changed.-> nISS_ecc0495363invoices_add["invoices:add"]
  nISS_ecc0495363 -.changed.-> nISS_ecc0495363ledger_add["ledger:add"]
  nISS_f1d1099e41["#3 payment_allocation<br/>21409.81 GBP"]
  nRCP_055889(["RCP/055889"]) --> nISS_f1d1099e41
  nSI_074640(["SI/074640"]) --> nISS_f1d1099e41
  nISS_f1d1099e41 -.changed.-> nISS_f1d1099e41ledger_add["ledger:add"]
  nISS_f1d1099e41 -.changed.-> nISS_f1d1099e41ledger_remove["ledger:remove"]
  nISS_f1d1099e41 -.changed.-> nISS_f1d1099e41payments_invoice_refs["payments:invoice_refs"]
  nISS_a061d5355d["#4 payment_allocation<br/>22206.60 EUR"]
  nRCP_051681(["RCP/051681"]) --> nISS_a061d5355d
  nSI_008673(["SI/008673"]) --> nISS_a061d5355d
  nISS_a061d5355d -.changed.-> nISS_a061d5355dledger_add["ledger:add"]
  nISS_a061d5355d -.changed.-> nISS_a061d5355dledger_credit_minor["ledger:credit_minor"]
  nISS_a061d5355d -.changed.-> nISS_a061d5355dpayments_invoice_refs["payments:invoice_refs"]
  nISS_65be7d85f8["#5 fx_error<br/>135.45 EUR"]
  nRCP_002888(["RCP/002888"]) --> nISS_65be7d85f8
  nISS_65be7d85f8 -.changed.-> nISS_65be7d85f8ledger_credit_minor["ledger:credit_minor"]
  nISS_65be7d85f8 -.changed.-> nISS_65be7d85f8ledger_debit_minor["ledger:debit_minor"]
  nISS_044b435d32["#6 fx_error<br/>99423 JPY"]
  nRCP_080198(["RCP/080198"]) --> nISS_044b435d32
  nISS_044b435d32 -.changed.-> nISS_044b435d32ledger_credit_minor["ledger:credit_minor"]
  nISS_044b435d32 -.changed.-> nISS_044b435d32ledger_debit_minor["ledger:debit_minor"]
  nISS_a4ce4ba77e["#7 period_cutoff<br/>38870.00 EUR"]
  nSI_073779(["SI/073779"]) --> nISS_a4ce4ba77e
  nISS_a4ce4ba77e -.changed.-> nISS_a4ce4ba77eledger_timestamp["ledger:timestamp"]
  nISS_7bc4fd98e9["#8 period_cutoff<br/>55246.66 EUR"]
  nRCP_074428(["RCP/074428"]) --> nISS_7bc4fd98e9
  nISS_7bc4fd98e9 -.changed.-> nISS_7bc4fd98e9ledger_timestamp["ledger:timestamp"]
```

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
