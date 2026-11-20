# Episode ep-e19bc9e1acf1 (evaluator-only)

Period 2026-01-01T00:00:00+00:00 .. 2026-03-01T00:00:00+00:00 (end exclusive), company timezone UTC+00:00, base USD, currencies USD, JPY, EUR. Records: {'ledger_rows': 310, 'invoices': 82, 'payments': 52, 'documents': 134, 'fx_rates': 696}.

**Clean company: no errors.** The right answer is an empty findings list; every accusation is a false positive.

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
