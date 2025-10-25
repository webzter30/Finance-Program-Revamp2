# Finance Program Revamp 2

Personal finance tracker and analyzer using SQLite + pandas.

Key concepts:
- Database: `ONE_BIG_ACCOUNT_combined_dataYYYY.db`
- Working table: `NEW_ONE_BIG_ACCOUNT_data_YYYY`
- Categories: maintained in `categories.csv`

## Menu Overview (highlights)

- 1 — Rebuild database from latest bank exports
- 2 — Re-categorize database with latest `categories.csv`
- 3 — Show uncategorized transactions (top 50)
- 4 — Lookup transactions by month and category
- 5 — Monthly and quarterly summary breakdown
- 6 — Show transactions tagged “LOOK INTO”
- 7 — Show transactions grouped by category
- 8 — Cash flow overview by month
- 8.1 — List income transactions for a month
- 8.2 — List expense transactions for a month (grouped)
- 14 — Consistent expense categories (ranked by YTD total)
- 14.1 — Monthly savings simulator (top 4 @ 15%, excludes Mortgage)
- 14.2 — Savings simulator (select categories, custom % per category, optional monthly cash‑flow simulation)
- 9/9.5/9.8 — Emergency fund estimates and drilldowns
- 10/11/12/13 — Forecasts, comparisons, date‑range reviews

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
