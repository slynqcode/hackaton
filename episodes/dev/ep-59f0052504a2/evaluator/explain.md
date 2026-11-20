# Episode ep-59f0052504a2 (evaluator-only)

Period 2026-06-01T00:00:00-03:00 .. 2026-07-01T00:00:00-03:00 (end exclusive), company timezone UTC-03:00, base EUR, currencies EUR, KZT, GBP. Records: {'ledger_rows': 290, 'invoices': 78, 'payments': 43, 'documents': 121, 'fx_rates': 522}.

**Clean company: no errors.** The right answer is an empty findings list; every accusation is a false positive.

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
