# Episode ep-ad76b7669d46 (evaluator-only)

Period 2026-06-01T00:00:00+05:30 .. 2026-09-01T00:00:00+05:30 (end exclusive), company timezone UTC+05:30, base GBP, currencies GBP, KZT, JPY. Records: {'ledger_rows': 364, 'invoices': 92, 'payments': 65, 'documents': 157, 'fx_rates': 894}.

## 12 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | RCP/070435, SI/062243 | 12890343.06 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate taken for the UTC date instead of the local date) | RCP/070435 | 114.76 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | RCP/002442 | 1096817.11 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | RCP/002442 | 16.63 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | SI/036940, SI/098320 | 3873775 JPY | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | SI/043026, SI/062248 | 34303660.00 KZT | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 7 | payment_allocation (missing allocation) | RCP/085882, SI/092151 | 984888.63 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 8 | payment_allocation (partial allocation) | RCP/009686, SI/096108 | 3038.40 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 9 | fx_error (rate of the previous day) | RCP/040115 | 481.87 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 10 | fx_error (rate of the invoice date) | RCP/099910 | 76.85 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 11 | period_cutoff | RCP/080893 | 13075.00 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 12 | period_cutoff | RCP/022851 | 11621038.41 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_b259153add["#1 payment_allocation<br/>12890343.06 KZT"]
  nRCP_070435(["RCP/070435"]) --> nISS_b259153add
  nSI_062243(["SI/062243"]) --> nISS_b259153add
  nISS_b259153add -.changed.-> nISS_b259153addledger_add["ledger:add"]
  nISS_b259153add -.changed.-> nISS_b259153addledger_credit_minor["ledger:credit_minor"]
  nISS_b259153add -.changed.-> nISS_b259153addledger_debit_minor["ledger:debit_minor"]
  nISS_b94e226072["#2 fx_error<br/>114.76 GBP"]
  nRCP_070435(["RCP/070435"]) --> nISS_b94e226072
  nISS_b94e226072 -.changed.-> nISS_b94e226072ledger_add["ledger:add"]
  nISS_b94e226072 -.changed.-> nISS_b94e226072ledger_credit_minor["ledger:credit_minor"]
  nISS_b94e226072 -.changed.-> nISS_b94e226072ledger_debit_minor["ledger:debit_minor"]
  nISS_e45eec18e7["#3 period_cutoff<br/>1096817.11 KZT"]
  nRCP_002442(["RCP/002442"]) --> nISS_e45eec18e7
  nISS_e45eec18e7 -.changed.-> nISS_e45eec18e7ledger_credit_minor["ledger:credit_minor"]
  nISS_e45eec18e7 -.changed.-> nISS_e45eec18e7ledger_debit_minor["ledger:debit_minor"]
  nISS_e45eec18e7 -.changed.-> nISS_e45eec18e7ledger_timestamp["ledger:timestamp"]
  nISS_3333294a7c["#4 fx_error<br/>16.63 GBP"]
  nRCP_002442(["RCP/002442"]) --> nISS_3333294a7c
  nISS_3333294a7c -.changed.-> nISS_3333294a7cledger_credit_minor["ledger:credit_minor"]
  nISS_3333294a7c -.changed.-> nISS_3333294a7cledger_debit_minor["ledger:debit_minor"]
  nISS_3333294a7c -.changed.-> nISS_3333294a7cledger_timestamp["ledger:timestamp"]
  nISS_8382a59748["#5 duplicate_invoice<br/>3873775 JPY"]
  nSI_036940(["SI/036940"]) --> nISS_8382a59748
  nSI_098320(["SI/098320"]) --> nISS_8382a59748
  nISS_8382a59748 -.changed.-> nISS_8382a59748invoices_add["invoices:add"]
  nISS_8382a59748 -.changed.-> nISS_8382a59748ledger_add["ledger:add"]
  nISS_8d174dbff7["#6 duplicate_invoice<br/>34303660.00 KZT"]
  nSI_043026(["SI/043026"]) --> nISS_8d174dbff7
  nSI_062248(["SI/062248"]) --> nISS_8d174dbff7
  nISS_8d174dbff7 -.changed.-> nISS_8d174dbff7invoices_add["invoices:add"]
  nISS_8d174dbff7 -.changed.-> nISS_8d174dbff7ledger_add["ledger:add"]
  nISS_5dee089b5e["#7 payment_allocation<br/>984888.63 KZT"]
  nRCP_085882(["RCP/085882"]) --> nISS_5dee089b5e
  nSI_092151(["SI/092151"]) --> nISS_5dee089b5e
  nISS_5dee089b5e -.changed.-> nISS_5dee089b5eledger_add["ledger:add"]
  nISS_5dee089b5e -.changed.-> nISS_5dee089b5eledger_remove["ledger:remove"]
  nISS_5dee089b5e -.changed.-> nISS_5dee089b5epayments_invoice_refs["payments:invoice_refs"]
  nISS_9cbdb07bb3["#8 payment_allocation<br/>3038.40 GBP"]
  nRCP_009686(["RCP/009686"]) --> nISS_9cbdb07bb3
  nSI_096108(["SI/096108"]) --> nISS_9cbdb07bb3
  nISS_9cbdb07bb3 -.changed.-> nISS_9cbdb07bb3ledger_add["ledger:add"]
  nISS_9cbdb07bb3 -.changed.-> nISS_9cbdb07bb3ledger_credit_minor["ledger:credit_minor"]
  nISS_9cbdb07bb3 -.changed.-> nISS_9cbdb07bb3payments_invoice_refs["payments:invoice_refs"]
  nISS_b049f9b91e["#9 fx_error<br/>481.87 GBP"]
  nRCP_040115(["RCP/040115"]) --> nISS_b049f9b91e
  nISS_b049f9b91e -.changed.-> nISS_b049f9b91eledger_credit_minor["ledger:credit_minor"]
  nISS_b049f9b91e -.changed.-> nISS_b049f9b91eledger_debit_minor["ledger:debit_minor"]
  nISS_6769423b9a["#10 fx_error<br/>76.85 GBP"]
  nRCP_099910(["RCP/099910"]) --> nISS_6769423b9a
  nISS_6769423b9a -.changed.-> nISS_6769423b9aledger_credit_minor["ledger:credit_minor"]
  nISS_6769423b9a -.changed.-> nISS_6769423b9aledger_debit_minor["ledger:debit_minor"]
  nISS_a16abc5fc8["#11 period_cutoff<br/>13075.00 GBP"]
  nRCP_080893(["RCP/080893"]) --> nISS_a16abc5fc8
  nISS_a16abc5fc8 -.changed.-> nISS_a16abc5fc8ledger_timestamp["ledger:timestamp"]
  nISS_0ed0210d23["#12 period_cutoff<br/>11621038.41 KZT"]
  nRCP_022851(["RCP/022851"]) --> nISS_0ed0210d23
  nISS_0ed0210d23 -.changed.-> nISS_0ed0210d23ledger_timestamp["ledger:timestamp"]
  nISS_b259153add ==>|"partial_fx: causes"| nISS_b94e226072
  nISS_e45eec18e7 ==>|"cutoff_fx: causes"| nISS_3333294a7c
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
