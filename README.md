# Finance Program Revamp 2

Personal finance tracker and analyzer using SQLite + pandas.

Key concepts:
- Database: `ONE_BIG_ACCOUNT_combined_dataYYYY.db`
- Working table: `NEW_ONE_BIG_ACCOUNT_data_YYYY`
- Categories: maintained in `categories.csv`


## Year Selection

- On startup, choose the active year; all reports use that year.
- The program reads `ONE_BIG_ACCOUNT_combined_dataYYYY.db` with table `NEW_ONE_BIG_ACCOUNT_data_YYYY`.
- After downloading new CSVs for a year, run Option 1 to rebuild that year's DB.


## Menu Overview (highlights)


- 1 — Rebuild database from latest bank exports
- 2 — Re-categorize database with latest `categories.csv`
- 3 — Show uncategorized transactions (top 50)
- ab — Enter account balance snapshot
- 4 — Lookup transactions by month and category
- 5 — Monthly and quarterly summary breakdown
- 5.1 — Quarterly income summary
- 5.2 — Monthly vs average (expenses)
- 6 — Show transactions tagged “LOOK INTO”
- 6.7 — Compare Costco credit card payments by month (2024–2026)
- 7 — Show transactions grouped by category
- 8 — Cash flow overview by month
- 8.1 — List income transactions for a month
- 8.2 — List expense transactions for a month (grouped)
- 14 — Consistent expense categories (ranked by YTD total)
- 14.1 — Monthly savings simulator (top 4 @ 15%, excludes Mortgage)
- 14.2 — Savings simulator (select categories, custom % per category, optional monthly cash‑flow simulation)
- 9/9.5/9.8 — Emergency fund estimates and drilldowns
- 9.7 — Big picture savings view (standard income + base recurring / irregular / flexible buckets + latest balance snapshot + optional house-maintenance reserve + planning recommendation + optional 401k/TSA progress)
- 9.75 — Account balance trend + funded/unfunded bucket status
- 10/11/12/13 — Forecasts, comparisons, date‑range reviews

## Planning Direction

The long-term goal is moving beyond transaction review into a cash-planning model that ties together:

- recurring take-home income (`PAYCHECK`, `S_S`, etc.)
- current spending behavior
- pre-tax retirement contribution timing (front-loaded vs smoothed across the year)
- bucket/account balances and account-floor buffers
- dated account-balance snapshots stored in SQLite so balance flow can be reviewed over time
- irregular reserve needs such as Auto, Taxes, House Projects, and roof-style maintenance
- retirement planning guardrails

The app is now trying to answer two different questions:

- How much cash is truly building across the real accounts and buckets?
- How much is safely sweepable to higher-yield savings without creating stress later?

Current planning philosophy:

- Separate base recurring spending from irregular reserve buckets and flexible spending.
- Show the included categories in each bucket so the model is understandable and auditable.
- Use standard recurring income first for savings guidance, but keep room to compare that against real balance buildup.
- Stabilize early-year planning views by blending completed months from the active year with the prior year's full monthly pace when too few current months exist.
- Track account balances over time so funded vs unfunded buckets can be reviewed against the flow model.
- Let the planning view optionally track annual 401k/TSA progress against a contribution goal so retirement saving pace can be seen next to cash-flow and savings-transfer guidance.
- Treat the current 401k/TSA progress block as a simple calendar-pace estimate; a later upgrade should make it paycheck-aware so max-out timing is based on actual pay frequency and withholding patterns.
- Prefer a conservative planning view, while still showing wiggle room so the output does not become a panic model.
- Keep the same planning discipline used in retirement analysis: enough structure to avoid forced bad decisions in tight periods or down markets.

## Using 8 / 8.1 / 8.2

