# Episode ep-5a85a12d1c28 (evaluator-only)

Period 2026-03-01T00:00:00+03:00 .. 2026-05-01T00:00:00+03:00 (end exclusive), company timezone UTC+03:00, base USD, currencies USD, EUR, JPY. Records: {'ledger_rows': 343, 'invoices': 85, 'payments': 59, 'documents': 144, 'fx_rates': 708}.

## 6 hidden errors

| # | type | affected | amount | how to see it |
|---|---|---|---|---|
| 1 | payment_allocation (partial allocation) | F-37872, P-00171 | 16115.06 EUR | The payment memo names an invoice, but invoice_refs allocate less than the amount (or are null); the rest sits in UNAPPLIED. |
| 2 | fx_error (rate taken for the UTC date instead of the local date) | P-00171 | 167.53 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 3 | period_cutoff | P-58345 | 67968.09 EUR | Compare the period side (before / in / after, company timezone) of the document timestamp and of its ledger rows. |
| 4 | fx_error (rate of the (wrong) posting date) | P-58345 | 596.03 USD | Re-convert the ALLOCATED amount at the fx row of the payment's LOCAL date (company timezone) and compare with the AR credit. |
| 5 | duplicate_invoice | F-32857, F-89219 | 46900.00 EUR | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |
| 6 | duplicate_invoice | F-55531, F-67052 | 9990.00 USD | Same entity, same po_ref, same line items (in a different order) under a second invoice number. |

## Causal graph

```mermaid
flowchart LR
  nISS_3b8f8b4cd5["#1 payment_allocation<br/>16115.06 EUR"]
  nF_37872(["F-37872"]) --> nISS_3b8f8b4cd5
  nP_00171(["P-00171"]) --> nISS_3b8f8b4cd5
  nISS_3b8f8b4cd5 -.changed.-> nISS_3b8f8b4cd5ledger_add["ledger:add"]
  nISS_3b8f8b4cd5 -.changed.-> nISS_3b8f8b4cd5ledger_credit_minor["ledger:credit_minor"]
  nISS_3b8f8b4cd5 -.changed.-> nISS_3b8f8b4cd5ledger_debit_minor["ledger:debit_minor"]
  nISS_f59aea3f6e["#2 fx_error<br/>167.53 USD"]
  nP_00171(["P-00171"]) --> nISS_f59aea3f6e
  nISS_f59aea3f6e -.changed.-> nISS_f59aea3f6eledger_add["ledger:add"]
  nISS_f59aea3f6e -.changed.-> nISS_f59aea3f6eledger_credit_minor["ledger:credit_minor"]
  nISS_f59aea3f6e -.changed.-> nISS_f59aea3f6eledger_debit_minor["ledger:debit_minor"]
  nISS_4b24bb4b48["#3 period_cutoff<br/>67968.09 EUR"]
  nP_58345(["P-58345"]) --> nISS_4b24bb4b48
  nISS_4b24bb4b48 -.changed.-> nISS_4b24bb4b48ledger_credit_minor["ledger:credit_minor"]
  nISS_4b24bb4b48 -.changed.-> nISS_4b24bb4b48ledger_debit_minor["ledger:debit_minor"]
  nISS_4b24bb4b48 -.changed.-> nISS_4b24bb4b48ledger_timestamp["ledger:timestamp"]
  nISS_8a73ca79ec["#4 fx_error<br/>596.03 USD"]
  nP_58345(["P-58345"]) --> nISS_8a73ca79ec
  nISS_8a73ca79ec -.changed.-> nISS_8a73ca79ecledger_credit_minor["ledger:credit_minor"]
  nISS_8a73ca79ec -.changed.-> nISS_8a73ca79ecledger_debit_minor["ledger:debit_minor"]
  nISS_8a73ca79ec -.changed.-> nISS_8a73ca79ecledger_timestamp["ledger:timestamp"]
  nISS_827dce1e5d["#5 duplicate_invoice<br/>46900.00 EUR"]
  nF_32857(["F-32857"]) --> nISS_827dce1e5d
  nF_89219(["F-89219"]) --> nISS_827dce1e5d
  nISS_827dce1e5d -.changed.-> nISS_827dce1e5dinvoices_add["invoices:add"]
  nISS_827dce1e5d -.changed.-> nISS_827dce1e5dledger_add["ledger:add"]
  nISS_d1627b0554["#6 duplicate_invoice<br/>9990.00 USD"]
  nF_55531(["F-55531"]) --> nISS_d1627b0554
  nF_67052(["F-67052"]) --> nISS_d1627b0554
  nISS_d1627b0554 -.changed.-> nISS_d1627b0554invoices_add["invoices:add"]
  nISS_d1627b0554 -.changed.-> nISS_d1627b0554ledger_add["ledger:add"]
  nISS_3b8f8b4cd5 ==>|"partial_fx: causes"| nISS_f59aea3f6e
  nISS_4b24bb4b48 ==>|"cutoff_fx: causes"| nISS_8a73ca79ec
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
