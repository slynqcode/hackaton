# Episode ep-963c60db9972 (evaluator-only)

Period 2026-06-01T00:00:00-07:00 .. 2026-08-01T00:00:00-07:00 (end exclusive), company timezone UTC-07:00, base USD, currencies USD, GBP, KZT. Records: {'ledger_rows': 354, 'invoices': 91, 'payments': 63, 'documents': 154, 'fx_rates': 708}.

## 12 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | F-66824, P-41479 | 3068905.26 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate taken for the UTC date instead of the local date) | P-41479 | 48.49 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | P-29829 | 32023179.86 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | P-29829 | 397.57 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | F-31904, F-63890 | 66295.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | F-43619, F-55924 | 1305.00 GBP | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 7 | payment_allocation (partial allocation) | F-57303, P-05981 | 17823193.86 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 8 | payment_allocation (missing allocation) | F-99852, P-22067 | 46855.00 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 9 | fx_error (rate of the invoice date) | P-93649 | 466.76 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 10 | fx_error (rate taken for the UTC date instead of the local date) | P-49860 | 69004.01 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 11 | period_cutoff | F-65534 | 5500.00 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 12 | period_cutoff | P-72854 | 1049052.98 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_d150bc419e["#1 payment_allocation<br/>3068905.26 KZT"]
  nF_66824(["F-66824"]) --> nISS_d150bc419e
  nP_41479(["P-41479"]) --> nISS_d150bc419e
  nISS_d150bc419e -.changed.-> nISS_d150bc419eledger_add["ledger:add"]
  nISS_d150bc419e -.changed.-> nISS_d150bc419eledger_credit_minor["ledger:credit_minor"]
  nISS_d150bc419e -.changed.-> nISS_d150bc419eledger_debit_minor["ledger:debit_minor"]
  nISS_3ff9d37832["#2 fx_error<br/>48.49 USD"]
  nP_41479(["P-41479"]) --> nISS_3ff9d37832
  nISS_3ff9d37832 -.changed.-> nISS_3ff9d37832ledger_add["ledger:add"]
  nISS_3ff9d37832 -.changed.-> nISS_3ff9d37832ledger_credit_minor["ledger:credit_minor"]
  nISS_3ff9d37832 -.changed.-> nISS_3ff9d37832ledger_debit_minor["ledger:debit_minor"]
  nISS_aa3fd6a805["#3 period_cutoff<br/>32023179.86 KZT"]
  nP_29829(["P-29829"]) --> nISS_aa3fd6a805
  nISS_aa3fd6a805 -.changed.-> nISS_aa3fd6a805ledger_credit_minor["ledger:credit_minor"]
  nISS_aa3fd6a805 -.changed.-> nISS_aa3fd6a805ledger_debit_minor["ledger:debit_minor"]
  nISS_aa3fd6a805 -.changed.-> nISS_aa3fd6a805ledger_timestamp["ledger:timestamp"]
  nISS_964b01c23c["#4 fx_error<br/>397.57 USD"]
  nP_29829(["P-29829"]) --> nISS_964b01c23c
  nISS_964b01c23c -.changed.-> nISS_964b01c23cledger_credit_minor["ledger:credit_minor"]
  nISS_964b01c23c -.changed.-> nISS_964b01c23cledger_debit_minor["ledger:debit_minor"]
  nISS_964b01c23c -.changed.-> nISS_964b01c23cledger_timestamp["ledger:timestamp"]
  nISS_d820fcc672["#5 duplicate_invoice<br/>66295.00 USD"]
  nF_31904(["F-31904"]) --> nISS_d820fcc672
  nF_63890(["F-63890"]) --> nISS_d820fcc672
  nISS_d820fcc672 -.changed.-> nISS_d820fcc672invoices_add["invoices:add"]
  nISS_d820fcc672 -.changed.-> nISS_d820fcc672ledger_add["ledger:add"]
  nISS_22f6fc9ec4["#6 duplicate_invoice<br/>1305.00 GBP"]
  nF_43619(["F-43619"]) --> nISS_22f6fc9ec4
  nF_55924(["F-55924"]) --> nISS_22f6fc9ec4
  nISS_22f6fc9ec4 -.changed.-> nISS_22f6fc9ec4invoices_add["invoices:add"]
  nISS_22f6fc9ec4 -.changed.-> nISS_22f6fc9ec4ledger_add["ledger:add"]
  nISS_fe14feb52b["#7 payment_allocation<br/>17823193.86 KZT"]
  nF_57303(["F-57303"]) --> nISS_fe14feb52b
  nP_05981(["P-05981"]) --> nISS_fe14feb52b
  nISS_fe14feb52b -.changed.-> nISS_fe14feb52bledger_add["ledger:add"]
  nISS_fe14feb52b -.changed.-> nISS_fe14feb52bledger_credit_minor["ledger:credit_minor"]
  nISS_fe14feb52b -.changed.-> nISS_fe14feb52bledger_debit_minor["ledger:debit_minor"]
  nISS_8d02f6e6f7["#8 payment_allocation<br/>46855.00 GBP"]
  nF_99852(["F-99852"]) --> nISS_8d02f6e6f7
  nP_22067(["P-22067"]) --> nISS_8d02f6e6f7
  nISS_8d02f6e6f7 -.changed.-> nISS_8d02f6e6f7ledger_add["ledger:add"]
  nISS_8d02f6e6f7 -.changed.-> nISS_8d02f6e6f7ledger_remove["ledger:remove"]
  nISS_8d02f6e6f7 -.changed.-> nISS_8d02f6e6f7payments_invoice_refs["payments:invoice_refs"]
  nISS_c719b190df["#9 fx_error<br/>466.76 USD"]
  nP_93649(["P-93649"]) --> nISS_c719b190df
  nISS_c719b190df -.changed.-> nISS_c719b190dfledger_credit_minor["ledger:credit_minor"]
  nISS_c719b190df -.changed.-> nISS_c719b190dfledger_debit_minor["ledger:debit_minor"]
  nISS_bc4ebd8805["#10 fx_error<br/>69004.01 KZT"]
  nP_49860(["P-49860"]) --> nISS_bc4ebd8805
  nISS_bc4ebd8805 -.changed.-> nISS_bc4ebd8805ledger_credit_minor["ledger:credit_minor"]
  nISS_bc4ebd8805 -.changed.-> nISS_bc4ebd8805ledger_debit_minor["ledger:debit_minor"]
  nISS_6da95ed092["#11 period_cutoff<br/>5500.00 GBP"]
  nF_65534(["F-65534"]) --> nISS_6da95ed092
  nISS_6da95ed092 -.changed.-> nISS_6da95ed092ledger_timestamp["ledger:timestamp"]
  nISS_1a9045aa53["#12 period_cutoff<br/>1049052.98 KZT"]
  nP_72854(["P-72854"]) --> nISS_1a9045aa53
  nISS_1a9045aa53 -.changed.-> nISS_1a9045aa53ledger_timestamp["ledger:timestamp"]
  nISS_d150bc419e ==>|"partial_fx: causes"| nISS_3ff9d37832
  nISS_aa3fd6a805 ==>|"cutoff_fx: causes"| nISS_964b01c23c
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