- Option 8 prints a monthly table: Income, Expenses, and Net for each month.
- Option 8.1 prompts for a month name and lists the exact income transactions included in that month’s Income total (Date, Transact, Amount, Category, ACCOUNT), plus a total.
- Option 8.2 prompts for a month name and lists the expense transactions included in that month’s Expense total, grouped by Category. Each category shows:
  - Category total
  - The transactions in that category
  - A grand total across all categories for the month
  - A summary line: “Categories counted as expenses this month were: …”

Both drilldowns use the same classification rules as the monthly table, so sums match.

## Budget Insights (14 / 14.1 / 14.2)

- 14 — Consistent expense categories
  - Shows: Category | YTD Total | Avg/Active Mo | Highest Month (Amt) | Months
  - Lists all expense categories ranked by YTD total by default.

- 14.1 — Monthly savings simulator (top 4 @ 15%)
  - For each month, picks that month’s top 4 expense categories (excluding Mortgage) and applies a 15% reduction.
  - Prints: savings by category (YTD), and a monthly table (original vs simulated) with ΔNet improvements.

- 14.2 — Savings simulator (pick categories, custom %)
  - Prompts: enter categories (comma‑separated), then percent per selected category.
  - Output table: Category | Original | Percent | Savings | Reduced | Monthly Cut (Savings ÷ 12)
  - Totals: estimated improvement to YTD net cash flow and total monthly reduction across selected categories.
  - Optional: apply those percents to a monthly cash‑flow simulation (same format as 14.1) to see month‑by‑month impact.

## What’s New Today (2025-10-25)

- Reports
  - 5.1 — Quarterly income summary (matches cash‑flow rules; shows S_S, PAYCHECK, etc.)
  - 5.2 — Monthly vs Average (expenses): Category | This Month | Avg/Month | Diff | % Change
- Cash flow and drilldowns
  - 8.1 — Income transactions by month (verifies what counts toward Income)
  - 8.2 — Expense transactions by month (grouped by category), summary of categories included
  - 8p — Printer‑friendly cash flow (ASCII headers/deltas)
  - 8.2p — Printer‑friendly grouped expense listing (compact columns, totals)
- Budget tools
  - 14 — Category insights now lists all expense categories ranked by YTD total
  - 14.1 — Monthly savings simulator (top 4 @ 15%, excludes Mortgage) with monthly table and ΔNet
  - 14.2 — Savings simulator: pick categories, set per‑category percents; shows YTD savings, Monthly Cut per category, total monthly reduction; optional monthly cash‑flow simulation applying those cuts
- Categorization and consistency fixes
  - Recategorize inbound “USAA Transfer” +2000.00 as S_S (counts as income)
  - Silenced pandas regex warning (non‑capturing groups for SS regex)
  - Option 5 (quarterly expenses) now uses the same cash‑flow classification rules as option 8 for consistency
- Menu ergonomics
  - “First Review & Printouts (Quick Start)” hints under Setup & Maintenance: 4, 5, 5.2, 8p, 8.2p, 14p

## Categories and Social Security

- Social Security deposits can arrive via an “USAA Transfer”. To ensure they count as income and appear under Social Security:
  - The recategorization includes a rule: inbound “USAA Transfer” of exactly +2000.00 → `S_S`.
  - If your `categories.csv` maps “Security” → `S_S`, both will be counted together as income.
- If the deposit amount text varies slightly (e.g., 1999.99/2000.01) or the description text differs, adjust the rule accordingly.

## Verifying tags and commits

Recent checkpoints:

- 2025‑10‑25 — Added 8.1/8.2 drilldowns, silenced SSA regex warning, USAA +2000 → `S_S`.
  - Commit: `bb202ec`
  - Tag: `simple-main-opts8-drilldowns-2025-10-25`

- 2025‑10‑20 — Menu cleanup; USAA 2000 categorized to Security earlier (now superseded).
  - Commit: `db7239c`
  - Tag: `simple-main-2025-10-20`

Local verification commands:
- `git log -1 --oneline`
- `git tag -l "simple-main-*"`
- `git show bb202ec --name-only`

## 2025-11-03 Updates

