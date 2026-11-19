# Failure analysis (measured: `python -m auditforge.cli analysis`)

Policy: `simple_reconciler` (same-entity+total duplicates, string-date cutoff, total-amount FX check). 15 episodes per cell, mean F1.

| reconciler variant | with distractors | distractors removed |
|---|---|---|
| naive | 0.266 | 0.651 |
| +tz_aware | 0.604 | 0.985 |
| +tz_aware+allocated_amount | 0.615 | 1.000 |

Per-type counts of the naive variant (sum over episodes, distractors on):

| type | TP | FP | FN |
|---|---|---|---|
| duplicate_invoice | 15 | 45 | 0 |
| payment_allocation | 15 | 30 | 0 |
| fx_error | 9 | 141 | 6 |
| period_cutoff | 9 | 41 | 6 |

Clean companies (10 episodes, 0 errors), naive: **137 false accusations**, mean return -1.000 (silence scores about 0.96).

Interacting-only episodes (10 episodes, partial_fx + cutoff_fx), mean F1: naive **0.135**, +tz_aware **0.462**, +tz_aware+allocated_amount **0.615**.

How to read it: each ablation row removes one naive shortcut and the F1 gain is the measured cost of that shortcut. `reference_solver` (same tool API, exact policy) reaches F1 = 1.0 on every episode (see `reports/hidden_like_eval.json`), so the remaining gap is analytical difficulty, not unsolvable data.
