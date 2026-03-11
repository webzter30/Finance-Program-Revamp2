# Status Report

## Checkpoint (2026-03-05)

### Completed
- Year handling:
  - Startup prompt now supports explicit year selection (`2024`, `2025`, `2026`).
  - In-menu year switching added (`y`) so restart is not required.
  - DB table resolution now auto-fallbacks between `NEW_ONE_BIG_ACCOUNT_data_<year>` and `ONE_BIG_ACCOUNT_data_<year>`.
- Menu UX:
  - Compact menu default to reduce scrolling.
  - Full/compact/quick-start commands available (`m`, `c`, `qs`).
- Emergency fund + comparisons:
  - Taxes excluded from options `9`, `9.5`, and `9.8`.
  - Optional non-essential category exclusions supported (e.g., `NANNY TAX`).
  - Added option `9.6` for base-funds comparison (YoY + category deltas).
  - Added option `9.6ch` for HTML chart export.
- Tax reporting:
  - Added option `6.6` for taxes paid by month and yearly total.
- Forecast model:
  - Remaining-month income model now uses previous-year Q4 average dynamically.
  - Forecast output now states the source math used for the monthly income model.
- Retirement planning:
  - Added option `16` Retirement Predictor:
    - 10-year fixed projection horizon
    - SS + pension phase modeling (e.g., `5:12819,10:9000`)
    - annual gross income, estimated taxes, healthcare modeling
    - annual/cumulative savings withdrawals
    - retirement readiness scorecard metrics
    - Medicare healthcare step-down modeling at selected age/reduction %
    - RMD-age portfolio projections (deterministic and Monte Carlo)
    - extra discretionary spending window (amount + start/end years)
    - comfort extra-spending guidance (monthly/yearly ranges via guardrails)
    - 5-year chunk visual summary blocks (withdrawal %, x-factor, cash months, and guardrail caps)

### Current Menu Additions
- `6.6` Taxes paid by month + total
- `9.6` Base funds comparison (YoY + category deltas)
- `9.6ch` Base funds comparison chart (HTML)
- `16` Retirement predictor (SS + pension + savings draw)

### Remaining / Next
- Optional: add export option for retirement predictor table (CSV/XLSX), e.g. `16x`.
- Optional: refine healthcare model inputs from historical category pulls (instead of manual entry).

### Git State
- Branch: `dev`
- Recent commits:
  - `b6ac380` Add retirement predictor, base-funds comparison, and menu/year UX improvements
  - `4202dda` Improve menu UX, year switching, and tax reporting/exclusions
