# Episode ep-fc37abbc580a (evaluator-only)

Period 2026-05-01T00:00:00+08:00 .. 2026-08-01T00:00:00+08:00 (end exclusive), company timezone UTC+08:00, base GBP, currencies GBP, USD, KZT. Records: {'ledger_rows': 351, 'invoices': 91, 'payments': 65, 'documents': 156, 'fx_rates': 894}.

## 12 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | RCP/016884, SI/040460 | 1724658.70 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate taken for the UTC date instead of the local date) | RCP/016884 | 70.39 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | RCP/084635 | 6875939.61 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | RCP/084635 | 69.64 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | SI/012851, SI/069068 | 34515.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | SI/072635, SI/090204 | 86210.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 7 | payment_allocation (partial allocation) | RCP/044968, SI/019541 | 1759430.60 KZT | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 8 | payment_allocation (partial allocation) | RCP/007785, SI/056344 | 9943.50 GBP | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 9 | fx_error (rate of the invoice date) | RCP/028633 | 208.48 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 10 | fx_error (two digits of the rate swapped when keyed in) | RCP/073332 | 147218.19 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 11 | period_cutoff | SI/035305 | 75880.00 GBP | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 12 | period_cutoff | RCP/006721 | 34655.00 USD | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_291b36325d["#1 payment_allocation<br/>1724658.70 KZT"]
  nRCP_016884(["RCP/016884"]) --> nISS_291b36325d
  nSI_040460(["SI/040460"]) --> nISS_291b36325d
  nISS_291b36325d -.changed.-> nISS_291b36325dledger_add["ledger:add"]
  nISS_291b36325d -.changed.-> nISS_291b36325dledger_credit_minor["ledger:credit_minor"]
  nISS_291b36325d -.changed.-> nISS_291b36325dledger_debit_minor["ledger:debit_minor"]
  nISS_802f0bde2a["#2 fx_error<br/>70.39 USD"]
  nRCP_016884(["RCP/016884"]) --> nISS_802f0bde2a
  nISS_802f0bde2a -.changed.-> nISS_802f0bde2aledger_add["ledger:add"]
  nISS_802f0bde2a -.changed.-> nISS_802f0bde2aledger_credit_minor["ledger:credit_minor"]
  nISS_802f0bde2a -.changed.-> nISS_802f0bde2aledger_debit_minor["ledger:debit_minor"]
  nISS_6a52df5a62["#3 period_cutoff<br/>6875939.61 KZT"]
  nRCP_084635(["RCP/084635"]) --> nISS_6a52df5a62
  nISS_6a52df5a62 -.changed.-> nISS_6a52df5a62ledger_credit_minor["ledger:credit_minor"]
  nISS_6a52df5a62 -.changed.-> nISS_6a52df5a62ledger_debit_minor["ledger:debit_minor"]
  nISS_6a52df5a62 -.changed.-> nISS_6a52df5a62ledger_timestamp["ledger:timestamp"]
  nISS_538cbe877f["#4 fx_error<br/>69.64 USD"]
  nRCP_084635(["RCP/084635"]) --> nISS_538cbe877f
  nISS_538cbe877f -.changed.-> nISS_538cbe877fledger_credit_minor["ledger:credit_minor"]
  nISS_538cbe877f -.changed.-> nISS_538cbe877fledger_debit_minor["ledger:debit_minor"]
  nISS_538cbe877f -.changed.-> nISS_538cbe877fledger_timestamp["ledger:timestamp"]
  nISS_2e0323b77b["#5 duplicate_invoice<br/>34515.00 USD"]
  nSI_012851(["SI/012851"]) --> nISS_2e0323b77b
  nSI_069068(["SI/069068"]) --> nISS_2e0323b77b
  nISS_2e0323b77b -.changed.-> nISS_2e0323b77binvoices_add["invoices:add"]
  nISS_2e0323b77b -.changed.-> nISS_2e0323b77bledger_add["ledger:add"]
  nISS_0fa77fa9ff["#6 duplicate_invoice<br/>86210.00 USD"]
  nSI_072635(["SI/072635"]) --> nISS_0fa77fa9ff
  nSI_090204(["SI/090204"]) --> nISS_0fa77fa9ff
  nISS_0fa77fa9ff -.changed.-> nISS_0fa77fa9ffinvoices_add["invoices:add"]
  nISS_0fa77fa9ff -.changed.-> nISS_0fa77fa9ffledger_add["ledger:add"]
  nISS_081ff60319["#7 payment_allocation<br/>1759430.60 KZT"]
  nRCP_044968(["RCP/044968"]) --> nISS_081ff60319
  nSI_019541(["SI/019541"]) --> nISS_081ff60319
  nISS_081ff60319 -.changed.-> nISS_081ff60319ledger_add["ledger:add"]
  nISS_081ff60319 -.changed.-> nISS_081ff60319ledger_credit_minor["ledger:credit_minor"]
  nISS_081ff60319 -.changed.-> nISS_081ff60319ledger_debit_minor["ledger:debit_minor"]
  nISS_c6b048e838["#8 payment_allocation<br/>9943.50 GBP"]
  nRCP_007785(["RCP/007785"]) --> nISS_c6b048e838
  nSI_056344(["SI/056344"]) --> nISS_c6b048e838
  nISS_c6b048e838 -.changed.-> nISS_c6b048e838ledger_add["ledger:add"]
  nISS_c6b048e838 -.changed.-> nISS_c6b048e838ledger_credit_minor["ledger:credit_minor"]
  nISS_c6b048e838 -.changed.-> nISS_c6b048e838payments_invoice_refs["payments:invoice_refs"]
  nISS_cd37e09f45["#9 fx_error<br/>208.48 USD"]
  nRCP_028633(["RCP/028633"]) --> nISS_cd37e09f45
  nISS_cd37e09f45 -.changed.-> nISS_cd37e09f45ledger_credit_minor["ledger:credit_minor"]
  nISS_cd37e09f45 -.changed.-> nISS_cd37e09f45ledger_debit_minor["ledger:debit_minor"]
  nISS_f591dafb79["#10 fx_error<br/>147218.19 USD"]
  nRCP_073332(["RCP/073332"]) --> nISS_f591dafb79
  nISS_f591dafb79 -.changed.-> nISS_f591dafb79ledger_credit_minor["ledger:credit_minor"]
  nISS_f591dafb79 -.changed.-> nISS_f591dafb79ledger_debit_minor["ledger:debit_minor"]
  nISS_3594d39c31["#11 period_cutoff<br/>75880.00 GBP"]
  nSI_035305(["SI/035305"]) --> nISS_3594d39c31
  nISS_3594d39c31 -.changed.-> nISS_3594d39c31ledger_timestamp["ledger:timestamp"]
  nISS_44be4bf856["#12 period_cutoff<br/>34655.00 USD"]
  nRCP_006721(["RCP/006721"]) --> nISS_44be4bf856
  nISS_44be4bf856 -.changed.-> nISS_44be4bf856ledger_timestamp["ledger:timestamp"]
  nISS_291b36325d ==>|"partial_fx: causes"| nISS_802f0bde2a
  nISS_6a52df5a62 ==>|"cutoff_fx: causes"| nISS_538cbe877f
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
