# High-open development pack, 2015-01-05 through 2025-12-31

This pack exists so the cloud workspace can run high-open recall **development**
scripts without the local FactorLab/DataHub absolute paths.

It is **not** a 2026 open.

- Included: `000852.SH` daily annotated panel, 1-minute bars, and FRED NASDAQ/VIX through 2025-12-31.
- Excluded: 2026-01-05 through 2026-08-21 sealed repeat-blackbox rows; post-2026-08-21 unread fresh rows.
- The original `data/development/` 2015-2020 freeze remains authoritative for the first research cycle.
- Production authority is false.

Local machines that still have the original FactorLab/DataHub files continue to
use those files. Cloud machines fall back to this pack.
