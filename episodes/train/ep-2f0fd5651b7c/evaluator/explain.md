# Episode ep-2f0fd5651b7c (evaluator-only)

Period 2026-05-01T00:00:00+01:00 .. 2026-06-01T00:00:00+01:00 (end exclusive), company timezone UTC+01:00, base EUR, currencies EUR, GBP, KZT. Records: {'ledger_rows': 320, 'invoices': 87, 'payments': 53, 'documents': 140, 'fx_rates': 528}.

## 12 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | RCP/089385, SI/036713 | 29384.48 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate taken for the UTC date instead of the local date) | RCP/089385 | 280.12 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | RCP/035247 | 10737.60 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | RCP/035247 | 22631.50 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | SI/007780, SI/010429 | 4810.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | SI/028104, SI/044672 | 52575.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 7 | payment_allocation (missing allocation) | RCP/075570, SI/054945 | 28250.00 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 8 | payment_allocation (partial allocation) | RCP/051876, SI/034819 | 10832.40 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 9 | fx_error (rate of the previous day) | RCP/036572 | 177.90 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 10 | fx_error (rate of the invoice date) | RCP/040265 | 215337.38 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 11 | period_cutoff | RCP/008501 | 8575.00 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 12 | period_cutoff | RCP/049527 | 16365.93 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_a5e844928b["#1 payment_allocation<br/>29384.48 GBP"]
  nRCP_089385(["RCP/089385"]) --> nISS_a5e844928b
  nSI_036713(["SI/036713"]) --> nISS_a5e844928b
  nISS_a5e844928b -.changed.-> nISS_a5e844928bledger_add["ledger:add"]
  nISS_a5e844928b -.changed.-> nISS_a5e844928bledger_credit_minor["ledger:credit_minor"]
  nISS_a5e844928b -.changed.-> nISS_a5e844928bledger_debit_minor["ledger:debit_minor"]
  nISS_40ce4f15c2["#2 fx_error<br/>280.12 EUR"]
  nRCP_089385(["RCP/089385"]) --> nISS_40ce4f15c2
  nISS_40ce4f15c2 -.changed.-> nISS_40ce4f15c2ledger_add["ledger:add"]
  nISS_40ce4f15c2 -.changed.-> nISS_40ce4f15c2ledger_credit_minor["ledger:credit_minor"]
  nISS_40ce4f15c2 -.changed.-> nISS_40ce4f15c2ledger_debit_minor["ledger:debit_minor"]
  nISS_d9f33da926["#3 period_cutoff<br/>10737.60 EUR"]
  nRCP_035247(["RCP/035247"]) --> nISS_d9f33da926
  nISS_d9f33da926 -.changed.-> nISS_d9f33da926ledger_credit_minor["ledger:credit_minor"]
  nISS_d9f33da926 -.changed.-> nISS_d9f33da926ledger_debit_minor["ledger:debit_minor"]
  nISS_d9f33da926 -.changed.-> nISS_d9f33da926ledger_timestamp["ledger:timestamp"]
  nISS_9c7f21c063["#4 fx_error<br/>22631.50 KZT"]
  nRCP_035247(["RCP/035247"]) --> nISS_9c7f21c063
  nISS_9c7f21c063 -.changed.-> nISS_9c7f21c063ledger_credit_minor["ledger:credit_minor"]
  nISS_9c7f21c063 -.changed.-> nISS_9c7f21c063ledger_debit_minor["ledger:debit_minor"]
  nISS_9c7f21c063 -.changed.-> nISS_9c7f21c063ledger_timestamp["ledger:timestamp"]
  nISS_e7ffaf4e5a["#5 duplicate_invoice<br/>4810.00 EUR"]
  nSI_007780(["SI/007780"]) --> nISS_e7ffaf4e5a
  nSI_010429(["SI/010429"]) --> nISS_e7ffaf4e5a
  nISS_e7ffaf4e5a -.changed.-> nISS_e7ffaf4e5ainvoices_add["invoices:add"]
  nISS_e7ffaf4e5a -.changed.-> nISS_e7ffaf4e5aledger_add["ledger:add"]
  nISS_fe9342b19d["#6 duplicate_invoice<br/>52575.00 EUR"]
  nSI_028104(["SI/028104"]) --> nISS_fe9342b19d
  nSI_044672(["SI/044672"]) --> nISS_fe9342b19d
  nISS_fe9342b19d -.changed.-> nISS_fe9342b19dinvoices_add["invoices:add"]
  nISS_fe9342b19d -.changed.-> nISS_fe9342b19dledger_add["ledger:add"]
  nISS_8c2a1f9b3a["#7 payment_allocation<br/>28250.00 EUR"]
  nRCP_075570(["RCP/075570"]) --> nISS_8c2a1f9b3a
  nSI_054945(["SI/054945"]) --> nISS_8c2a1f9b3a
  nISS_8c2a1f9b3a -.changed.-> nISS_8c2a1f9b3aledger_add["ledger:add"]
  nISS_8c2a1f9b3a -.changed.-> nISS_8c2a1f9b3aledger_remove["ledger:remove"]
  nISS_8c2a1f9b3a -.changed.-> nISS_8c2a1f9b3apayments_invoice_refs["payments:invoice_refs"]
  nISS_1ef5205ffc["#8 payment_allocation<br/>10832.40 GBP"]
  nRCP_051876(["RCP/051876"]) --> nISS_1ef5205ffc
  nSI_034819(["SI/034819"]) --> nISS_1ef5205ffc
  nISS_1ef5205ffc -.changed.-> nISS_1ef5205ffcledger_add["ledger:add"]
  nISS_1ef5205ffc -.changed.-> nISS_1ef5205ffcledger_credit_minor["ledger:credit_minor"]
  nISS_1ef5205ffc -.changed.-> nISS_1ef5205ffcpayments_invoice_refs["payments:invoice_refs"]
  nISS_a1b5bb8a91["#9 fx_error<br/>177.90 EUR"]
  nRCP_036572(["RCP/036572"]) --> nISS_a1b5bb8a91
  nISS_a1b5bb8a91 -.changed.-> nISS_a1b5bb8a91ledger_credit_minor["ledger:credit_minor"]
  nISS_a1b5bb8a91 -.changed.-> nISS_a1b5bb8a91ledger_debit_minor["ledger:debit_minor"]
  nISS_7155d9ecb7["#10 fx_error<br/>215337.38 KZT"]
  nRCP_040265(["RCP/040265"]) --> nISS_7155d9ecb7
  nISS_7155d9ecb7 -.changed.-> nISS_7155d9ecb7ledger_credit_minor["ledger:credit_minor"]
  nISS_7155d9ecb7 -.changed.-> nISS_7155d9ecb7ledger_debit_minor["ledger:debit_minor"]
  nISS_8d4463089a["#11 period_cutoff<br/>8575.00 GBP"]
  nRCP_008501(["RCP/008501"]) --> nISS_8d4463089a
  nISS_8d4463089a -.changed.-> nISS_8d4463089aledger_timestamp["ledger:timestamp"]
  nISS_f0a8c49f67["#12 period_cutoff<br/>16365.93 EUR"]
  nRCP_049527(["RCP/049527"]) --> nISS_f0a8c49f67
  nISS_f0a8c49f67 -.changed.-> nISS_f0a8c49f67ledger_timestamp["ledger:timestamp"]
  nISS_a5e844928b ==>|"partial_fx: causes"| nISS_40ce4f15c2
  nISS_d9f33da926 ==>|"cutoff_fx: causes"| nISS_9c7f21c063
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
