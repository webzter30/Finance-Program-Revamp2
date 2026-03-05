# Changelog

All notable changes to this project will be documented in this file.

## 2026-03-05

- Change: Dynamic year workflow improvements:
  - Explicit startup selection for `2024/2025/2026`.
  - In-menu year switching (`y`) without restart.
  - DB table auto-fallback between `NEW_ONE_BIG_ACCOUNT_data_<year>` and `ONE_BIG_ACCOUNT_data_<year>`.
- Change: Menu usability updates:
  - Compact menu default to reduce scrolling.
  - Added menu commands for `m` (full), `c` (compact), `qs` (quick-start), `y` (switch year).
- Feature: Added `6.6` report for taxes paid by month plus yearly total.
- Change: Emergency fund options now support tax exclusion and optional non-essential category exclusions:
  - Updated `9`, `9.5`, `9.8` (e.g., exclude `NANNY TAX` as needed).
- Feature: Added `9.6` base-funds comparison (YoY monthly + category deltas).
- Feature: Added `9.6ch` HTML chart for base-funds comparison.
- Change: Forecast model now uses previous-year Q4 income dynamically instead of hardcoded 2024 assumptions, and prints source math.
- Feature: Added `16` Retirement Predictor:
  - fixed 10-year projection horizon
  - SS + pension phase schedule parsing (`years:amount`)
  - annual gross income, estimated taxes, healthcare modeling, yearly/cumulative withdrawals
  - retirement readiness scorecard metrics (spending multiple, withdrawal rate, guaranteed-income coverage, 10-year draw, 4% stress test, liquidity targets)

## 2026-01-16

- Change: Prompt for active year at program start; reports use the selected year.
- Change: Option 1 rebuild writes into the selected year's database.
- Fix: Avoid blank reports when system date is ahead of the data year.
- Change: Manual override for Costco tires purchase ($1036.47) to categorize as Auto.


## 2025-11-03

- New: Exports menu and HTML-Only Exports menu.
  - 5x: Quarterly expense summary now exports one file per quarter (Q1..Q4). Timestamped filenames to avoid overwrite.
  - 5xh: Same as 5x but CSV/HTML only (no XLSX creation).
  - 5.2x / 5.2xh: Monthly vs Average (expenses) exports.
  - 8x / 8xh: Cash flow by month exports.
  - 8.2x / 8.2xh: Expense transactions for a month exports.
  - 14x / 14xh: Category insights exports; "Months Active" is formatted as a count.
  - 15x / 15xh: Monthly review batch export.
- New: Combined quarterly HTML (5xhc) that stacks Q1–Q4 on one printable page.
- New: Charts (HTML) using inline SVG (no dependencies):
  - 8ch Cash flow by month; 14ch Category insights Top 10; 5.2ch Monthly vs Average.
- Change: All exports round numeric values to two decimals by default; integer-like counts (e.g., "Months Active") are whole numbers.
- Change: Optional export subfolder (Setup & Maintenance → `xd`) to save under `exports/<subfolder>` per session.

## 2025-10-25

- Feature: Option 8.1 — List income transactions for a month
- Feature: Option 8.2 — List expense transactions for a month (grouped by category), with category totals and a final summary of all expense categories counted that month
- Fix: Silenced pandas warning by switching Social Security regex to non‑capturing groups
- Change: Recategorize inbound “USAA Transfer” +2000.00 as `S_S` (counts as income and appears under Social Security)
- Feature: Option 14 — Consistent expense categories (ranked by YTD total; show highest month and averages)
- Feature: Option 14.1 — Monthly savings simulator (top 4 @ 15%, excludes Mortgage); prints monthly original vs simulated with ΔNet
- Feature: Option 14.2 — Savings simulator for selected categories with custom percent each; shows YTD savings, Monthly Cut, and optional monthly cash‑flow simulation applying those percents
- Git: Tag `simple-main-opts8-drilldowns-2025-10-25`, commit `bb202ec`
- Git: Tag `pre-monthly-savings-sim-2025-10-25-1510` (checkpoint)

## 2025-10-20

- Menu cleanup and categorization adjustments
- Git: Tag `simple-main-2025-10-20`, commit `db7239c`
