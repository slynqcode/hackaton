# Episode ep-ab4e0c2d234a (evaluator-only)

Period 2026-03-01T00:00:00-05:00 .. 2026-05-01T00:00:00-05:00 (end exclusive), company timezone UTC-05:00, base GBP, currencies GBP, KZT, EUR. Records: {'ledger_rows': 350, 'invoices': 81, 'payments': 60, 'documents': 141, 'fx_rates': 708}.

**Clean company: no errors.** The right answer is an empty findings list; every accusation is a false positive.

## Legitimate look-alikes in this company (not errors)

- same amounts for the same customer with a different po_ref (legitimate repeat orders)
- monthly subscriptions with identical lines
- instalments and multi-invoice payments
- refunds (negative amounts)
- advance payments on account: legitimate UNAPPLIED cash, memo names no invoice
- documents near the period boundary rendered in a foreign UTC offset (calendar-date strings mislead)
- correct cross-currency receipts
