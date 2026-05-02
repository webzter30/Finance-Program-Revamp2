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
- Comparison / planning reports:
  - Added option `6.7` to compare `CITY CC PAYMENT` by month across `2024`, `2025`, and `2026`.
  - Added option `9.7` Big Picture Savings View:
    - separates spending into `Base recurring`, `Irregular / sinking-fund`, and `Flexible`
    - uses standard recurring income categories first (`PAYCHECK`, `S_S`, etc.) when estimating safe savings transfers
    - prints the categories included in each bucket so the model is auditable
    - can include an optional house-maintenance reserve from a home-value % assumption
    - can include optional 401k/TSA progress inputs (annual goal, YTD contributed, estimated max-out timing)
    - now supports a biweekly paycheck-aware 401k estimate using gross pay, current withholding, and last payday to estimate remaining checks and likely max-out date
    - now includes the latest balance-snapshot totals so the flow model can be read next to current funded balances
    - now blends in prior-year monthly pace when the active year has too few completed months, so early-year spikes do not overstate categories like `AUTO` or `VACATION`
    - now prints a plain-English planning recommendation / takeaway section, including a note that 401k/TSA max-out timing and 3-paycheck month seasonality are not yet explicitly modeled
    - now includes a simple "how to read a negative month" section so one bad month does not read like a broken plan
    - frames the result as a conservative planning model, not a panic / solvency model
  - Added account-balance snapshot support:
    - setup option `ab` records dated balance snapshots into `ACCOUNT_BALANCE_SNAPSHOTS.db`
    - report option `9.75` shows balance trend plus funded / below-target bucket status using per-account floors
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
- `6.7` Costco credit card payments by month (2024-2026)
- `9.6` Base funds comparison (YoY + category deltas)
- `9.7` Big picture savings view (flow model + early-year prior-year stabilization + recommendation block + latest balance snapshot + optional house reserve + optional 401k/TSA progress, including biweekly paycheck-aware mode)
- `9.75` Account balance trend + funded bucket status
- `9.6ch` Base funds comparison chart (HTML)
- `16` Retirement predictor (SS + pension + savings draw)

### Planning Direction
- The app is moving toward a full working-years cash-planning model, not just transaction review.
- The target model should connect:
  - recurring take-home income
  - pre-tax retirement contribution timing and max-out effects
  - 2-paycheck vs 3-paycheck month seasonality
  - current account balances and bucket floors
  - dated account-balance flow over time
  - irregular reserve categories such as Auto, Taxes, and House Projects
  - retirement-style guardrails and wiggle-room stress testing
- The purpose is to answer both:
  - `safe to sweep now` based on current balances
  - `safe recurring monthly sweep` based on cash-flow behavior and reserve pacing
- The user wants a model that supports better 401k/TSA smoothing decisions, house-maintenance planning, and retirement planning discipline without forcing panic thinking.

### Remaining / Next
- Optional: add export option for retirement predictor table (CSV/XLSX), e.g. `16x`.
- Optional: refine healthcare model inputs from historical category pulls (instead of manual entry).
- Next requested step (queued):
  - Add seasonal income planning:
    - detect low-pay vs post-max-out periods for 401k/TSA
    - show how smoothing retirement contributions across the year changes monthly cash availability
  - Extend the new biweekly paycheck-aware `9.7` 401k/TSA block:
    - support non-biweekly pay frequencies
    - estimate take-home change from lowering the contribution rate
    - compare current front-loaded path vs a smoother full-year rate
  - Connect working-years cash planning more directly to retirement planning:
    - feed house-project targets and current cash funding into option `16`
    - show whether roof / HVAC / maintenance prep is already funded, partly funded, or still needs a build path before retirement
    - compare "keep 401k high" vs "slightly lower 401k and build cash" as part of the retirement-readiness tradeoff
  - Add "House Projects Bucket" modeling to option `16`:
    - input planned house-capex total (or yearly schedule)
    - separate must-do vs deferable items
    - model impact on draw, readiness, and cash reserve runway
    - include bad-market deferral logic for non-essential projects

### Git State
- Branch: `dev`
- Sync status: local `dev` matches `origin/dev`
- Recent commits:
  - `95573d3` Track retirement and house-project planning follow-up
  - `0cd1c47` Add paycheck-aware 401k planning estimates
  - `53c6700` Document paycheck-aware 401k planning follow-up
  - `2aa9d25` Add 401k progress to planning view
