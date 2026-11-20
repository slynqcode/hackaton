# Episode ep-449fb060d047 (evaluator-only)

Period 2026-06-01T00:00:00-05:00 .. 2026-08-01T00:00:00-05:00 (end exclusive), company timezone UTC-05:00, base EUR, currencies EUR, GBP, JPY. Records: {'ledger_rows': 353, 'invoices': 86, 'payments': 65, 'documents': 151, 'fx_rates': 708}.

## 8 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | duplicate_invoice | SI/071273, SI/075880 | 38225.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 2 | duplicate_invoice | SI/035985, SI/043765 | 35680.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 3 | payment_allocation (missing allocation) | RCP/012048, SI/056019 | 5220.00 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 4 | payment_allocation (partial allocation) | RCP/055889, SI/074640 | 5566.56 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 5 | fx_error (rate of the invoice date) | RCP/096011 | 1.46 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 6 | fx_error (rate of the previous day) | RCP/080198 | 99423 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 7 | period_cutoff | SI/008679 | 20590.00 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 8 | period_cutoff | RCP/098695 | 48505.00 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_403974f668["#1 duplicate_invoice<br/>38225.00 EUR"]
  nSI_071273(["SI/071273"]) --> nISS_403974f668
  nSI_075880(["SI/075880"]) --> nISS_403974f668
  nISS_403974f668 -.changed.-> nISS_403974f668invoices_add["invoices:add"]
  nISS_403974f668 -.changed.-> nISS_403974f668ledger_add["ledger:add"]
  nISS_ecc0495363["#2 duplicate_invoice<br/>35680.00 EUR"]
  nSI_035985(["SI/035985"]) --> nISS_ecc0495363
  nSI_043765(["SI/043765"]) --> nISS_ecc0495363
  nISS_ecc0495363 -.changed.-> nISS_ecc0495363invoices_add["invoices:add"]
  nISS_ecc0495363 -.changed.-> nISS_ecc0495363ledger_add["ledger:add"]
  nISS_f1d1099e41["#3 payment_allocation<br/>5220.00 EUR"]
  nRCP_012048(["RCP/012048"]) --> nISS_f1d1099e41
  nSI_056019(["SI/056019"]) --> nISS_f1d1099e41
  nISS_f1d1099e41 -.changed.-> nISS_f1d1099e41ledger_add["ledger:add"]
  nISS_f1d1099e41 -.changed.-> nISS_f1d1099e41ledger_remove["ledger:remove"]
  nISS_f1d1099e41 -.changed.-> nISS_f1d1099e41payments_invoice_refs["payments:invoice_refs"]
  nISS_a061d5355d["#4 payment_allocation<br/>5566.56 GBP"]
  nRCP_055889(["RCP/055889"]) --> nISS_a061d5355d
  nSI_074640(["SI/074640"]) --> nISS_a061d5355d
  nISS_a061d5355d -.changed.-> nISS_a061d5355dledger_add["ledger:add"]
  nISS_a061d5355d -.changed.-> nISS_a061d5355dledger_credit_minor["ledger:credit_minor"]
  nISS_a061d5355d -.changed.-> nISS_a061d5355dledger_debit_minor["ledger:debit_minor"]
  nISS_65be7d85f8["#5 fx_error<br/>1.46 EUR"]
  nRCP_096011(["RCP/096011"]) --> nISS_65be7d85f8
  nISS_65be7d85f8 -.changed.-> nISS_65be7d85f8ledger_credit_minor["ledger:credit_minor"]
  nISS_65be7d85f8 -.changed.-> nISS_65be7d85f8ledger_debit_minor["ledger:debit_minor"]
  nISS_044b435d32["#6 fx_error<br/>99423 JPY"]
  nRCP_080198(["RCP/080198"]) --> nISS_044b435d32
  nISS_044b435d32 -.changed.-> nISS_044b435d32ledger_credit_minor["ledger:credit_minor"]
  nISS_044b435d32 -.changed.-> nISS_044b435d32ledger_debit_minor["ledger:debit_minor"]
  nISS_a4ce4ba77e["#7 period_cutoff<br/>20590.00 EUR"]
  nSI_008679(["SI/008679"]) --> nISS_a4ce4ba77e
  nISS_a4ce4ba77e -.changed.-> nISS_a4ce4ba77eledger_timestamp["ledger:timestamp"]
  nISS_7bc4fd98e9["#8 period_cutoff<br/>48505.00 EUR"]
  nRCP_098695(["RCP/098695"]) --> nISS_7bc4fd98e9
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
