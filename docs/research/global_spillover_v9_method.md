# v9: A50 shock magnitude and the CSI1000 opening gap

The financial question and the single candidate were frozen at commit
`9554809cec804545e0713be1be788b42d7803bd5`, before this implementation.
This experiment asks whether the linear v6 mapping underfits the size of an
already available offshore-China price shock. It does not add information.

For ordinary sessions let `x` be the unchanged same-contract SGX A50 return
from the previous mainland close to strictly before 09:15. Add only
`q = x * abs(x)` to the exact V6A features, using the same StandardScaler and
Ridge(alpha=1). Both are fitted only on 2015–2018. The new feature is exactly
zero on holiday rows; missing ordinary observations remain missing.
The holiday A50 source keeps its earlier frozen 09:24:59 cutoff.

If standardized coefficients are `beta_x` and `beta_q`, the derivative in
raw-return units is `beta_x/scale_x + 2*abs(x)*beta_q/scale_q`.
Standardization means change the level, not this derivative. The derivative
must be strictly positive on every ordinary training observation. A larger
absolute shock can strengthen or weaken transmission; it cannot reverse its
economic direction within that observed support. This training gate is not
rescued by favorable holdout metrics.

The target remains `09:31 open / previous 15:00 close - 1`, an index forecast,
not an executable trade or an exact 09:25 auction-clearing price. 2019–2020
has already been used by previous research and supplies only repeat-audit
evidence. No 2021+ market rows may be requested or read.

The mathematical basis is a deliberately restricted hypothesis. The papers
cited by the frozen preanalysis concern nonlinear or asymmetric spillovers;
they do not establish this particular formula or this target's predictability.
The preanalysis's reference to previously "validated" A50 information means
retrospective progression evidence here, not genuinely unseen validation.

## Execution and failure interpretation

`python scripts/research_global_spillover_v9_a50_nonlinearity.py`

The runner checks exact V6 source bytes against its parent and exact v9
preregistration bytes against its freeze commit. It must reproduce V6 on
900 training and 461 holdout observations, including IC, R², sign and SSE,
within the registered `1e-12` tolerance before fitting V9.

Every registered progression gate is reported: full-sample magnitude and
direction; ordinary and holiday subsets; both years; all eight quarters;
and the training derivative. An unsuccessful candidate is a valid completed
experiment, not a software failure. Genuine source, clock, identity or replay
failures stop execution with an error.

Only one candidate is selectable. The two extra fits (original feature set
and NASDAQ only) fulfill the repository's required reference comparisons on
the exact same common sample; neither can replace V6 or influence selection.
Always-low-open accuracy is also reported.

Snapshots, fixed holdout predictions, training derivatives and source digests
are retained. Forensics operate only on those predictions: ordinary-row
same/lead/lag correlations, signed shock groups, coefficient redistribution,
and loss concentration after removing the top 1/5/10 positive contributors.
Removing rows never refits a model and cannot change the selection verdict.
One-row lead/lag refers to the ordered available ordinary holdout sample and
can cross a missing session or holiday; it is a diagnostic, not a trading-day
causality test.

No result grants baseline replacement, production, live registry changes,
runtime routing, or permission to merge main. The original V6 unseen
confirmation identity remains immutable.
