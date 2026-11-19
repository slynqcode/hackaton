# Episode ep-2df38a76c8df (evaluator-only)

Period 2026-02-01T00:00:00+00:00 .. 2026-05-01T00:00:00+00:00 (end exclusive), company timezone UTC+00:00, base JPY, currencies JPY, KZT, USD. Records: {'ledger_rows': 302, 'invoices': 80, 'payments': 57, 'documents': 137, 'fx_rates': 876}.

**Clean company: no errors.** The right answer is an empty findings list; every accusation is a false positive.

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
