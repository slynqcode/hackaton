# Episode ep-b9630892e373 (evaluator-only)

Period 2026-01-01T00:00:00+01:00 .. 2026-02-01T00:00:00+01:00 (end exclusive), company timezone UTC+01:00, base USD, currencies USD, EUR, KZT. Records: {'ledger_rows': 339, 'invoices': 89, 'payments': 55, 'documents': 144, 'fx_rates': 528}.

## 12 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | RCP/019478, SI/057525 | 14921.74 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate taken for the UTC date instead of the local date) | RCP/019478 | 27.94 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | RCP/053934 | 44160464.36 KZT | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | RCP/053934 | 648.81 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | SI/011419, SI/087729 | 37105.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | SI/011001, SI/038278 | 2757260.00 KZT | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 7 | payment_allocation (partial allocation) | RCP/092316, SI/020902 | 6217.25 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 8 | payment_allocation (partial allocation) | RCP/019910, SI/063658 | 17191.39 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 9 | fx_error (two digits of the rate swapped when keyed in) | RCP/098484 | 2695377.60 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 10 | fx_error (two digits of the rate swapped when keyed in) | RCP/034576 | 37312.70 EUR | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 11 | period_cutoff | SI/081959 | 28570.00 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 12 | period_cutoff | RCP/063143 | 10565.73 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |

## Causal graph

```mermaid
flowchart LR
  nISS_d24c6570c0["#1 payment_allocation<br/>14921.74 USD"]
  nRCP_019478(["RCP/019478"]) --> nISS_d24c6570c0
  nSI_057525(["SI/057525"]) --> nISS_d24c6570c0
  nISS_d24c6570c0 -.changed.-> nISS_d24c6570c0ledger_add["ledger:add"]
  nISS_d24c6570c0 -.changed.-> nISS_d24c6570c0ledger_credit_minor["ledger:credit_minor"]
  nISS_d24c6570c0 -.changed.-> nISS_d24c6570c0ledger_debit_minor["ledger:debit_minor"]
  nISS_12540f6e63["#2 fx_error<br/>27.94 EUR"]
  nRCP_019478(["RCP/019478"]) --> nISS_12540f6e63
  nISS_12540f6e63 -.changed.-> nISS_12540f6e63ledger_add["ledger:add"]
  nISS_12540f6e63 -.changed.-> nISS_12540f6e63ledger_credit_minor["ledger:credit_minor"]
  nISS_12540f6e63 -.changed.-> nISS_12540f6e63ledger_debit_minor["ledger:debit_minor"]
  nISS_bccbc2078b["#3 period_cutoff<br/>44160464.36 KZT"]
  nRCP_053934(["RCP/053934"]) --> nISS_bccbc2078b
  nISS_bccbc2078b -.changed.-> nISS_bccbc2078bledger_credit_minor["ledger:credit_minor"]
  nISS_bccbc2078b -.changed.-> nISS_bccbc2078bledger_debit_minor["ledger:debit_minor"]
  nISS_bccbc2078b -.changed.-> nISS_bccbc2078bledger_timestamp["ledger:timestamp"]
  nISS_7d0320112f["#4 fx_error<br/>648.81 EUR"]
  nRCP_053934(["RCP/053934"]) --> nISS_7d0320112f
  nISS_7d0320112f -.changed.-> nISS_7d0320112fledger_credit_minor["ledger:credit_minor"]
  nISS_7d0320112f -.changed.-> nISS_7d0320112fledger_debit_minor["ledger:debit_minor"]
  nISS_7d0320112f -.changed.-> nISS_7d0320112fledger_timestamp["ledger:timestamp"]
  nISS_d5ff8361f2["#5 duplicate_invoice<br/>37105.00 USD"]
  nSI_011419(["SI/011419"]) --> nISS_d5ff8361f2
  nSI_087729(["SI/087729"]) --> nISS_d5ff8361f2
  nISS_d5ff8361f2 -.changed.-> nISS_d5ff8361f2invoices_add["invoices:add"]
  nISS_d5ff8361f2 -.changed.-> nISS_d5ff8361f2ledger_add["ledger:add"]
  nISS_f74d773f40["#6 duplicate_invoice<br/>2757260.00 KZT"]
  nSI_011001(["SI/011001"]) --> nISS_f74d773f40
  nSI_038278(["SI/038278"]) --> nISS_f74d773f40
  nISS_f74d773f40 -.changed.-> nISS_f74d773f40invoices_add["invoices:add"]
  nISS_f74d773f40 -.changed.-> nISS_f74d773f40ledger_add["ledger:add"]
  nISS_b5d3259836["#7 payment_allocation<br/>6217.25 EUR"]
  nRCP_092316(["RCP/092316"]) --> nISS_b5d3259836
  nSI_020902(["SI/020902"]) --> nISS_b5d3259836
  nISS_b5d3259836 -.changed.-> nISS_b5d3259836ledger_add["ledger:add"]
  nISS_b5d3259836 -.changed.-> nISS_b5d3259836ledger_credit_minor["ledger:credit_minor"]
  nISS_b5d3259836 -.changed.-> nISS_b5d3259836ledger_debit_minor["ledger:debit_minor"]
  nISS_f15fbcf427["#8 payment_allocation<br/>17191.39 USD"]
  nRCP_019910(["RCP/019910"]) --> nISS_f15fbcf427
  nSI_063658(["SI/063658"]) --> nISS_f15fbcf427
  nISS_f15fbcf427 -.changed.-> nISS_f15fbcf427ledger_add["ledger:add"]
  nISS_f15fbcf427 -.changed.-> nISS_f15fbcf427ledger_credit_minor["ledger:credit_minor"]
  nISS_f15fbcf427 -.changed.-> nISS_f15fbcf427ledger_debit_minor["ledger:debit_minor"]
  nISS_4407919092["#9 fx_error<br/>2695377.60 KZT"]
  nRCP_098484(["RCP/098484"]) --> nISS_4407919092
  nISS_4407919092 -.changed.-> nISS_4407919092ledger_credit_minor["ledger:credit_minor"]
  nISS_4407919092 -.changed.-> nISS_4407919092ledger_debit_minor["ledger:debit_minor"]
  nISS_679e30c4f7["#10 fx_error<br/>37312.70 EUR"]
  nRCP_034576(["RCP/034576"]) --> nISS_679e30c4f7
  nISS_679e30c4f7 -.changed.-> nISS_679e30c4f7ledger_credit_minor["ledger:credit_minor"]
  nISS_679e30c4f7 -.changed.-> nISS_679e30c4f7ledger_debit_minor["ledger:debit_minor"]
  nISS_bd99b1e029["#11 period_cutoff<br/>28570.00 EUR"]
  nSI_081959(["SI/081959"]) --> nISS_bd99b1e029
  nISS_bd99b1e029 -.changed.-> nISS_bd99b1e029ledger_timestamp["ledger:timestamp"]
  nISS_6637311680["#12 period_cutoff<br/>10565.73 EUR"]
  nRCP_063143(["RCP/063143"]) --> nISS_6637311680
  nISS_6637311680 -.changed.-> nISS_6637311680ledger_timestamp["ledger:timestamp"]
  nISS_d24c6570c0 ==>|"partial_fx: causes"| nISS_12540f6e63
  nISS_bccbc2078b ==>|"cutoff_fx: causes"| nISS_7d0320112f
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
