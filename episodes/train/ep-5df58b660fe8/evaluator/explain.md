# Episode ep-5df58b660fe8 (evaluator-only)

Period 2026-05-01T00:00:00+00:00 .. 2026-07-01T00:00:00+00:00 (end exclusive), company timezone UTC+00:00, base EUR, currencies EUR, JPY, USD. Records: {'ledger_rows': 310, 'invoices': 80, 'payments': 54, 'documents': 134, 'fx_rates': 708}.

**Clean company: no errors.** The right answer is an empty findings list; every accusation is a false positive.

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
