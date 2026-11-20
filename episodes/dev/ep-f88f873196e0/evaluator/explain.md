# Episode ep-f88f873196e0 (evaluator-only)

Period 2026-04-01T00:00:00+00:00 .. 2026-06-01T00:00:00+00:00 (end exclusive), company timezone UTC+00:00, base KZT, currencies KZT, USD, JPY. Records: {'ledger_rows': 349, 'invoices': 85, 'payments': 59, 'documents': 144, 'fx_rates': 708}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | F-24437, P-56072 | 24245.45 USD | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate of the previous day) | P-56072 | 95219 JPY | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | P-96760 | 86826.71 USD | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | P-96760 | 170750.99 KZT | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | F-04967, F-86102 | 9126245.00 KZT | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | F-28065, F-52887 | 12210.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |

## Causal graph

```mermaid
flowchart LR
  nISS_ff11ea8cc8["#1 payment_allocation<br/>24245.45 USD"]
  nF_24437(["F-24437"]) --> nISS_ff11ea8cc8
  nP_56072(["P-56072"]) --> nISS_ff11ea8cc8
  nISS_ff11ea8cc8 -.changed.-> nISS_ff11ea8cc8ledger_add["ledger:add"]
  nISS_ff11ea8cc8 -.changed.-> nISS_ff11ea8cc8ledger_credit_minor["ledger:credit_minor"]
  nISS_ff11ea8cc8 -.changed.-> nISS_ff11ea8cc8ledger_debit_minor["ledger:debit_minor"]
  nISS_9e3e757d3d["#2 fx_error<br/>95219 JPY"]
  nP_56072(["P-56072"]) --> nISS_9e3e757d3d
  nISS_9e3e757d3d -.changed.-> nISS_9e3e757d3dledger_add["ledger:add"]
  nISS_9e3e757d3d -.changed.-> nISS_9e3e757d3dledger_credit_minor["ledger:credit_minor"]
  nISS_9e3e757d3d -.changed.-> nISS_9e3e757d3dledger_debit_minor["ledger:debit_minor"]
  nISS_5d5cd6bc11["#3 period_cutoff<br/>86826.71 USD"]
  nP_96760(["P-96760"]) --> nISS_5d5cd6bc11
  nISS_5d5cd6bc11 -.changed.-> nISS_5d5cd6bc11ledger_credit_minor["ledger:credit_minor"]
  nISS_5d5cd6bc11 -.changed.-> nISS_5d5cd6bc11ledger_debit_minor["ledger:debit_minor"]
  nISS_5d5cd6bc11 -.changed.-> nISS_5d5cd6bc11ledger_timestamp["ledger:timestamp"]
  nISS_46222fd78e["#4 fx_error<br/>170750.99 KZT"]
  nP_96760(["P-96760"]) --> nISS_46222fd78e
  nISS_46222fd78e -.changed.-> nISS_46222fd78eledger_credit_minor["ledger:credit_minor"]
  nISS_46222fd78e -.changed.-> nISS_46222fd78eledger_debit_minor["ledger:debit_minor"]
  nISS_46222fd78e -.changed.-> nISS_46222fd78eledger_timestamp["ledger:timestamp"]
  nISS_ae5d789906["#5 duplicate_invoice<br/>9126245.00 KZT"]
  nF_04967(["F-04967"]) --> nISS_ae5d789906
  nF_86102(["F-86102"]) --> nISS_ae5d789906
  nISS_ae5d789906 -.changed.-> nISS_ae5d789906invoices_add["invoices:add"]
  nISS_ae5d789906 -.changed.-> nISS_ae5d789906ledger_add["ledger:add"]
  nISS_afb1e91e5a["#6 duplicate_invoice<br/>12210.00 USD"]
  nF_28065(["F-28065"]) --> nISS_afb1e91e5a
  nF_52887(["F-52887"]) --> nISS_afb1e91e5a
  nISS_afb1e91e5a -.changed.-> nISS_afb1e91e5ainvoices_add["invoices:add"]
  nISS_afb1e91e5a -.changed.-> nISS_afb1e91e5aledger_add["ledger:add"]
  nISS_ff11ea8cc8 ==>|"partial_fx: causes"| nISS_9e3e757d3d
  nISS_5d5cd6bc11 ==>|"cutoff_fx: causes"| nISS_46222fd78e
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
