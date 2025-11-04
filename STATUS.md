# Status Report — 2025-11-03

This status summarizes recent changes and current usage tips for the Finance Program.

## Highlights (New Capabilities)

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

## Output and Formatting

- All numeric outputs are rounded to 2 decimals by default
- Count-like columns (e.g., Months Active) render as whole numbers
- Files save to `exports/` with a `_YYYY-MM-DD_HHMM` suffix
- If you prefer: set a subfolder (e.g., `printed 2025-11-03`) so outputs land in `exports/printed 2025-11-03`

## Printing Guidance

- HTML outputs print cleanly from any browser (Landscape, Fit to width)
- CSVs open in Excel/Google Sheets; set page to Landscape, Fit all columns
- XLSX page setup and currency formats apply when `xlsxwriter` is installed (optional)

## Next Ideas

- Add year prompts for combined quarterly page and cash-flow charts
- Optional PDF export via browser automation (would require additional tooling)