- New Exports and HTML-Only Exports menus
  - 5x/5xh: Quarterly expense summaries now export one file per quarter (Q1–Q4). HTML-only variant writes CSV+HTML without Excel.
  - 5.2x/5.2xh: Monthly vs Average exports with 2-decimal formatting; "% Change" shown to two decimals.
  - 8x/8xh, 8.2x/8.2xh, 14x/14xh: Cash Flow, Expense Transactions (by month), and Category Insights exports. "Months Active" renders as a whole-number count.
  - 15x/15xh: Batch monthly review that runs all exports in one step.
- Combined quarterly HTML (5xhc): stacks Q1–Q4 tables on a single, print-friendly page.
- Charts (HTML; zero-install SVG)
  - 8ch: Cash flow by month (Income/Expenses bars, Net line)
  - 14ch: Category insights Top 10 (horizontal bars)
  - 5.2ch: Monthly vs Average (side-by-side bars)
- Timestamped filenames: all exports append `_YYYY-MM-DD_HHMM` to avoid overwrites.
- 2-decimal output: CSV/HTML/XLSX round numeric values to two decimals by default (integer-like counts remain whole numbers).
- Export subfolder: By default, exports save under `exports/printed YYYY-MM-DD` for the current day. Use Setup & Maintenance → `xd` to change the subfolder or clear it (blank) to save directly under `exports/`.

### Quick Tip: Set Export Subfolder (xd)

Keep runs organized under a dated folder.

- In the app menu: Setup & Maintenance → `xd`
- Enter a name like `printed 2025-11-03` → files save under `exports/printed 2025-11-03/`
- Press Enter with no text to clear and save directly under `exports/`
- The menu also reminds you: “Tip: Use 'xd' in Setup to set exports subfolder (e.g., printed YYYY-MM-DD)”

Tip: If you don't have Excel installed, use the HTML exports and print from your browser (Landscape, Fit to width).

## Current Status

This status summarizes recent changes and current usage tips for the Finance Program.
### Highlights (New Capabilities)

- Startup year prompt selects the active year/DB for reports
- Option 1 rebuild writes into the selected year's database
- Exports now have a dedicated menu and timestamped filenames
  - 5x (and 5xh HTML-only): Quarterly expense exports — one file per quarter
  - 5.2x / 5.2xh: Monthly vs Average (expenses)
  - 8x / 8xh: Cash flow by month
  - 8.2x / 8.2xh: Expense transactions for a selected month
  - 14x / 14xh: Category insights (Months Active is a count)
  - 15x / 15xh: Monthly review batch export
- Combined Quarterly HTML: 5xhc stacks Q1–Q4 on one print page
- Charts (HTML, no installs): 8ch (Cash Flow), 14ch (Top 10 Categories), 5.2ch (Monthly vs Avg)
- Export subfolder prompt (Setup & Maintenance → `xd`) to save under `exports/<subfolder>`

### Output and Formatting

- All numeric outputs are rounded to 2 decimals by default
- Count-like columns (e.g., Months Active) render as whole numbers
- Files save to `exports/` with a `_YYYY-MM-DD_HHMM` suffix
- If you prefer: set a subfolder (e.g., `printed 2025-11-03`) so outputs land in `exports/printed 2025-11-03`

### Printing Guidance

- HTML outputs print cleanly from any browser (Landscape, Fit to width)
- CSVs open in Excel/Google Sheets; set page to Landscape, Fit all columns
- XLSX page setup and currency formats apply when `xlsxwriter` is installed (optional)

### Next Ideas

- Add year prompts for combined quarterly page and cash-flow charts
- Optional PDF export via browser automation (would require additional tooling)
- Extend the planning layer to prompt for current account balances, bucket floors, and seasonal paycheck changes so "safe to sweep now" and "safe monthly sweep" can be modeled separately
- Add house-project / maintenance reserve planning (percent-of-home or project-based monthly reserve) and connect it to retirement/cash-planning decisions

