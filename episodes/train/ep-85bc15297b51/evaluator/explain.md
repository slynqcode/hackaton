# Episode ep-85bc15297b51 (evaluator-only)

Period 2026-04-01T00:00:00+00:00 .. 2026-05-01T00:00:00+00:00 (end exclusive), company timezone UTC+00:00, base GBP, currencies GBP, USD, EUR. Records: {'ledger_rows': 281, 'invoices': 81, 'payments': 44, 'documents': 125, 'fx_rates': 522}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | F-30271, P-27933 | 15869.67 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate of the previous day) | P-27933 | 183.66 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | P-96386 | 22803.85 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | P-96386 | 186.33 GBP | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | F-50903, F-70476 | 60400.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | F-72092, F-98176 | 55045.00 GBP | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |

## Causal graph

```mermaid
flowchart LR
  nISS_eb46e3ad42["#1 payment_allocation<br/>15869.67 EUR"]
  nF_30271(["F-30271"]) --> nISS_eb46e3ad42
  nP_27933(["P-27933"]) --> nISS_eb46e3ad42
  nISS_eb46e3ad42 -.changed.-> nISS_eb46e3ad42ledger_add["ledger:add"]
  nISS_eb46e3ad42 -.changed.-> nISS_eb46e3ad42ledger_credit_minor["ledger:credit_minor"]
  nISS_eb46e3ad42 -.changed.-> nISS_eb46e3ad42ledger_debit_minor["ledger:debit_minor"]
  nISS_f4539df001["#2 fx_error<br/>183.66 USD"]
  nP_27933(["P-27933"]) --> nISS_f4539df001
  nISS_f4539df001 -.changed.-> nISS_f4539df001ledger_add["ledger:add"]
  nISS_f4539df001 -.changed.-> nISS_f4539df001ledger_credit_minor["ledger:credit_minor"]
  nISS_f4539df001 -.changed.-> nISS_f4539df001ledger_debit_minor["ledger:debit_minor"]
  nISS_58491665fa["#3 period_cutoff<br/>22803.85 EUR"]
  nP_96386(["P-96386"]) --> nISS_58491665fa
  nISS_58491665fa -.changed.-> nISS_58491665faledger_credit_minor["ledger:credit_minor"]
  nISS_58491665fa -.changed.-> nISS_58491665faledger_debit_minor["ledger:debit_minor"]
  nISS_58491665fa -.changed.-> nISS_58491665faledger_timestamp["ledger:timestamp"]
  nISS_de055f4886["#4 fx_error<br/>186.33 GBP"]
  nP_96386(["P-96386"]) --> nISS_de055f4886
  nISS_de055f4886 -.changed.-> nISS_de055f4886ledger_credit_minor["ledger:credit_minor"]
  nISS_de055f4886 -.changed.-> nISS_de055f4886ledger_debit_minor["ledger:debit_minor"]
  nISS_de055f4886 -.changed.-> nISS_de055f4886ledger_timestamp["ledger:timestamp"]
  nISS_93285c5ff7["#5 duplicate_invoice<br/>60400.00 USD"]
  nF_50903(["F-50903"]) --> nISS_93285c5ff7
  nF_70476(["F-70476"]) --> nISS_93285c5ff7
  nISS_93285c5ff7 -.changed.-> nISS_93285c5ff7invoices_add["invoices:add"]
  nISS_93285c5ff7 -.changed.-> nISS_93285c5ff7ledger_add["ledger:add"]
  nISS_f3e5ad43a1["#6 duplicate_invoice<br/>55045.00 GBP"]
  nF_72092(["F-72092"]) --> nISS_f3e5ad43a1
  nF_98176(["F-98176"]) --> nISS_f3e5ad43a1
  nISS_f3e5ad43a1 -.changed.-> nISS_f3e5ad43a1invoices_add["invoices:add"]
  nISS_f3e5ad43a1 -.changed.-> nISS_f3e5ad43a1ledger_add["ledger:add"]
  nISS_eb46e3ad42 ==>|"partial_fx: causes"| nISS_f4539df001
  nISS_58491665fa ==>|"cutoff_fx: causes"| nISS_de055f4886
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
