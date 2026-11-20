# Failure analysis (measured: `python -m auditforge.cli analysis`)

Policy: `simple_reconciler` (same-entity+total duplicates, string-date cutoff, total-amount FX check). 15 episodes per cell, mean F1.

| reconciler variant | with distractors | distractors removed |
|---|---|---|
| naive | 0.258 | 0.609 |
| +tz_aware | 0.499 | 0.978 |
| +tz_aware+allocated_amount | 0.507 | 1.000 |

Per-type counts of the naive variant (sum over episodes, distractors on):

| type | TP | FP | FN |
|---|---|---|---|
| duplicate_invoice | 15 | 57 | 0 |
| payment_allocation | 15 | 60 | 0 |
| fx_error | 10 | 108 | 5 |
| period_cutoff | 9 | 51 | 6 |

Clean companies (10 episodes, 0 errors), naive: **171 false accusations**, mean return -1.000 (silence scores about 0.96).

Interacting-only episodes (10 episodes, partial_fx + cutoff_fx), mean F1: naive **0.176**, +tz_aware **0.380**, +tz_aware+allocated_amount **0.507**.

How to read it: each ablation row removes one naive shortcut and the F1 gain is the measured cost of that shortcut. `reference_solver` (same tool API, exact policy) reaches F1 = 1.0 on every episode (see `reports/hidden_like_eval.json`), so the remaining gap is analytical difficulty, not unsolvable data.

## Shortcut rules (tricks) vs the truth (40 episodes: train + dev + hidden_like)

Each rule reads public tables only and skips the real logic (period of document vs posting, line items, memo). Legit distractors make every one of them pay with false accusations.

| error type | shortcut rule | TP | FP (false accusations) | FN |
|---|---|---|---|---|
| period_cutoff | posting delay outside 0-4 h | 45 | 200 | 1 |
| period_cutoff | posting before the document or 4-24 h after it | 40 | 114 | 6 |
| duplicate_invoice | same entity + po_ref | 37 | 80 | 0 |
| duplicate_invoice | same entity + po_ref + currency + total | 37 | 40 | 0 |
| payment_allocation | refs null or sum(refs) != amount | 42 | 160 | 0 |
| payment_allocation | refs null or non-empty refs with sum != amount | 42 | 120 | 0 |
