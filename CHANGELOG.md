# Changelog

All notable changes to this project will be documented in this file.

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
