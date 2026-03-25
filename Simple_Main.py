## CREATED WITH AI TO SIMPLIFY MY CODE GETTING THE ACCOUNTS CSV TOGETHER AND FILTERING THEM WITH A FILTER_CATEGORY.CSV TO MAKE IT 
## TO CHANGE THE CATEGORIES 
# 4_8_25

# ╔════════════════════════════════════════════════════════════════════════════════╗
# ║ 💼 REVAMP FINANCE V3 — 4_8_25                                                 ║
# ╠════════════════════════════════════════════════════════════════════════════════╣
# ║ 📂 Personal finance tracker + analyzer                                        ║
# ║ 🧠 Tracks income, expenses, and categories                                    ║
# ║ 📊 Outputs monthly + yearly summaries, uncategorized lists, and cash flow     ║
# ║ 💾 Uses SQLite database: ONE_BIG_ACCOUNT_combined_data2025.db                 ║
# ║ 📈 Working table: NEW_ONE_BIG_ACCOUNT_data_2025                               ║
# ║ 📁 Category mapping via: categories.csv                                       ║
# ║ 🧩 categories.csv allows smoother addition of transaction-category rules      ║
# ║ 🚀 Ready for future expansions: web, mobile, goals, and savings optimization  ║
# ╚════════════════════════════════════════════════════════════════════════════════╝



###########################################
# WORKFLOW SUMMARY
###########################################

## NOTE Current Flow Recap (Your Setup)

## NOTE Download multiple CSVs (bank, credit card, etc.)
# - CSVs downloaded manually from your banks/credit cards

## NOTE Normalize them to a unified column format
# - Handled using a flexible config dictionary that maps column names

## NOTE Concatenate into one pandas DataFrame
# - All cleaned DataFrames are combined with pd.concat()

## NOTE Categorize each transaction (using a custom dictionary)
# - Keyword-based using categories.csv !!!!!
# - Automatically tags transactions
#
#    ##-- how to fix this, streamline review, and prevent rework
#    - All uncategorized transactions are printed with top counts
#    - You can update categories.csv and re-run categorization without reloading CSVs
#    - Review top missed descriptions directly in console with script 

## NOTE Store in a database
# - Data is stored in an SQLite .db file
# - Table name is version-controlled (NEW_ONE_BIG_ACCOUNT_data_2025)

## NOTE Analyze in main.py (monthly/quarterly breakdowns)
# - Supports pivot tables, charts, and exports to Excel or summary printouts

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, inspect
import pandas as pd
from datetime import date
from typing import Optional
from datetime import datetime
import os

# --- CONFIGURATION ---
YEAR = 'FULL_YEAR_25'
category_mapping_file = "categories.csv"
PRINTER_FRIENDLY = True
# Default: save exports under a dated subfolder per day (can be changed via 'xd')
EXPORTS_SUBDIR: Optional[str] = f"printed {datetime.now().strftime('%Y-%m-%d')}"
ACTIVE_YEAR: Optional[int] = None


def _year_from_tag(tag) -> Optional[int]:
    if tag is None:
        return None
    if isinstance(tag, int):
        return int(tag)
    digits = ''.join(filter(str.isdigit, str(tag)))
    if len(digits) == 2:
        return int("20" + digits)
    if len(digits) == 4:
        return int(digits)
    if len(digits) > 4:
        return int(digits[-4:])
    return None


def _year_to_tag(year: int) -> str:
    yy = str(int(year))[-2:]
    return f"FULL_YEAR_{yy}"


def get_active_year(default_to_today: bool = True) -> int:
    if ACTIVE_YEAR is not None:
        return int(ACTIVE_YEAR)
    y = _year_from_tag(YEAR)
    if y is not None:
        return y
    return date.today().year if default_to_today else date.today().year


def set_active_year(year: int) -> None:
    global ACTIVE_YEAR, YEAR, account_csv_configs
    ACTIVE_YEAR = int(year)
    YEAR = _year_to_tag(ACTIVE_YEAR)
    try:
        account_csv_configs = build_account_csv_configs(YEAR)
    except Exception:
        pass


def _prompt_active_year() -> bool:
    default_year = get_active_year()
    print(f"\nSelect year to use: 2024 / 2025 / 2026 (default {default_year})")
    raw = input("Year: ").strip()
    if raw == "":
        set_active_year(default_year)
        return True
    if raw.isdigit():
        year = int(raw)
        if len(raw) == 2:
            year = int("20" + raw)
        if year < 2000 or year > 2100:
            print("Please enter a valid year between 2000 and 2100.")
            return False
        set_active_year(year)
        return True
    print("Invalid year input. Please enter a 2- or 4-digit year.")
    return False


def get_db_info(year: Optional[int] = None) -> tuple[str, str]:
    y = int(year) if year is not None else get_active_year()
    db_file = f"ONE_BIG_ACCOUNT_combined_data{y}.db"

    # Prefer NEW_* when available, but auto-fallback to legacy table names (e.g., 2024).
    candidates = [f"NEW_ONE_BIG_ACCOUNT_data_{y}", f"ONE_BIG_ACCOUNT_data_{y}"]
    if os.path.exists(db_file):
        try:
            engine = create_engine(f"sqlite:///{db_file}")
            insp = inspect(engine)
            for t in candidates:
                if insp.has_table(t):
                    return db_file, t
        except Exception:
            pass

    # Default fallback keeps existing behavior for rebuild flows.
    return db_file, candidates[0]


# 9_15_25

# === CASHFLOW RULES — SINGLE SOURCE OF TRUTH ===
import re
import pandas as pd

# Count these as INCOME
CF_INCOME_CATS = {
    "PAYCHECK", "S_S", "S S", "SS", "SOCIAL SECURITY", "SSA", "SSA INCOME",
    "INCOME ? KP", "WORK", "SECURITY"  # <- include Security as income
}

# Ignore these entirely (not income, not expense)
CF_EXCLUDE_CATS = {
    "CITY CC PAYMENT", "USAA CC PAYMENT", "CC PAYMENT",
    "TRANSFER", "COSTCO REBATE", "ACCOUNT INTEREST",
    "VANGUARD INVESTMENT", "INVESTMENT"
}

# SS/SSA detector for weird labels in Description/Transact/Account text
CF_SS_REGEX = re.compile(
    r"(?:ssa\s*treas|treas\s*310\s*ssa|soc(?:ial)?\s*sec(?:urity)?|ssa\s*deposit|ss\s*income)",
    flags=re.IGNORECASE
)

def _series(df, col):
    """Safe accessor that always returns a Series (prevents 'str has no .astype' errors)."""
    return df[col].astype(str) if col in df.columns else pd.Series([""] * len(df), index=df.index)

def compute_inflow_outflow(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a dataframe with:
      - Date (datetime), Month (name)
      - Amount (float)
      - Category (string)
      - inflow (abs income), outflow (abs expense)
      - is_income, is_expense flags
    Using a single, consistent rule set for ALL features.
    """
    out = df.copy()

    # Types
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce")
    out["Amount"] = pd.to_numeric(out["Amount"], errors="coerce")
    out = out[out["Date"].notna() & out["Amount"].notna()].copy()
    if "Month" not in out.columns:
        out["Month"] = out["Date"].dt.month_name()

    # Categories/text
    cat_raw = _series(out, "Category")
    cat_up  = cat_raw.str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
    cat_lo  = cat_raw.str.lower().str.strip()

    text_blob = (_series(out, "Transact") + " " +
                 _series(out, "Description") + " " +
                 _series(out, "ACCOUNT") + " " +
                 cat_raw).str.lower()

    looks_ss = text_blob.str.contains(CF_SS_REGEX, na=False)

    is_income   = cat_up.isin(CF_INCOME_CATS) | looks_ss
    is_excluded = cat_up.isin(CF_EXCLUDE_CATS)
    is_mortgage = cat_lo.eq("mortgage")
    is_expense  = (~is_income & ~is_excluded) | is_mortgage

    out["inflow"]  = 0.0
    out["outflow"] = 0.0
    out.loc[is_income,  "inflow"]  = out.loc[is_income,  "Amount"].abs()
    out.loc[is_expense, "outflow"] = out.loc[is_expense, "Amount"].abs()

    out["is_income"]  = is_income
    out["is_expense"] = is_expense
    return out

# --- Export helper (CSV/XLSX/HTML) ---
def export_print_friendly(
    df: pd.DataFrame,
    base_name: str = "Report",
    out_dir: str = "exports",
    *,
    currency_cols: set[str] | None = None,
    number_cols: set[str] | None = None,
    timestamped: bool = False,
    write_xlsx: bool = True,
) -> None:
    """Save DataFrame to CSV, XLSX (print-optimized), and HTML for clean printing.

    - Creates `out_dir` if needed
    - XLSX: landscape, fit to one page wide, narrow margins, bold header, freeze header
    - Attempts xlsxwriter for better print settings; falls back to openpyxl
    """
    import os
    # Resolve output directory, honoring optional global subfolder
    effective_dir = out_dir
    try:
        if EXPORTS_SUBDIR and str(EXPORTS_SUBDIR).strip():
            effective_dir = os.path.join(out_dir, str(EXPORTS_SUBDIR).strip())
    except NameError:
        # Fallback if global not defined yet
        effective_dir = out_dir

    os.makedirs(effective_dir, exist_ok=True)

    # Optional timestamp suffix to keep every run
    if timestamped:
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%Y-%m-%d_%H%M")
        file_stem = f"{base_name}_{ts}"
    else:
        file_stem = base_name

    csv_path = os.path.join(effective_dir, f"{file_stem}.csv")
    xlsx_path = os.path.join(effective_dir, f"{file_stem}.xlsx")
    html_path = os.path.join(effective_dir, f"{file_stem}.html")

    # Normalize numeric precision for consistent CSV/HTML display
    from pandas.api.types import is_numeric_dtype as _is_num
    df2 = df.copy()
    for col in df2.columns:
        if _is_num(df2[col]):
            if number_cols and col in number_cols:
                # Round to 0 and keep as nullable integer to preserve blanks
                try:
                    df2[col] = pd.to_numeric(df2[col], errors="coerce").round(0).astype("Int64")
                except Exception:
                    df2[col] = pd.to_numeric(df2[col], errors="coerce").round(0)
            else:
                df2[col] = pd.to_numeric(df2[col], errors="coerce").round(2)

    # CSV
    df2.to_csv(csv_path, index=False)

    # Excel engine preference
    try:
        import xlsxwriter  # noqa: F401
        engine = "xlsxwriter"
    except Exception:
        engine = "openpyxl"

    if write_xlsx:
        with pd.ExcelWriter(xlsx_path, engine=engine) as writer:
            sheet_name = "Report"
            df2.to_excel(writer, sheet_name=sheet_name, index=False)

            if engine == "xlsxwriter":
                wb = writer.book
                ws = writer.sheets[sheet_name]

                # Page/print layout
                ws.set_landscape()
                ws.set_margins(left=0.25, right=0.25, top=0.5, bottom=0.5)
                ws.center_horizontally()
                ws.fit_to_pages(1, 0)

                # Header style and freeze
                header_fmt = wb.add_format({"bold": True})
                ws.set_row(0, None, header_fmt)
                ws.freeze_panes(1, 0)

                # Column widths and numeric formatting
                from pandas.api.types import is_numeric_dtype
                currency_fmt = wb.add_format({"num_format": "$#,##0.00"})
                number_fmt = wb.add_format({"num_format": "#,##0"})
                for col_idx, col_name in enumerate(df2.columns):
                    s = df2[col_name].astype(str)
                    try:
                        max_len_val = int(s.map(len).max())
                    except Exception:
                        max_len_val = len(str(col_name))
                    max_len = max(len(str(col_name)), max_len_val)
                    fmt = None
                    if currency_cols and col_name in currency_cols:
                        fmt = currency_fmt
                    elif number_cols and col_name in number_cols:
                        fmt = number_fmt
                    elif is_numeric_dtype(df2[col_name]) and currency_cols is None and number_cols is None:
                        # Default behavior when no explicit formatting sets provided: treat numerics as currency
                        fmt = currency_fmt
                    ws.set_column(col_idx, col_idx, max(8, min(40, max_len + 2)), fmt)

    # HTML with monospace + landscape print CSS
    css = (
        "<style>"
        "body{font-family:Consolas,'Courier New',monospace;font-size:11pt;}"
        "table{border-collapse:collapse;width:100%;}"
        "th,td{border:1px solid #999;padding:4px 6px;}"
        "th{background:#f2f2f2;}"
        "@page{size:A4 landscape;margin:0.5in;}"
        "</style>"
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(css + df2.to_html(index=False, border=0))

    print(f"Saved: {csv_path}")
    if write_xlsx:
        print(f"Saved: {xlsx_path}")
    print(f"Saved: {html_path}")


def set_export_subfolder():
    """Prompt to set a subfolder under 'exports' for all subsequent exports in this session.

    Examples: 'printed 2025-11-03' or leave blank to reset.
    """
    global EXPORTS_SUBDIR
    today_str = datetime.now().strftime("%Y-%m-%d")
    cur = EXPORTS_SUBDIR or "(none)"
    print(f"\nCurrent export subfolder: {cur}")
    print("Leave blank to use default 'exports' (no subfolder).")
    suggested = f"printed {today_str}"
    val = input(f"Enter export subfolder name (e.g., {suggested}): ").strip()
    if not val:
        EXPORTS_SUBDIR = None
        print("Export subfolder cleared; using 'exports' root.")
    else:
        # Sanitize just a little
        EXPORTS_SUBDIR = val.replace("\\", "/").strip()
        print(f"Export subfolder set to: {EXPORTS_SUBDIR}")


BALANCE_DB_FILE = "ACCOUNT_BALANCE_SNAPSHOTS.db"
BALANCE_TABLE_NAME = "ACCOUNT_BALANCE_SNAPSHOTS"
DEFAULT_BALANCE_ACCOUNT_ROWS = [
    {"account_name": "JEFF CHECKING", "purpose": "operating", "target_floor": 3000.0, "notes": "paycheck landing account"},
    {"account_name": "JOINT CHECKING", "purpose": "shared bills", "target_floor": 4000.0, "notes": "credit-card and shared bill float"},
    {"account_name": "SAVINGS", "purpose": "surplus storage", "target_floor": 0.0, "notes": "high-yield / reserve cash"},
    {"account_name": "NANNY ACCOUNT", "purpose": "bucket", "target_floor": 0.0, "notes": "nanny reserve"},
    {"account_name": "MORTGAGE ACCOUNT", "purpose": "buffer", "target_floor": 0.0, "notes": "mortgage cushion"},
]


def _balance_engine():
    return create_engine(f"sqlite:///{BALANCE_DB_FILE}")


def _ensure_balance_snapshot_table():
    engine = _balance_engine()
    try:
        insp = inspect(engine)
        if insp.has_table(BALANCE_TABLE_NAME):
            return
        cols = ["snapshot_date", "account_name", "balance", "target_floor", "purpose", "notes", "captured_at"]
        pd.DataFrame(columns=cols).to_sql(BALANCE_TABLE_NAME, engine, if_exists="replace", index=False)
    finally:
        engine.dispose()


def _parse_money_value(raw: str) -> float:
    return float(str(raw).replace("$", "").replace(",", "").strip())


def load_balance_snapshots() -> pd.DataFrame:
    _ensure_balance_snapshot_table()
    engine = _balance_engine()
    try:
        df = pd.read_sql_table(BALANCE_TABLE_NAME, engine)
    finally:
        engine.dispose()
    if df.empty:
        return df
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["balance"] = pd.to_numeric(df.get("balance"), errors="coerce").fillna(0.0)
    df["target_floor"] = pd.to_numeric(df.get("target_floor"), errors="coerce").fillna(0.0)
    for col in ["account_name", "purpose", "notes", "captured_at"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    return df


def _balance_seed_rows() -> pd.DataFrame:
    df = load_balance_snapshots()
    if df.empty:
        return pd.DataFrame(DEFAULT_BALANCE_ACCOUNT_ROWS)
    df["snapshot_date_dt"] = pd.to_datetime(df["snapshot_date"], errors="coerce")
    latest_date = df["snapshot_date_dt"].max()
    latest = (
        df[df["snapshot_date_dt"].eq(latest_date)]
        .sort_values(["account_name", "captured_at"])
        .drop_duplicates(subset=["account_name"], keep="last")
        .copy()
    )
    if latest.empty:
        return pd.DataFrame(DEFAULT_BALANCE_ACCOUNT_ROWS)
    keep_cols = ["account_name", "balance", "target_floor", "purpose", "notes"]
    return latest[keep_cols].reset_index(drop=True)


def save_balance_snapshots(df_new: pd.DataFrame) -> None:
    _ensure_balance_snapshot_table()
    engine = _balance_engine()
    try:
        existing = load_balance_snapshots()

        df_save = df_new.copy()
        df_save["snapshot_date"] = pd.to_datetime(df_save["snapshot_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df_save["account_name"] = df_save["account_name"].astype(str).str.strip()
        df_save["purpose"] = df_save["purpose"].fillna("").astype(str).str.strip()
        df_save["notes"] = df_save["notes"].fillna("").astype(str).str.strip()
        df_save["balance"] = pd.to_numeric(df_save["balance"], errors="coerce").fillna(0.0)
        df_save["target_floor"] = pd.to_numeric(df_save["target_floor"], errors="coerce").fillna(0.0)
        if "captured_at" not in df_save.columns:
            df_save["captured_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if existing.empty:
            combined = df_save
        else:
            key_new = set(
                zip(
                    df_save["snapshot_date"].astype(str),
                    df_save["account_name"].astype(str).str.upper().str.strip(),
                )
            )
            keep_mask = ~existing.apply(
                lambda r: (str(r["snapshot_date"]), str(r["account_name"]).upper().strip()) in key_new,
                axis=1,
            )
            combined = pd.concat([existing.loc[keep_mask].copy(), df_save], ignore_index=True)

        combined.to_sql(BALANCE_TABLE_NAME, engine, if_exists="replace", index=False)
    finally:
        engine.dispose()


def enter_account_balance_snapshot():
    _ensure_balance_snapshot_table()
    default_date = datetime.now().strftime("%Y-%m-%d")
    raw_date = input(f"\nSnapshot date [default {default_date}]: ").strip()
    snapshot_date = raw_date or default_date
    try:
        snapshot_date = pd.to_datetime(snapshot_date, errors="raise").strftime("%Y-%m-%d")
    except Exception:
        print("Invalid date. Use YYYY-MM-DD.")
        return

    seed = _balance_seed_rows()
    rows = []
    print("\nEnter current balances and target floors.")
    print("Press Enter to keep the shown default value.")

    for _, row in seed.iterrows():
        account_name = str(row.get("account_name", "")).strip()
        if not account_name:
            continue

        bal_default = float(pd.to_numeric(pd.Series([row.get("balance", 0.0)]), errors="coerce").fillna(0.0).iloc[0])
        floor_default = float(pd.to_numeric(pd.Series([row.get("target_floor", 0.0)]), errors="coerce").fillna(0.0).iloc[0])
        purpose_default = str(row.get("purpose", "")).strip()
        notes_default = str(row.get("notes", "")).strip()

        print(f"\nAccount: {account_name}")
        while True:
            bal_raw = input(f"  Balance [default {bal_default:,.2f}]: ").strip()
            try:
                balance = bal_default if bal_raw == "" else _parse_money_value(bal_raw)
                break
            except Exception:
                print("  Enter a valid number.")
        while True:
            floor_raw = input(f"  Target floor / buffer [default {floor_default:,.2f}]: ").strip()
            try:
                target_floor = floor_default if floor_raw == "" else _parse_money_value(floor_raw)
                break
            except Exception:
                print("  Enter a valid number.")

        purpose = input(f"  Purpose [default {purpose_default or 'bucket'}]: ").strip() or (purpose_default or "bucket")
        notes = input(f"  Notes [default {notes_default}]: ").strip() or notes_default

        rows.append(
            {
                "snapshot_date": snapshot_date,
                "account_name": account_name,
                "balance": balance,
                "target_floor": target_floor,
                "purpose": purpose,
                "notes": notes,
                "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    while True:
        add_more = input("\nAdd another account snapshot? (y/N): ").strip().lower()
        if add_more not in {"y", "yes"}:
            break
        account_name = input("  Account name: ").strip()
        if not account_name:
            print("  Account name required.")
            continue
        while True:
            bal_raw = input("  Balance: ").strip()
            try:
                balance = _parse_money_value(bal_raw)
                break
            except Exception:
                print("  Enter a valid number.")
        floor_raw = input("  Target floor / buffer [default 0]: ").strip()
        target_floor = 0.0 if floor_raw == "" else _parse_money_value(floor_raw)
        purpose = input("  Purpose [default bucket]: ").strip() or "bucket"
        notes = input("  Notes [optional]: ").strip()
        rows.append(
            {
                "snapshot_date": snapshot_date,
                "account_name": account_name,
                "balance": balance,
                "target_floor": target_floor,
                "purpose": purpose,
                "notes": notes,
                "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    if not rows:
        print("No balance snapshot rows entered.")
        return

    save_balance_snapshots(pd.DataFrame(rows))
    print(f"\nSaved {len(rows)} balance snapshot rows for {snapshot_date} into {BALANCE_DB_FILE}.")


def show_account_balance_trend_and_funding_status():
    df = load_balance_snapshots()
    if df.empty:
        print("\nNo account balance snapshots found yet. Use the balance-entry menu option first.")
        return

    df["snapshot_date_dt"] = pd.to_datetime(df["snapshot_date"], errors="coerce")
    df = df[df["snapshot_date_dt"].notna()].copy()
    if df.empty:
        print("\nNo valid dated balance snapshots found.")
        return

    latest_date = df["snapshot_date_dt"].max()
    latest = (
        df[df["snapshot_date_dt"].eq(latest_date)]
        .sort_values(["account_name", "captured_at"])
        .drop_duplicates(subset=["account_name"], keep="last")
        .copy()
    )
    prev = (
        df[df["snapshot_date_dt"] < latest_date]
        .sort_values(["snapshot_date_dt", "account_name", "captured_at"])
        .drop_duplicates(subset=["account_name"], keep="last")
        .copy()
    )
    prev_map = prev.set_index("account_name")["balance"].to_dict() if not prev.empty else {}

    latest["surplus"] = latest["balance"] - latest["target_floor"]
    latest["delta_prev"] = latest["account_name"].map(prev_map)
    latest["delta_prev"] = latest.apply(
        lambda r: (float(r["balance"]) - float(r["delta_prev"])) if pd.notna(r["delta_prev"]) else np.nan,
        axis=1,
    )
    latest["status"] = np.where(latest["surplus"] >= 0, "Funded", "Below target")

    print("\n=== ACCOUNT BALANCE SNAPSHOT STATUS ===")
    print(f"Latest snapshot date: {latest_date.strftime('%Y-%m-%d')}")
    print(f"SQLite file: {BALANCE_DB_FILE}")
    print(
        f"{'Account':<18} | {'Purpose':<14} | {'Balance':>12} | {'Target':>12} | "
        f"{'Surplus':>12} | {'Prev Delta':>12} | {'Status':<12}"
    )
    print("-" * 104)
    for _, row in latest.sort_values(["purpose", "account_name"]).iterrows():
        delta_txt = f"${float(row['delta_prev']):>11,.2f}" if pd.notna(row["delta_prev"]) else "     (n/a)"
        print(
            f"{str(row['account_name'])[:18]:<18} | {str(row['purpose'])[:14]:<14} | "
            f"${float(row['balance']):>11,.2f} | ${float(row['target_floor']):>11,.2f} | "
            f"${float(row['surplus']):>11,.2f} | {delta_txt:>12} | {str(row['status']):<12}"
        )

    total_balance = float(latest["balance"].sum())
    total_target = float(latest["target_floor"].sum())
    total_surplus = float(latest["surplus"].sum())
    funded_count = int((latest["surplus"] >= 0).sum())
    print("-" * 104)
    print(
        f"{'TOTAL':<18} | {'':<14} | ${total_balance:>11,.2f} | ${total_target:>11,.2f} | "
        f"${total_surplus:>11,.2f} | {'':>12} | {f'{funded_count}/{len(latest)} funded':<12}"
    )

    summary = (
        df.groupby("snapshot_date", as_index=False)
        .agg(total_balance=("balance", "sum"), total_target=("target_floor", "sum"))
        .sort_values("snapshot_date")
    )
    summary["surplus"] = summary["total_balance"] - summary["total_target"]
    print("\n--- Snapshot Totals Over Time ---")
    print(f"{'Date':<12} | {'Total Balance':>14} | {'Total Target':>13} | {'Above Floors':>13}")
    print("-" * 60)
    for _, row in summary.tail(12).iterrows():
        print(
            f"{str(row['snapshot_date']):<12} | ${float(row['total_balance']):>13,.2f} | "
            f"${float(row['total_target']):>12,.2f} | ${float(row['surplus']):>12,.2f}"
        )

    print("\n--- Account Trends ---")
    for account_name, grp in df.sort_values("snapshot_date_dt").groupby("account_name"):
        first = grp.iloc[0]
        last = grp.iloc[-1]
        delta = float(last["balance"]) - float(first["balance"])
        print(
            f"  - {account_name}: {first['snapshot_date']} ${float(first['balance']):,.2f} -> "
            f"{last['snapshot_date']} ${float(last['balance']):,.2f} ({delta:+,.2f})"
        )


# --- Simple SVG chart helpers (no external deps) ---
def _svg_header(width: int, height: int) -> str:
    return f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"


def _html_wrap(title: str, body: str) -> str:
    css = (
        "<style>"
        "body{font-family:Consolas,'Courier New',monospace;font-size:11pt;margin:0.5in;}"
        "h1{margin:0 0 12px 0;} h2{margin:12px 0 8px 0;}"
        "@page{size:A4 landscape;margin:0.5in;}"
        "</style>"
    )
    return f"<html><head>{css}<title>{title}</title></head><body><h1>{title}</h1>{body}</body></html>"


def cash_flow_by_month_chart_html():
    """Generate an HTML page with an inline SVG chart of Income/Expenses/Net by month."""
    df = load_main_df()
    cf = compute_inflow_outflow(df)
    months = _ordered_months()
    inc = [float(cf.loc[cf["Month"].astype(str)==m, "inflow"].sum()) for m in months]
    exp = [float(cf.loc[cf["Month"].astype(str)==m, "outflow"].sum()) for m in months]
    net = [i - e for i, e in zip(inc, exp)]
    labels = [m[:3] for m in months]

    max_val = max([*inc, *exp, *[abs(n) for n in net]] + [1.0])
    width, height = 1100, 420
    left, right, top, bottom = 60, 20, 30, 60
    chart_w = width - left - right
    chart_h = height - top - bottom
    bar_group_w = chart_w / len(months)
    bar_w = bar_group_w * 0.32

    def y(v: float) -> float:
        return top + chart_h - (v / max_val) * chart_h

    parts = [_svg_header(width, height)]
    # Axes
    parts.append(f"<line x1='{left}' y1='{top+chart_h}' x2='{left+chart_w}' y2='{top+chart_h}' stroke='#333' stroke-width='1' />")
    parts.append(f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top+chart_h}' stroke='#333' stroke-width='1' />")

    # Bars and net line
    points = []
    for i, (inc_v, exp_v, net_v) in enumerate(zip(inc, exp, net)):
        cx = left + bar_group_w * (i + 0.5)
        # Income (green)
        x_inc = cx - bar_w * 1.1
        parts.append(f"<rect x='{x_inc:.1f}' y='{y(inc_v):.1f}' width='{bar_w:.1f}' height='{(top+chart_h - y(inc_v)):.1f}' fill='#2e7d32' />")
        # Expense (red)
        x_exp = cx + bar_w * 0.1
        parts.append(f"<rect x='{x_exp:.1f}' y='{y(exp_v):.1f}' width='{bar_w:.1f}' height='{(top+chart_h - y(exp_v)):.1f}' fill='#c62828' />")
        # Net point (blue)
        px, py = cx, y(net_v)
        points.append((px, py))
        parts.append(f"<circle cx='{px:.1f}' cy='{py:.1f}' r='3' fill='#1565c0' />")
        # X labels
        parts.append(f"<text x='{cx:.1f}' y='{top+chart_h+16}' text-anchor='middle' font-size='10'>{labels[i]}</text>")

    # Net line
    poly = " ".join([f"{px:.1f},{py:.1f}" for px, py in points])
    parts.append(f"<polyline fill='none' stroke='#1565c0' stroke-width='2' points='{poly}' />")

    # Legend
    lx, ly = left + 10, top + 10
    parts.append(f"<rect x='{lx}' y='{ly}' width='10' height='10' fill='#2e7d32' /><text x='{lx+16}' y='{ly+10}' font-size='11'>Income</text>")
    parts.append(f"<rect x='{lx+90}' y='{ly}' width='10' height='10' fill='#c62828' /><text x='{lx+106}' y='{ly+10}' font-size='11'>Expenses</text>")
    parts.append(f"<line x1='{lx+200}' y1='{ly+5}' x2='{lx+215}' y2='{ly+5}' stroke='#1565c0' stroke-width='2' /><text x='{lx+220}' y='{ly+10}' font-size='11'>Net</text>")

    parts.append("</svg>")

    html = _html_wrap("Cash Flow by Month (Chart)", "".join(parts))
    out_dir = os.path.join("exports", EXPORTS_SUBDIR) if (EXPORTS_SUBDIR and str(EXPORTS_SUBDIR).strip()) else "exports"
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = os.path.join(out_dir, f"Cash_Flow_By_Month_Chart_{ts}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved: {path}")


def category_insights_chart_html(topn: int = 10):
    """Top-N categories by YTD spend as a horizontal bar chart (SVG in HTML)."""
    df0 = load_main_df()
    cf0 = compute_inflow_outflow(df0)
    exp = cf0[cf0["is_expense"]].copy()
    if exp.empty:
        print("No expense rows found.")
        return
    exp["AmountAbs"] = exp["Amount"].abs()
    by_cat = exp.groupby("Category")["AmountAbs"].sum().sort_values(ascending=False).head(int(topn))

    cats = ["(Uncategorized)" if (pd.isna(c) or str(c).strip()=="") else str(c) for c in by_cat.index]
    vals = [float(v) for v in by_cat.values]
    max_val = max(vals + [1.0])

    width, height = 1000, max(200, 30 + 26*len(cats))
    left, right, top, bottom = 180, 30, 20, 20
    chart_w = width - left - right

    parts = [_svg_header(width, height)]
    # Bars
    for i, (label, v) in enumerate(zip(cats, vals)):
        y = top + i*26
        w = (v / max_val) * chart_w
        parts.append(f"<rect x='{left}' y='{y}' width='{w:.1f}' height='18' fill='#1565c0' />")
        parts.append(f"<text x='{left-6}' y='{y+13}' text-anchor='end' font-size='11'>{label[:28]}</text>")
        parts.append(f"<text x='{left+w+6}' y='{y+13}' font-size='11'>${v:,.2f}</text>")
    parts.append("</svg>")

    html = _html_wrap("Category Insights (Top 10)", "".join(parts))
    out_dir = os.path.join("exports", EXPORTS_SUBDIR) if (EXPORTS_SUBDIR and str(EXPORTS_SUBDIR).strip()) else "exports"
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = os.path.join(out_dir, f"Category_Insights_Top10_Chart_{ts}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved: {path}")


def monthly_vs_average_chart_html(month_name: Optional[str] = None, topn: int = 10):
    """Side-by-side bars for This Month vs Avg/Month, Top-N by absolute diff."""
    import calendar
    df = load_main_df()
    dfn = normalize_transactions(df)
    if "date" not in dfn.columns or dfn["date"].isna().all():
        print("No usable dates found.")
        return
    valid_months = [calendar.month_name[m] for m in range(1,13)]
    if not month_name:
        sel = input("Enter month name for chart (e.g., August): ").strip().title()
        month_name = sel
    if month_name not in valid_months:
        print(f"Unknown month '{month_name}'. Valid: {', '.join(valid_months)}")
        return

    dsub = dfn[dfn["is_expense"]].copy()
    dsub["Month"] = dsub["date"].dt.month_name()
    dsub["category"] = dsub["category"].astype(str).fillna("Uncategorized")
    piv = dsub.pivot_table(index="category", columns="Month", values="outflow", aggfunc="sum", fill_value=0.0)
    this_m = piv.get(month_name) if month_name in piv.columns else pd.Series(0.0, index=piv.index)
    others = piv.drop(columns=[month_name]) if month_name in piv.columns else piv.copy()
    active_counts = (others > 0).sum(axis=1)
    avg_other = (others.sum(axis=1) / active_counts.replace(0,1)).where(active_counts>0, 0.0)
    diff = (this_m - avg_other).abs().sort_values(ascending=False)
    top_idx = diff.head(int(topn)).index

    cats = [str(c) for c in top_idx]
    vals_this = [float(this_m.get(c, 0.0)) for c in top_idx]
    vals_avg = [float(avg_other.get(c, 0.0)) for c in top_idx]
    max_val = max(vals_this + vals_avg + [1.0])

    width, height = 1000, max(220, 30 + 28*len(cats))
    left, right, top, bottom = 200, 30, 20, 20
    chart_w = width - left - right
    bar_h = 18

    parts = [_svg_header(width, height)]
    for i, (label, a, b) in enumerate(zip(cats, vals_this, vals_avg)):
        y = top + i*28
        w_a = (a / max_val) * chart_w
        w_b = (b / max_val) * chart_w
        parts.append(f"<text x='{left-8}' y='{y+13}' text-anchor='end' font-size='11'>{label[:28]}</text>")
        parts.append(f"<rect x='{left}' y='{y}' width='{w_a:.1f}' height='{bar_h}' fill='#1565c0' />")
        parts.append(f"<rect x='{left}' y='{y+bar_h+4}' width='{w_b:.1f}' height='{bar_h}' fill='#2e7d32' />")
        parts.append(f"<text x='{left+w_a+6}' y='{y+13}' font-size='11'>${a:,.2f}</text>")
        parts.append(f"<text x='{left+w_b+6}' y='{y+bar_h+4+13}' font-size='11'>${b:,.2f}</text>")
    # Legend
    lx, ly = left + 10, height - bottom - 10
    parts.append(f"<rect x='{lx}' y='{ly}' width='10' height='10' fill='#1565c0' /><text x='{lx+16}' y='{ly+10}' font-size='11'>This Month</text>")
    parts.append(f"<rect x='{lx+120}' y='{ly}' width='10' height='10' fill='#2e7d32' /><text x='{lx+136}' y='{ly+10}' font-size='11'>Avg/Month</text>")
    parts.append("</svg>")

    html = _html_wrap(f"Monthly vs Average (Chart) — {month_name}", "".join(parts))
    out_dir = os.path.join("exports", EXPORTS_SUBDIR) if (EXPORTS_SUBDIR and str(EXPORTS_SUBDIR).strip()) else "exports"
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = os.path.join(out_dir, f"Monthly_vs_Average_Chart_{month_name}_{ts}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved: {path}")

# --- Printer-friendly helpers (ASCII-only) ---
def _pf_delta(cur: float, prev: float | None) -> str:
    """ASCII delta string like '+1,234.56' or '-987.65'; empty if no previous."""
    if prev is None:
        return ""
    d = float(cur) - float(prev)
    if d == 0:
        return " 0.00"
    sign = "+" if d > 0 else "-"
    return f" {sign}{abs(d):,.2f}"

def _ordered_months():
    return [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]


def _completed_months_for_year(year: int) -> list[int]:
    """Return completed months for a given year (full 1-12 for past years)."""
    today = date.today()
    if int(year) == today.year:
        return list(range(1, today.month))
    return list(range(1, 13))


def cash_flow_by_month_printable():
    """Printer-friendly version of cash_flow_by_month (ASCII-only header/deltas)."""
    df = load_main_df()
    cf = compute_inflow_outflow(df)

    inc_by_m = cf.groupby("Month", observed=False)["inflow"].sum()
    exp_by_m = cf.groupby("Month", observed=False)["outflow"].sum()

    order = _ordered_months()
    months = [m for m in order if (m in inc_by_m.index) or (m in exp_by_m.index)]

    print("\nMonth       |     Income (chg)    |    Expenses (chg)   |        Net (chg)      | Status")
    print("----------------------------------------------------------------------------------------------")

    ytd = 0.0
    prev_inc = prev_exp = prev_net = None
    for m in months:
        inc = float(inc_by_m.get(m, 0.0))
        exp = float(exp_by_m.get(m, 0.0))
        net = inc - exp
        ytd += net
        status = "Surplus" if net >= 0 else "Deficit"
        print(
            f"{m:<11} | ${inc:>11,.2f} {_pf_delta(inc, prev_inc):>10} | "
            f"${exp:>11,.2f} {_pf_delta(exp, prev_exp):>10} | "
            f"${net:>12,.2f} {_pf_delta(net, prev_net):>10} | {status}"
        )
        prev_inc, prev_exp, prev_net = inc, exp, net

    print(f"\nYear-to-Date Net Cash Flow: ${ytd:,.2f}")

def cash_flow_by_month_export(write_xlsx: bool = True):
    """Export cash flow overview by month to CSV/XLSX/HTML (print-friendly)."""
    df = load_main_df()
    cf = compute_inflow_outflow(df)

    inc_by_m = cf.groupby("Month", observed=False)["inflow"].sum()
    exp_by_m = cf.groupby("Month", observed=False)["outflow"].sum()
    order = _ordered_months()

    rows = []
    for m in [x for x in order if (x in inc_by_m.index) or (x in exp_by_m.index)]:
        inc = float(inc_by_m.get(m, 0.0))
        exp = float(exp_by_m.get(m, 0.0))
        net = inc - exp
        status = "Surplus" if net >= 0 else "Deficit"
        rows.append({"Month": m, "Income": inc, "Expenses": exp, "Net": net, "Status": status})

    out_df = pd.DataFrame(rows, columns=["Month", "Income", "Expenses", "Net", "Status"])
    export_print_friendly(
        out_df,
        base_name="Cash_Flow_By_Month",
        currency_cols={"Income", "Expenses", "Net"},
        timestamped=True,
        write_xlsx=write_xlsx,
    )


def category_spend_insights_printable():
    """Printer-friendly: list ALL expense categories ranked by YTD total.

    Columns: Category | YTD Total | Avg/Active Mo | Highest Month (Amt) | Months
    Matches the logic used by option 14.
    """
    try:
        df0 = load_main_df()
        cf0 = compute_inflow_outflow(df0)
        exp = cf0[cf0["is_expense"]].copy()
        if exp.empty:
            print("No expense rows found.")
            return

        exp["AmountAbs"] = exp["Amount"].abs()
        piv = exp.pivot_table(index="Category", columns="Month", values="AmountAbs", aggfunc="sum", fill_value=0.0)
        months_present = (piv > 0).sum(axis=1)
        ytd = piv.sum(axis=1)
        active = months_present.replace(0, 1)
        avg_active = ytd / active
        hi_month = piv.idxmax(axis=1)
        hi_value = piv.max(axis=1)

        ordered_index = ytd.sort_values(ascending=False).index
        print("\nExpense categories (ranked by YTD total):")
        print(f"{'Category':<24} | {'YTD Total':>12} | {'Avg/Active Mo':>13} | {'Highest Month (Amt)':>22} | {'Months':>6}")
        print("-" * 92)
        for cat in ordered_index:
            label = "(Uncategorized)" if (pd.isna(cat) or str(cat).strip()=="") else str(cat)
            print(f"{label:<24} | ${ytd[cat]:>11,.2f} | ${avg_active[cat]:>12,.2f} | {hi_month[cat]:<9} (${hi_value[cat]:,.2f}) | {int(months_present[cat]):>6}")
    except Exception as exc:
        print(f"Error generating category insights: {exc}")

def category_spend_insights_export(min_months: int = 0, topn: Optional[int] = None, write_xlsx: bool = True):
    """Export category insights (YTD) to CSV/XLSX/HTML for printing from Excel."""
    df0 = load_main_df()
    cf0 = compute_inflow_outflow(df0)
    exp = cf0[cf0["is_expense"]].copy()
    if exp.empty:
        print("No expense rows found.")
        return

    exp["AmountAbs"] = exp["Amount"].abs()
    piv = exp.pivot_table(index="Category", columns="Month", values="AmountAbs", aggfunc="sum", fill_value=0.0)
    months_present = (piv > 0).sum(axis=1)
    ytd = piv.sum(axis=1)
    active = months_present.replace(0, 1)
    avg_active = ytd / active
    hi_month = piv.idxmax(axis=1)
    hi_value = piv.max(axis=1)

    if int(min_months) > 0:
        mask = months_present >= int(min_months)
        piv = piv[mask]
        months_present = months_present[mask]
        ytd = ytd[mask]
        avg_active = avg_active[mask]
        hi_month = hi_month[mask]
        hi_value = hi_value[mask]

    ordered = ytd.sort_values(ascending=False)
    if topn is not None:
        ordered = ordered.iloc[: int(topn)]

    rows = []
    for cat in ordered.index:
        label = "(Uncategorized)" if (pd.isna(cat) or str(cat).strip()=="") else str(cat)
        rows.append({
            "Category": label,
            "YTD Total": float(ytd[cat]),
            "Avg/Active Mo": float(avg_active[cat]),
            "Highest Month": str(hi_month[cat]),
            "Highest Month Amount": float(hi_value[cat]),
            "Months Active": int(months_present[cat]),
        })

    out_df = pd.DataFrame(rows, columns=[
        "Category", "YTD Total", "Avg/Active Mo", "Highest Month", "Highest Month Amount", "Months Active"
    ])
    export_print_friendly(
        out_df,
        base_name="Category_Insights",
        currency_cols={"YTD Total", "Avg/Active Mo", "Highest Month Amount"},
        number_cols={"Months Active"},
        timestamped=True,
        write_xlsx=write_xlsx,
    )

# --- Printer-friendly helpers ---
def _delta_ascii(cur, prev):
    if prev is None:
        return ""
    d = float(cur) - float(prev)
    if d == 0:
        return " 0.00"
    sign = "+" if d > 0 else "-"
    return f" {sign}{abs(d):,.2f}"

#_______________________
# this loads the sql table into the load_main_df to be used easily in functions. added 6_23_25

def load_main_df(year_tag: Optional[str] = None):
    year = _year_from_tag(year_tag) if year_tag is not None else None
    if year is None:
        year = get_active_year()
    db_file, table_name = get_db_info(year)
    engine = create_engine(f"sqlite:///{db_file}")
    return pd.read_sql_table(table_name, engine)


# --- CATEGORY LOADING ---
def load_category_map(filepath):
    df = pd.read_csv(filepath)
    df["keyword"] = df["keyword"].fillna("").astype(str).str.strip()
    df["category"] = df["category"].fillna("").astype(str).str.strip()
    df = df[(df["keyword"] != "") & (df["category"] != "")]
    return dict(zip(df["keyword"].str.lower(), df["category"]))

category_mapping = load_category_map(category_mapping_file)

def categorize_transaction(description, category_map):
    description = str(description).lower()
    for keyword, category in category_map.items():
        if keyword in description:
            return category
    return 'Uncategorized'

def apply_categorization(df, description_col='Description'):
       
    category_mapping = load_category_map(category_mapping_file)  # ← reload every time


    if description_col is None:
        if 'Transact' in df.columns:
            description_col = 'Transact'
        elif 'Description' in df.columns:
            description_col = 'Description'
        else:
            raise ValueError("❌ No valid description column found!")

    if description_col not in df.columns:
        raise KeyError(f"❌ Column '{description_col}' not found in DataFrame! Available columns: {df.columns.tolist()}")

    df['Category'] = df[description_col].apply(lambda desc: categorize_transaction(desc, category_mapping))
    return df

       
       
# --- ACCOUNT CSV CONFIGS ---
def build_account_csv_configs(year_tag: str) -> dict:
    return {
        "JEFF_CHECKING_USAA": {
            "filepath": f"JEFF_CHECKING_USAA_{year_tag}.csv",
            "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
            "account_name": "JEFF CHECKING"
        },
        "JEFF_SAVINGS_USAA": {
            "filepath": f"JEFF_SAVINGS_USAA_{year_tag}.csv",
            "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
            "account_name": "JEFF SAVINGS"
        },
        "JOINT_CHECKING_USAA": {
            "filepath": f"JOINT_CHECKING_USAA_{year_tag}.csv",
            "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
            "account_name": "JOINT CHECKING"
        },
        "USAA_VISA": {
            "filepath": f"USAA_VISA_{year_tag}.csv",
            "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
            "account_name": "USAA VISA"
        },
        "Ohenry_USAA": {
            "filepath": f"Ohenry_USAA_{year_tag}.csv",
            "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
            "account_name": "OHENRY"
        },
        "NANNY_USAA": {
            "filepath": f"NANNY_USAA_{year_tag}.csv",
            "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
            "account_name": "NANNY"
        },
        #### CHANGE THE CITY_VISA_YEAR CSV FILE HERE AFTER DOWNLOADING NEW ONE FOR THE MONTH!!!
        "City_Visa": {
            "filepath": "City_Visa_Year to date_download_3_24_2026.CSV",
            "columns": {"Amount": "Debit", "Description": "Description", "Date": "Date"},
            "account_name": "COSTCO CITY BANK",
            "strip_symbols_from_amount": True
        }
    }


account_csv_configs = build_account_csv_configs(YEAR)


# --- LOAD & NORMALIZE ---


# --- backup (optional) ---
# def load_account_data_original(config): 

# # paste your current load_account_data here for safekeeping


def load_account_data(config):
    df = pd.read_csv(config["filepath"])
    df = df.rename(columns={v: k for k, v in config["columns"].items()})

    if config.get("strip_symbols_from_amount", False):
        df["Amount"] = pd.to_numeric(df["Amount"].replace({'\\$': '', ',': ''}, regex=True), errors='coerce')
    else:
        df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce')

    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = pd.DatetimeIndex(df["Date"]).month_name()
    df["Description"] = df["Description"].fillna("").astype(str).str.strip()
    df["Transact"] = df["Description"]

    if "Original Description" in df.columns:
        df["Original_Description"] = df["Original Description"].fillna("").astype(str).str.strip()
        df["_CategoryText"] = (
            df["Transact"].astype(str).str.strip() + " " + df["Original_Description"].astype(str).str.strip()
        ).str.strip()
        df = apply_categorization(df, description_col="_CategoryText")
        df = df.drop(columns=["_CategoryText"])
    else:
        df = apply_categorization(df)

    df["ACCOUNT"] = config["account_name"]
    out_cols = ["Date", "Month", "Transact", "Amount", "Category", "ACCOUNT"]
    if "Original_Description" in df.columns:
        out_cols.append("Original_Description")
    return df[out_cols]



"""
def load_account_data(config):
    import pandas as pd

    df = pd.read_csv(config["filepath"])

    # Normalize columns using the mapping in config["columns"]
    df = df.rename(columns={v: k for k, v in config["columns"].items()})

    def to_num(s):
        return pd.to_numeric(s.replace({'\\$': '', ',': ''}, regex=True), errors='coerce') if isinstance(s, pd.Series) \
               else pd.to_numeric(s, errors='coerce')

    # Coerce the standard Amount if present
    if "Amount" in df.columns:
        if config.get("strip_symbols_from_amount", False):
            df["Amount"] = to_num(df["Amount"])
        else:
            df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    else:
        df["Amount"] = pd.NA

    # 🔒 Only do Debit/Credit merge for City Visa (by config name or account_name)
    is_city = str(config.get("account_name","")).upper() == "COSTCO CITY BANK"

    if is_city:
            # Coerce if present
        if "Debit" in df.columns:
            df["Debit"] = to_num(df["Debit"])
        if "Credit" in df.columns:
            df["Credit"] = to_num(df["Credit"])

        # Build Series defaults (never plain ints), aligned to df.index
        import pandas as pd
        zeros = pd.Series(0.0, index=df.index)

        debit  = df["Debit"]  if "Debit"  in df.columns else zeros
        credit = df["Credit"] if "Credit" in df.columns else zeros

        # Signed Amount: charges positive, payments/refunds negative
        df["Amount"] = (debit.fillna(0.0) - credit.fillna(0.0))

    # Derive standard fields
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Month"] = pd.DatetimeIndex(df["Date"]).month_name()
    df["Transact"] = df["Description"].astype(str)

    # Categorize + tag account
    df = apply_categorization(df)
    df["ACCOUNT"] = config["account_name"]

    # Guard: never leave NaN Amounts
    if df["Amount"].isna().any() and is_city:
        missing = int(df["Amount"].isna().sum())
        print(f"⚠️ {missing} City Visa rows had NaN Amount — set to 0.")
        df["Amount"] = df["Amount"].fillna(0)

    return df[["Date", "Month", "Transact", "Amount", "Category", "ACCOUNT"]]

"""



# 9_12_25

9
# ---- Column autodetection helpers ----
DATE_CANDIDATES       = ["date","transaction date","post date","posted date","date posted","trans date","posting date"]
ACCOUNT_CANDIDATES    = ["account","account name","accountname","acct","source account"]
CATEGORY_CANDIDATES   = ["category","type","cat"]
DESC_CANDIDATES       = ["description","memo","details","payee","name","merchant","narrative"]
DEBIT_CANDIDATES      = ["debit","charge","charges","withdrawal","withdrawals","outflow","amount debit","debits"]
CREDIT_CANDIDATES     = ["credit","payment","payments","deposit","deposits","inflow","amount credit","credits"]
AMOUNT_CANDIDATES     = ["amount","transaction amount","value","amt","net amount"]

def _pick_col(df, candidates):
    cols_lower = {c.lower(): c for c in df.columns}
    for alias in candidates:
        if alias in cols_lower:
            return cols_lower[alias]
    return None

def _ensure_col(df, name):
    if name not in df.columns:
        df[name] = ""


# --- REVIEW UNCATEGORIZED TRANSACTIONS ---
def show_uncategorized(df, n=25):
    uncategorized = df[df['Category'] == 'Uncategorized']
    print(f"\nFound {len(uncategorized)} uncategorized transactions:")
    print(uncategorized[['Date', 'Transact', 'Amount']].head(n))

    # Show most common uncategorized transaction descriptions
    print("\nTop uncategorized descriptions:")
    print(uncategorized['Transact'].value_counts().head(10))

# --- RE-CATEGORIZE FULL DB FROM EXISTING TABLE ---
def recategorize_full_table(db_path, table_name):
    engine = create_engine(f"sqlite:///{db_path}")
    df = pd.read_sql_table(table_name, engine)

    # 🧼 Strip whitespace from transaction descriptions
    df['Transact'] = df['Transact'].str.strip()

    # 🧮 Round float amounts to 2 decimal places to fix comparison
    df['Amount'] = df['Amount'].round(2)

    # Use both user-facing and original bank descriptions when available so
    # reward/credit rows are not forced through generic merchant rules.
    if 'Original_Description' in df.columns:
        df['_CategoryText'] = (
            df['Transact'].fillna('').astype(str).str.strip() + ' ' +
            df['Original_Description'].fillna('').astype(str).str.strip()
        ).str.strip()
        df = apply_categorization(df, description_col='_CategoryText')
        df = df.drop(columns=['_CategoryText'])
    else:
        df = apply_categorization(df, description_col='Transact')

    # 🎯 Manual override for specific rebate
    costco_cond = (df['Transact'].str.contains("Costco", case=False)) & (df['Amount'] == 1050.45)
    df.loc[costco_cond, 'Category'] = 'COSTCO REBATE'

    # Treat inbound USAA transfer of $2,000 as Social Security income
    usaa_cond = (
        df['Transact'].str.contains("USAA Transfer", case=False, na=False)
        & df['Amount'].round(2).eq(2000.00)  # positive inflow only
    )
    df.loc[usaa_cond, 'Category'] = 'S_S'

    ccpay_cond = (df['Transact'].str.contains("0822", case=False)) & (df['Amount'] == -13873.74)
    df.loc[ccpay_cond, 'Category'] = 'CC PAYMENT'

    # One-off Costco tires purchase (avoid misclassifying as Grocery)
    costco_tires_cond = (
        df['Transact'].str.contains("COSTCO WHSE #1086", case=False, na=False)
        & df['Amount'].round(2).eq(1036.47)
    )
    df.loc[costco_tires_cond, 'Category'] = 'Auto'


    
    # 🔎 Debug: show what matched
    print("Manual override applied to Costco:")
    print(df[costco_cond][['Date', 'Transact', 'Amount', 'Category']])

    print("Manual override applied to USAA Transfer:")
    print(df[usaa_cond][['Date', 'Transact', 'Amount', 'Category']])

    print("Manual override applied to CC Costco PAYMENT:")
    print(df[ccpay_cond][['Date', 'Transact', 'Amount', 'Category']])

    

    # 💾 Save re-categorized data back to DB
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print("Re-categorized table based on updated categories.csv and manual overrides.")



# --- CREATE DB ---
def create_data_base():
    db_path, table_name = get_db_info()
    engine = create_engine(f"sqlite:///{db_path}")
    all_dataframes = [load_account_data(cfg) for cfg in account_csv_configs.values()]
    ONE_BIG_ACCOUNT = pd.concat(all_dataframes, ignore_index=True)
    ONE_BIG_ACCOUNT.to_sql(table_name, engine, if_exists='replace', index=False)
    print("Streamlined DB created!")
    show_uncategorized(ONE_BIG_ACCOUNT)


# --- LOOKUP TRANSACTIONS BY MONTH & CATEGORY ---
def lookup_by_month_and_category():
    df = load_main_df()

    valid_months = df['Month'].dropna().unique()

    while True:
        month_input = input("\nEnter month name (e.g., March), or press Enter to return to main menu: ").strip()
        if month_input == "":
            print("\nReturning to main menu...\n")
            return  # Use return instead of break to properly return to main menu

        month_input = month_input.capitalize()
        if month_input not in valid_months:
            print("❌ That month is not in the database.")
            continue

        while True:
            filtered_df = df[df['Month'] == month_input]
            available_categories = sorted(filtered_df['Category'].unique())

            print("\n📂 Categories for", month_input)
            for i, cat in enumerate(available_categories, 1):
                print(f"{i}. {cat}")
            print(f"0. Back to month selection")

            cat_input = input("\nSelect a category by number (or press Enter to choose another month): ").strip()
            if cat_input == "":
                break
            try:
                cat_choice = int(cat_input)
                if cat_choice == 0:
                    break
                selected_cat = available_categories[cat_choice - 1]
            except (IndexError, ValueError):
                print("❌ Invalid category selection.")
                continue

            results = filtered_df[filtered_df['Category'] == selected_cat]
            print(f"\n🔍 Transactions in {month_input} under '{selected_cat}':")
            cols = ['Date', 'Month', 'Transact', 'Amount', 'Category', 'ACCOUNT']
            print(results[cols].sort_values('Date').to_string(index=False, max_colwidth=40, line_width=120))
          
            try:
                count = int(len(results))
                raw_total = float(results["Amount"].sum())
                pos = float(results.loc[results["Amount"] > 0, "Amount"].sum())
                neg = float(results.loc[results["Amount"] < 0, "Amount"].sum())
                cf_results = compute_inflow_outflow(results.copy())
                income_total = float(cf_results["inflow"].sum())
                expense_total = float(cf_results["outflow"].sum())

                print("\n" + "—" * 60)
                if expense_total and not income_total:
                    print(f"Expense total for '{selected_cat}' in {month_input}: ${expense_total:,.2f}  ({count} txns)")
                elif income_total and not expense_total:
                    print(f"Income total for '{selected_cat}' in {month_input}: ${income_total:,.2f}  ({count} txns)")
                else:
                    net_total = income_total - expense_total
                    print(f"Net total for '{selected_cat}' in {month_input}: ${net_total:,.2f}  ({count} txns)")
                    if income_total:
                        print(f"  Income total: ${income_total:,.2f}")
                    if expense_total:
                        print(f"  Expense total: ${expense_total:,.2f}")
                if pos and neg:
                    print(f"  • Sum of positives: ${pos:,.2f}")
                    print(f"  • Sum of negatives: ${neg:,.2f}")
                    print(f"  • Raw signed Amount sum: ${raw_total:,.2f}")
                print("—" * 60)
            except Exception as e:
                print(f"\n(Couldn’t compute total: {e})")

            see_all = input("\nWould you like to see all transactions for this month? (y/n or 'c' to compare with another month): ").strip().lower()
            #if see_all == 'y':
                #print(f"\n📅 All transactions in {month_input}:")
                #print(filtered_df[cols].sort_values('Date').to_string(index=False, max_colwidth=40, line_width=120))
            if see_all == 'y':
                # Normalize signs via SSOT
                month_df = filtered_df.copy()
                cf_month = compute_inflow_outflow(month_df)  # adds inflow/outflow/is_income/is_expense

                if cf_month.empty:
                    print("(No transactions)")
                    continue

                # 🔒 Hide excluded rows (transfers, CC payments, investments, rebates, etc.)
                cf_month = cf_month[(cf_month["is_income"]) | (cf_month["is_expense"])].copy()

                # Signed: + for income, - for expense
                cf_month["Signed"] = cf_month["inflow"] - cf_month["outflow"]

                # Tidy for display
                cf_month["Transact"] = cf_month["Transact"].astype(str).str.slice(0, 60)
                if "Description" in cf_month.columns:
                    cf_month["Description"] = cf_month["Description"].astype(str).str.slice(0, 60)

                # Rank categories by magnitude (income+expense)
                cf_month["AbsAmt"] = (cf_month["inflow"] + cf_month["outflow"])
                cat_order = (
                    cf_month.groupby("Category", observed=False)["AbsAmt"]
                            .sum()
                            .sort_values(ascending=False)
                            .index.tolist()
                )

                grand_inc = float(cf_month["inflow"].sum())
                grand_exp = float(cf_month["outflow"].sum())
                net = grand_inc - grand_exp

                print(f"\n📅 All transactions in {month_input} — grouped by Category\n")

                display_cols = [c for c in ["Date","Month","Transact","Description","ACCOUNT","Signed"] if c in cf_month.columns]

                for cat in cat_order:
                    block = cf_month[cf_month["Category"] == cat].copy()
                    if block.empty:
                        continue

                    is_income_cat = bool(block["is_income"].any())
                    cat_signed_total = float(block["Signed"].sum())
                    cat_total_display = cat_signed_total if is_income_cat else abs(cat_signed_total)
                    header_type = "Income" if is_income_cat else "Expense"

                    print(f"==== {cat} [{header_type}] — Total: ${cat_total_display:,.2f} — {len(block)} txns ====\n")

                    block = block.sort_values(["Date","Signed"], ascending=[True, False])
                    with pd.option_context("display.max_colwidth", 60, "display.width", 140):
                        print(block[display_cols].rename(columns={"Signed":"Amount (±)"}).to_string(index=False))
                    print("")

                print("—" * 72)
                print(f"Grand Income : ${grand_inc:,.2f}")
                print(f"Grand Expense: ${grand_exp:,.2f}")
                print(f"Net          : ${net:,.2f}  ({'Surplus' if net >= 0 else 'Deficit'})")
                print("—" * 72)
                continue


            
            elif see_all == 'c':
                compare_month = input("\nEnter another month to compare: ").strip().capitalize()
                if compare_month in valid_months:
                    compare_df = df[df['Month'] == compare_month]
                    print(f"\n📅 All transactions in {compare_month}:")
                    print(compare_df[cols].sort_values('Date').to_string(index=False, max_colwidth=40, line_width=120))
                else:
                    print("❌ That month is not in the database.")

            next_action = input("\nPress Enter to return to category list, or enter a category number to view another: ").strip()
            if next_action.isdigit():
                cat_num = int(next_action)
                if 1 <= cat_num <= len(available_categories):
                    selected_cat = available_categories[cat_num - 1]
                    results = filtered_df[filtered_df['Category'] == selected_cat]
                    print(f"\n🔍 Transactions in {month_input} under '{selected_cat}':")
                    print(results[cols].sort_values('Date').to_string(index=False, max_colwidth=40, line_width=120))
                    input("\nPress Enter to return to category list...")
                else:
                    print("❌ Invalid number, returning to category list.")
            else:
                continue




def display_monthly_and_quarterly_summary(year=None, include_incomplete=True):
    """
    Classic Option 5 output:
      - Prints Q1, Q2, Q3, Q4 blocks
      - Each block shows Category x Month table with 'Total' and 'Mean'
      - Uses normalize_transactions() => expenses-only (no transfers/paychecks/etc.)
    include_incomplete=True shows the current, in-progress month (mimics your old display that showed 0s).
    """
    import calendar
    from datetime import date

    # 1) Load and normalize (shared logic with Option 9)
    df = load_main_df()
    dfn = normalize_transactions(df)

    if "date" not in dfn.columns or dfn["date"].isna().all():
        print("\n=== QUARTERLY SUMMARY (expenses only) ===")
        print("No usable dates found.")
        return

    # Helpers
    def month_name(m): return calendar.month_name[m]
    def quarter_months(q): return [3*(q-1)+1, 3*(q-1)+2, 3*(q-1)+3]

    today = date.today()
    year = int(year) if year is not None else get_active_year()
    current_q = (today.month - 1) // 3 + 1
    def print_quarter(q):
        # Which months belong to this quarter
        q_months = quarter_months(q)

        # If we don't want to show in-progress months, drop months >= current month for the current quarter
        if not include_incomplete and (q == current_q) and (year == today.year):
            q_months = [m for m in q_months if m < today.month]

        # Build subset (expenses only)
        mask = (
            (dfn["date"].dt.year == year) &
            (dfn["date"].dt.month.isin(q_months)) &
            (dfn["is_expense"])
        )
        dsub = dfn.loc[mask, ["date","category","outflow"]].copy()
        dsub["category"] = dsub["category"].astype(str).fillna("Uncategorized")
        dsub["Month"] = dsub["date"].dt.month_name()

        # Build pivot Category x Month
        if dsub.empty:
            # Create an empty table with the correct columns to mirror the old layout
            cols = [month_name(m) for m in quarter_months(q)]
            pivot = pd.DataFrame(columns=cols + ["Total", "Mean"])
            pivot.index.name = "Category"
            pivot.columns.name = "Month"
        else:
            pivot = (
                dsub.pivot_table(
                    index="category",
                    columns="Month",
                    values="outflow",
                    aggfunc="sum",
                    fill_value=0.0,
                )
            )

            # Ensure quarter months appear in order (even if 0)
            for ml in [month_name(m) for m in quarter_months(q)]:
                if ml not in pivot.columns:
                    pivot[ml] = 0.0
            # Reorder columns strictly: three months for the quarter
            pivot = pivot[[month_name(m) for m in quarter_months(q)]]

            # Add Total and Mean
            pivot["Total"] = pivot.sum(axis=1)
            pivot["Mean"] = pivot[[month_name(m) for m in quarter_months(q)]].mean(axis=1)

            # Sort by Total desc; round for display; set labels like your old output
            pivot = pivot.sort_values("Total", ascending=False).round(2)
            pivot.index.name = "Category"
            pivot.columns.name = "Month"

        # Header like your old printout
        print(f"\n===== Q{q} Summary =====\n")
        # Pretty-print (trim very long names to keep width reasonable)
        if not pivot.empty:
            show = pivot.copy()
            show.index = [str(c)[:28] for c in show.index]
            print(show.to_string())
        else:
            # Keep the same look when empty
            empty = pd.DataFrame(columns=[month_name(m) for m in quarter_months(q)] + ["Total", "Mean"])
            empty.index.name = "Category"
            empty.columns.name = "Month"
            print(empty.to_string())

    # 2) Print Q1..Q4 blocks in order, like before
    for q in range(1, 5):
        print_quarter(q)



def display_quarterly_income_summary(year=None, include_incomplete=True):
    """
    Companion to Option 5: Quarterly summary for INCOME only.
      - Prints Q1..Q4 blocks
      - Each block shows Income Category x Month table with 'Total' and 'Mean'
      - Uses compute_inflow_outflow() so it matches the cash‑flow rules
    include_incomplete=True shows the current, in‑progress month in the current quarter.
    """
    import calendar
    from datetime import date

    df = load_main_df()
    cf = compute_inflow_outflow(df)  # has inflow/outflow/is_income/is_expense

    if "Date" not in cf.columns or cf["Date"].isna().all():
        print("\n=== QUARTERLY INCOME SUMMARY ===")
        print("No usable dates found.")
        return

    # Helpers
    def month_name(m):
        return calendar.month_name[m]

    def quarter_months(q):
        return [3 * (q - 1) + 1, 3 * (q - 1) + 2, 3 * (q - 1) + 3]

    today = date.today()
    year = int(year) if year is not None else get_active_year()
    current_q = (today.month - 1) // 3 + 1
    def print_quarter(q):
        q_months = quarter_months(q)
        if not include_incomplete and (q == current_q) and (year == today.year):
            q_months = [m for m in q_months if m < today.month]

        mask = (
            (cf["Date"].dt.year == year)
            & (cf["Date"].dt.month.isin(q_months))
            & (cf["is_income"])
        )
        dsub = cf.loc[mask, ["Date", "Category", "inflow"]].copy()
        if dsub.empty:
            cols = [month_name(m) for m in quarter_months(q)]
            pivot = pd.DataFrame(columns=cols + ["Total", "Mean"])
            pivot.index.name = "Category"
            pivot.columns.name = "Month"
        else:
            dsub["Category"] = dsub["Category"].astype(str).fillna("Uncategorized")
            dsub["Month"] = dsub["Date"].dt.month_name()
            pivot = (
                dsub.pivot_table(
                    index="Category",
                    columns="Month",
                    values="inflow",
                    aggfunc="sum",
                    fill_value=0.0,
                )
            )
            # Ensure quarter month columns exist (zero if missing)
            for ml in [month_name(m) for m in quarter_months(q)]:
                if ml not in pivot.columns:
                    pivot[ml] = 0.0
            pivot = pivot[[month_name(m) for m in quarter_months(q)]]

            pivot["Total"] = pivot.sum(axis=1)
            pivot["Mean"] = pivot[[month_name(m) for m in quarter_months(q)]].mean(axis=1)
            pivot = pivot.sort_values("Total", ascending=False).round(2)
            pivot.index.name = "Category"
            pivot.columns.name = "Month"

        print(f"\n===== Q{q} Income Summary =====\n")
        if not pivot.empty:
            show = pivot.copy()
            show.index = [str(c)[:28] for c in show.index]
            print(show.to_string())
        else:
            empty = pd.DataFrame(columns=[month_name(m) for m in quarter_months(q)] + ["Total", "Mean"])
            empty.index.name = "Category"
            empty.columns.name = "Month"
            print(empty.to_string())

    for q in range(1, 5):
        print_quarter(q)


def monthly_vs_average_expenses(year: int | None = None, month_name: str | None = None):
    """Compare one month's expense totals per category vs that category's average month in the year.

    Output columns:
      - Category | This Month | Avg/Month (excl. selected) | Diff | % Change

    Notes:
      - Uses normalize_transactions (aligned with cash-flow rules) → expenses only
      - Averages are computed across the other months in the same year where the category had any spend
      - If a category has no other-month activity, Avg/Month is 0 and % Change is shown as N/A
    """
    import calendar
    from datetime import date

    # Load normalized expenses
    df = load_main_df()
    dfn = normalize_transactions(df)

    if "date" not in dfn.columns or dfn["date"].isna().all():
        print("\n=== Monthly vs Average (expenses) ===")
        print("No usable dates found.")
        return

    year = int(year) if year is not None else get_active_year()

    # Prompt for month if needed
    valid_months = [calendar.month_name[m] for m in range(1, 13)]
    if not month_name:
        month_name = input("Enter month name (e.g., August): ").strip().title()
    if month_name not in valid_months:
        print(f"Unknown month '{month_name}'. Valid: {', '.join(valid_months)}")
        return

    # Filter this year and build monthly totals per category
    dsub = dfn[(dfn["date"].dt.year == year) & (dfn["is_expense"])].copy()
    if dsub.empty:
        print(f"\n=== Monthly vs Average (expenses) — {month_name} {year} ===")
        print("No expense rows found for the selected year.")
        return

    dsub["Month"] = dsub["date"].dt.month_name()
    dsub["category"] = dsub["category"].astype(str).fillna("Uncategorized")

    # Pivot: Category x Month → outflow sum
    piv = (
        dsub.pivot_table(index="category", columns="Month", values="outflow", aggfunc="sum", fill_value=0.0)
           .reindex(columns=valid_months, fill_value=0.0)
    )

    # Extract this-month values
    this_m = piv.get(month_name)
    if this_m is None:
        # Should not happen due to reindex, but safer to guard
        this_m = pd.Series(0.0, index=piv.index)

    # Compute average across other months where the category is active (non-zero)
    others = piv.drop(columns=[month_name]) if month_name in piv.columns else piv.copy()
    active_counts = (others > 0).sum(axis=1)
    sums_others = others.sum(axis=1)
    # Avoid div-by-zero; where active_counts==0, avg=0
    avg_other = sums_others / active_counts.replace(0, 1)
    avg_other = avg_other.where(active_counts > 0, 0.0)

    diff = this_m - avg_other
    with pd.option_context('display.float_format', lambda v: f"{v:,.2f}"):
        # Build a tidy table for print
        out = pd.DataFrame({
            "This Month": this_m,
            "Avg/Month": avg_other,
            "Diff": diff,
        })
        # Percent change vs average
        pct = pd.Series(index=out.index, dtype=float)
        nonzero_avg = out["Avg/Month"].replace(0.0, pd.NA)
        pct = (out["This Month"] - nonzero_avg) / nonzero_avg * 100.0
        out["% Change"] = pct.round(2).astype("Float64")  # keep NaN as <NA>

        # Sort by absolute Diff desc
        out = out.sort_values(by="Diff", key=lambda s: s.abs(), ascending=False)

        print(f"\n=== Monthly vs Average (expenses) — {month_name} {year} ===\n")
        # Format category names similar to option 5
        show = out.round(2).copy()
        show.index = [str(c)[:28] for c in show.index]
        print(show.to_string())


## 9_15_24 
def emergency_fund_from_raw():
    """
    Compute average monthly expenses from RAW DB (no fancy normalize):
      - Treat expenses as absolute Amount for rows that are NOT income/transfers/investments/etc.
      - ALWAYS include Category == 'Mortgage'
      - Use completed months this year
    Also prints top categories for the last completed month.
    """
    import pandas as pd
    from datetime import date

    df = load_main_df().copy()

    # Required columns
    need = {"Date","Amount","Category"}
    if not need.issubset(df.columns):
        print(f"DB is missing required columns: {need - set(df.columns)}")
        return

    # Types
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df = df[df["Date"].notna() & df["Amount"].notna()].copy()

    # Category text
    cat = df["Category"].astype(str)
    cat_lo = cat.str.strip().str.lower()
    cat_up = cat.str.strip().str.upper()

    # Category buckets (tune here only)
    income_cats = {"PAYCHECK","S_S","INCOME ? KP","WORK"}
    exclude_cats = {
        "SECURITY","CITY CC PAYMENT","USAA CC PAYMENT","TRANSFER",
        "COSTCO REBATE","ACCOUNT INTEREST","CC PAYMENT","VANGUARD INVESTMENT","INVESTMENT"
    }

    is_mortgage = cat_lo.eq("mortgage")
    is_income   = cat_up.isin(income_cats)
    is_excluded = cat_up.isin(exclude_cats)

    # Expense selection: NOT income, NOT excluded, OR Mortgage
    is_expense = (~is_income & ~is_excluded) | is_mortgage

    df["outflow"] = 0.0
    df.loc[is_expense, "outflow"] = df.loc[is_expense, "Amount"].abs()

    # Completed months this year
    active_year = get_active_year()
    months = _completed_months_for_year(active_year)
    if not months:
        print("No completed months yet.")
        return

    # Per-month totals
    per = []
    used = []
    for m in months:
        mask = (df["Date"].dt.year == active_year) & (df["Date"].dt.month == m) & (df["outflow"] > 0)
        total = float(df.loc[mask, "outflow"].sum())
        used.append(f"{active_year}-{m:02d}")
        per.append(total)

    if not per:
        print("No expenses found in completed months.")
        return

    avg = sum(per) / len(per)

    print("\n=== EMERGENCY FUND ESTIMATE (RAW, category-based) ===")
    print("Months used:")
    for label, val in zip(used, per):
        print(f"  {label}: ${val:,.2f}")
    print(f"\nAverage monthly expenses: ${avg:,.2f}\n")
    for n in (6, 9, 12):
        print(f"{n}-month fund: ${avg*n:,.2f}")

    # Top categories for last completed month
    last_m = months[-1]
    mask_last = (df["Date"].dt.year == active_year) & (df["Date"].dt.month == last_m) & (df["outflow"] > 0)
    top = (df.loc[mask_last]
             .groupby(df.loc[mask_last, "Category"].astype(str))["outflow"]
             .sum()
             .sort_values(ascending=False)
             .head(12))
    print(f"\n--- Top categories in {active_year}-{last_m:02d} ---")
    if top.empty:
        print("  (none)")
    else:
        for k, v in top.items():
            print(f"  - {k}: ${v:,.2f}")


## THIS SHOWS ALL TRANSACTIONS UNDER EACH INDIVIDUAL CATEGORY SO I CAN SCAN THEM TO MAKE SURE
## THE TRANSACATIONS ARE CATEGORIZED CORRECTLY. 


def show_look_into_transactions():
    """Display transactions tagged as 'LOOK INTO' for quick review."""
    df = load_main_df()

    if 'Category' not in df.columns:
        print("No 'Category' column present in the database table.")
        return

    mask = df['Category'].astype(str).str.strip().str.lower() == 'look into'
    look_into_df = df.loc[mask].copy()

    if look_into_df.empty:
        print("\nNo 'LOOK INTO' transactions found.")
        return

    cols = [c for c in ['Date', 'Month', 'Transact', 'Amount', 'Category', 'ACCOUNT'] if c in look_into_df.columns]
    look_into_df = look_into_df.sort_values('Date')

    print(f"\nFound {len(look_into_df)} 'LOOK INTO' transactions:\n")
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 120):
        print(look_into_df[cols].to_string(index=False))

def print_nanny_tax_transactions_for_year(year: Optional[int] = None):
    """Print all NANNY TAX transactions for a selected year in copy/paste-friendly format."""
    target_year = int(year) if year is not None else get_active_year()
    df = load_main_df(_year_to_tag(target_year))

    if "Date" not in df.columns or "Category" not in df.columns:
        print("Required columns ('Date', 'Category') are missing in the database table.")
        return

    dfr = df.copy()
    dfr["Date"] = pd.to_datetime(dfr["Date"], errors="coerce")
    dfr["Amount"] = pd.to_numeric(dfr.get("Amount"), errors="coerce")

    mask = (
        dfr["Date"].dt.year.eq(target_year)
        & dfr["Category"].astype(str).str.strip().str.upper().eq("NANNY TAX")
    )
    rep = dfr.loc[mask].copy()

    if rep.empty:
        print(f"\nNo NANNY TAX transactions found for {target_year}.")
        return

    rep = rep.sort_values("Date")
    cols = [c for c in ["Date", "Month", "Transact", "Amount", "Category", "ACCOUNT"] if c in rep.columns]
    rep["Date"] = rep["Date"].dt.strftime("%Y-%m-%d")

    total = float(rep["Amount"].sum(skipna=True))
    total_abs = float(rep["Amount"].abs().sum(skipna=True))

    print(f"\nNANNY TAX transactions for {target_year}:")
    with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 180):
        print(rep[cols].to_string(index=False))
    print(f"\nCount: {len(rep)}")
    print(f"Net total (signed): ${total:,.2f}")
    print(f"Gross total (absolute): ${total_abs:,.2f}")

def show_taxes_paid_by_month(year: Optional[int] = None):
    """Show tax-related spending by month plus yearly total."""
    target_year = int(year) if year is not None else get_active_year()
    df = load_main_df(_year_to_tag(target_year))

    need = {"Date", "Amount", "Category"}
    miss = need - set(df.columns)
    if miss:
        print(f"Required columns missing: {miss}")
        return

    dfr = df.copy()
    dfr["Date"] = pd.to_datetime(dfr["Date"], errors="coerce")
    dfr["Amount"] = pd.to_numeric(dfr["Amount"], errors="coerce")
    dfr = dfr[dfr["Date"].notna() & dfr["Amount"].notna()].copy()
    dfr = dfr[dfr["Date"].dt.year.eq(target_year)].copy()

    if dfr.empty:
        print(f"\nNo rows found for {target_year}.")
        return

    cat_up = dfr["Category"].astype(str).str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
    is_tax = cat_up.str.contains(r"\bTAX\b", regex=True, na=False) | cat_up.str.contains("IRS", regex=False, na=False)
    tax_df = dfr.loc[is_tax].copy()

    if tax_df.empty:
        print(f"\nNo tax-category transactions found for {target_year}.")
        return

    tax_df["TaxPaid"] = tax_df["Amount"].abs()
    month_order = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]
    by_month = (
        tax_df.assign(Month=tax_df["Date"].dt.month_name())
        .groupby("Month")["TaxPaid"]
        .sum()
        .reindex(month_order)
        .dropna()
    )

    print(f"\n=== TAXES PAID BY MONTH ({target_year}) ===")
    print("Month       | Taxes Paid")
    print("-------------------------")
    for m, v in by_month.items():
        print(f"{m:<11} | ${float(v):>10,.2f}")

    total_paid = float(by_month.sum())
    print("-------------------------")
    print(f"TOTAL       | ${total_paid:>10,.2f}")

    by_cat = tax_df.groupby("Category")["TaxPaid"].sum().sort_values(ascending=False)
    print("\nTax category totals:")
    for cat, v in by_cat.items():
        print(f"  - {cat}: ${float(v):,.2f}")

def show_city_cc_payments_by_month_comparison(years: Optional[list[int]] = None):
    """Compare CITY CC PAYMENT totals by month across available years."""
    target_years = years if years is not None else [2024, 2025, 2026]
    month_order = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]

    series_by_year: dict[int, pd.Series] = {}
    available_years: list[int] = []

    for year in target_years:
        db_file, _table_name = get_db_info(year)
        if not os.path.exists(db_file):
            continue

        try:
            df = load_main_df(_year_to_tag(year))
        except Exception:
            continue

        need = {"Date", "Amount", "Category"}
        if not need.issubset(df.columns):
            continue

        dfr = df.copy()
        dfr["Date"] = pd.to_datetime(dfr["Date"], errors="coerce")
        dfr["Amount"] = pd.to_numeric(dfr["Amount"], errors="coerce")
        dfr = dfr[dfr["Date"].notna() & dfr["Amount"].notna()].copy()
        dfr = dfr[dfr["Date"].dt.year.eq(int(year))].copy()
        dfr = dfr[
            dfr["Category"].astype(str).str.upper().str.replace(r"\s+", " ", regex=True).str.strip().eq("CITY CC PAYMENT")
        ].copy()

        if dfr.empty:
            continue

        by_month = (
            dfr.assign(Month=dfr["Date"].dt.month_name(), Payment=dfr["Amount"].abs())
               .groupby("Month")["Payment"]
               .sum()
               .reindex(month_order)
        )
        series_by_year[int(year)] = by_month
        available_years.append(int(year))

    if not available_years:
        print("\nNo CITY CC PAYMENT data found in the available databases.")
        return

    print("\n=== COSTCO CREDIT CARD PAYMENTS BY MONTH ===")
    header = "Month       | " + " | ".join([f"{year:>10}" for year in available_years])
    divider = "-" * len(header)
    print(header)
    print(divider)

    totals: dict[int, float] = {year: 0.0 for year in available_years}
    for month in month_order:
        row_vals = []
        for year in available_years:
            value = series_by_year[year].get(month, np.nan)
            if pd.isna(value):
                row_vals.append(f"{'-':>10}")
            else:
                val = float(value)
                totals[year] += val
                row_vals.append(f"${val:>9,.2f}")
        print(f"{month:<11} | " + " | ".join(row_vals))

    print(divider)
    print("TOTAL       | " + " | ".join([f"${totals[year]:>9,.2f}" for year in available_years]))
    print("\nCategory used: CITY CC PAYMENT")
    print("Note: totals use absolute payment amounts and ignore non-numeric autopay rows.")

def show_all_transactions_grouped_by_category():
    import pandas as pd
    from sqlalchemy import create_engine

    df = load_main_df()

    df.columns = df.columns.str.strip()
    df = df.sort_values(by=['Category', 'Date'])

    categories = df['Category'].dropna().unique()

    for category in categories:
        print(f"\n==== CATEGORY: {category.upper()} ====\n")
        cat_df = df[df['Category'] == category]

        for _, row in cat_df.iterrows():
            print(f"{row['Date'].strftime('%Y-%m-%d')}   {row['Month']:6} {row['Transact'][:40]:<40} {row['Amount']:6.2f} {row['Category']:<15} {row['ACCOUNT']}")
    
    input("\n✅ Done. Press Enter to return to the main menu...")


# --- INCOME VS EXPENSES / MONTHLY CASH FLOW ---

#9_15_25
def cash_flow_by_month():
    df = load_main_df()
    cf = compute_inflow_outflow(df)

    inc_by_m = cf.groupby("Month", observed=False)["inflow"].sum()
    exp_by_m = cf.groupby("Month", observed=False)["outflow"].sum()

    order = ["January","February","March","April","May","June",
             "July","August","September","October","November","December"]
    months = [m for m in order if (m in inc_by_m.index) or (m in exp_by_m.index)]

    def delta(cur, prev):
        if prev is None: return ""
        d = cur - prev
        arrow = "⬆️" if d > 0 else ("⬇️" if d < 0 else "➖")
        return f"{arrow} {abs(d):,.2f}"

    print("\nMonth       |     Income (Δ)     |    Expenses (Δ)    |        Net (Δ)       | Status")
    print("----------------------------------------------------------------------------------------------")

    ytd = 0.0
    prev_inc = prev_exp = prev_net = None
    for m in months:
        inc = float(inc_by_m.get(m, 0.0))
        exp = float(exp_by_m.get(m, 0.0))
        net = inc - exp
        ytd += net
        status = "Surplus" if net >= 0 else "Deficit"
        print(f"{m:<11} | ${inc:>11,.2f} {delta(inc, prev_inc):>8} | "
              f"${exp:>11,.2f} {delta(exp, prev_exp):>8} | "
              f"${net:>12,.2f} {delta(net, prev_net):>8} | {status}")
        prev_inc, prev_exp, prev_net = inc, exp, net

    print(f"\n📊 Year-to-Date Net Cash Flow: ${ytd:,.2f}")

# 9_15_25
def cash_flow_drilldown(year=2025, month_name="August"):
    from sqlalchemy import create_engine
    import pandas as pd, re

    db_path, table_name = get_db_info(year)
    df = pd.read_sql_table(table_name,
                           create_engine(f"sqlite:///{db_path}")).copy()
    df["Date"]   = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df = df[(df["Date"].dt.year == year) & (df["Date"].dt.month_name() == month_name)]

    # Safe text
    def _s(col): return df[col].astype(str) if col in df.columns else pd.Series([""]*len(df), index=df.index)
    cat = df.get("Category", pd.Series([""]*len(df), index=df.index)).astype(str)
    cat_up = cat.str.upper().str.strip()
    cat_lo = cat.str.lower().str.strip()

    income_cats = {"PAYCHECK","S_S","S S","SS","SOCIAL SECURITY","SSA","SSA INCOME","INCOME ? KP","WORK"}
    exclude_cats = {
        "SECURITY","CITY CC PAYMENT","USAA CC PAYMENT","TRANSFER",
        "COSTCO REBATE","ACCOUNT INTEREST","CC PAYMENT","VANGUARD INVESTMENT","INVESTMENT"
    }
    text = (_s("Transact")+" "+_s("Description")+" "+_s("ACCOUNT")+" "+cat).str.lower()
    looks_ss = text.str.contains(r"(ssa\s*treas|treas\s*310\s*ssa|soc(?:ial)?\s*sec(?:urity)?|ssa\s*deposit)", na=False, regex=True)

    is_income   = cat_up.isin(income_cats) | looks_ss
    is_excluded = cat_up.isin(exclude_cats)
    is_mortgage = cat_lo.eq("mortgage")
    is_expense  = (~is_income & ~is_excluded) | is_mortgage

    inc = df[is_income].assign(AmountAbs=lambda x: x["Amount"].abs())
    exp = df[is_expense].assign(AmountAbs=lambda x: x["Amount"].abs())

    print(f"\n🔎 CASH-FLOW DRILLDOWN — {month_name} {year}")
    print("\nIncome sources by Category:")
    print(inc.groupby("Category")["AmountAbs"].sum().sort_values(ascending=False).to_string() if not inc.empty else "(none)")
    print("\nExpense buckets by Category:")
    print(exp.groupby("Category")["AmountAbs"].sum().sort_values(ascending=False).to_string() if not exp.empty else "(none)")

    print("\nTop 10 income lines:")
    print(inc[['Date','Transact','Amount','Category','ACCOUNT']].sort_values('AmountAbs', ascending=False).head(10).to_string(index=False))
    print("\nTop 15 expense lines:")
    print(exp[['Date','Transact','Amount','Category','ACCOUNT']].sort_values('AmountAbs', ascending=False).head(15).to_string(index=False))

    print(f"\nTotals → Income: ${inc['AmountAbs'].sum():,.2f} | Expenses: ${exp['AmountAbs'].sum():,.2f} | Net: ${(inc['AmountAbs'].sum()-exp['AmountAbs'].sum()):,.2f}")

# 6_24_25
def list_income_transactions_for_month():
    """Interactively list all income transactions included in a month's Income total.

    Uses the same classification rules as cash_flow_by_month/compute_inflow_outflow.
    """
    import calendar

    df = load_main_df()
    cf = compute_inflow_outflow(df)

    # Valid months present in data
    months_present = [m for m in [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ] if m in set(cf["Month"].dropna().astype(str))]

    if not months_present:
        print("No monthly data available.")
        return

    print("\nAvailable months: " + ", ".join(months_present))
    sel = input("Enter month name to list income transactions (blank to cancel): ").strip()
    if not sel:
        return

    sel_month = sel.title()
    if sel_month not in months_present:
        print(f"Unknown month '{sel}'. Valid: {', '.join(months_present)}")
        return

    inc_tx = cf[(cf["Month"].astype(str) == sel_month) & (cf["is_income"])].copy()
    if inc_tx.empty:
        print(f"\nNo income transactions found for {sel_month}.")
        return

    inc_tx["AmountAbs"] = inc_tx["Amount"].abs()
    cols = [c for c in ["Date","Month","Transact","Amount","Category","ACCOUNT"] if c in inc_tx.columns]
    inc_tx = inc_tx.sort_values("Date")

    print(f"\nIncome transactions included in {sel_month}:")
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 160):
        print(inc_tx[cols].to_string(index=False))
    print(f"\nTotal income for {sel_month}: ${inc_tx['AmountAbs'].sum():,.2f}")

    # Small pause to review
    input("\nDone. Press Enter to return to the menu...")

def list_expense_transactions_for_month_grouped():
    """Interactively list expense transactions for a month, grouped by category.

    Uses the same normalization and classification rules as cash_flow_by_month
    via compute_inflow_outflow, so totals match the summary.
    """
    df = load_main_df()
    cf = compute_inflow_outflow(df)

    # Determine available months from the data
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    months_present = [m for m in month_order if m in set(cf["Month"].dropna().astype(str))]
    if not months_present:
        print("No monthly data available.")
        return

    print("\nAvailable months: " + ", ".join(months_present))
    sel = input("Enter month name to list EXPENSE transactions (blank to cancel): ").strip()
    if not sel:
        return

    sel_month = sel.title()
    if sel_month not in months_present:
        print(f"Unknown month '{sel}'. Valid: {', '.join(months_present)}")
        return

    exp_tx = cf[(cf["Month"].astype(str) == sel_month) & (cf["is_expense"])].copy()
    if exp_tx.empty:
        print(f"\nNo expense transactions found for {sel_month}.")
        return

    exp_tx["AmountAbs"] = exp_tx["Amount"].abs()
    cols = [c for c in ["Date", "Month", "Transact", "Amount", "Category", "ACCOUNT"] if c in exp_tx.columns]

    # Order categories by total descending
    cat_totals = (
        exp_tx.groupby("Category", dropna=False)["AmountAbs"].sum().sort_values(ascending=False)
    )

    grand_total = exp_tx["AmountAbs"].sum()
    print(f"\nExpense transactions included in {sel_month} (grouped by category):")
    for cat, total in cat_totals.items():
        cat_label = "(Uncategorized)" if (pd.isna(cat) or str(cat).strip()=="") else str(cat)
        print(f"\n==== {cat_label} | Total: ${total:,.2f} ====")
        sub = exp_tx[exp_tx["Category"].astype(str) == str(cat)].sort_values("Date")
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 160):
            print(sub[cols].to_string(index=False))

    print(f"\nGrand total expenses for {sel_month}: ${grand_total:,.2f}")
    # Summary line: list categories counted as expenses this month
    cat_labels = [
        ("(Uncategorized)" if (pd.isna(c) or str(c).strip()=="") else str(c))
        for c in cat_totals.index
    ]
    if cat_labels:
        print("\nCategories counted as expenses this month were: " + ", ".join(cat_labels))
    input("\nDone. Press Enter to return to the menu...")

def list_expense_transactions_for_month_grouped_printable():
    """Printer-friendly (ASCII) version of 8.2: grouped expense transactions by month.

    - Prompts for a month name
    - Prints each expense category block with Total and transaction count
    - Rows use fixed, compact columns suitable for copy/paste to Notepad
    """
    df = load_main_df()
    cf = compute_inflow_outflow(df)

    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    months_present = [m for m in month_order if m in set(cf["Month"].dropna().astype(str))]
    if not months_present:
        print("No monthly data available.")
        return

    print("\nAvailable months: " + ", ".join(months_present))
    sel = input("Enter month name to list EXPENSE transactions (blank to cancel): ").strip()
    if not sel:
        return

    sel_month = sel.title()
    if sel_month not in months_present:
        print(f"Unknown month '{sel}'. Valid: {', '.join(months_present)}")
        return

    exp_tx = cf[(cf["Month"].astype(str) == sel_month) & (cf["is_expense"])].copy()
    if exp_tx.empty:
        print(f"\nNo expense transactions found for {sel_month}.")
        return

    exp_tx["AmountAbs"] = exp_tx["Amount"].abs()

    # Order categories by total descending
    cat_totals = (
        exp_tx.groupby("Category", dropna=False)["AmountAbs"].sum().sort_values(ascending=False)
    )

    grand_total = exp_tx["AmountAbs"].sum()
    print(f"\nExpense transactions included in {sel_month} (grouped by category):")
    for cat, total in cat_totals.items():
        cat_label = "(Uncategorized)" if (pd.isna(cat) or str(cat).strip()=="") else str(cat)
        block = exp_tx[exp_tx["Category"].astype(str) == str(cat)].copy()
        # Build compact, printable columns
        block["_Date"] = pd.to_datetime(block["Date"], errors="coerce").dt.strftime('%Y-%m-%d')
        block["_Transact"] = block.get("Transact").astype(str).str.replace(r"\s+"," ", regex=True).str.slice(0, 48)
        block["_Account"] = block.get("ACCOUNT").astype(str).str.slice(0, 20) if "ACCOUNT" in block.columns else ""
        block["_Amount"] = block["AmountAbs"].round(2)

        disp_cols = [c for c in ["_Date","_Transact","_Amount","_Account"] if c in block.columns]
        print(f"\n==== {cat_label} | Total: ${total:,.2f} | {len(block)} txns ====")
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 120,
                               'display.float_format', lambda v: f"{v:,.2f}"):
            print(block[disp_cols].rename(columns={"_Date":"Date","_Transact":"Transact","_Amount":"Amount","_Account":"Account"}).to_string(index=False))

    print(f"\nGrand total expenses for {sel_month}: ${grand_total:,.2f}")
    # Summary line: list categories counted as expenses this month
    cat_labels = [
        ("(Uncategorized)" if (pd.isna(c) or str(c).strip()=="") else str(c))
        for c in cat_totals.index
    ]
    if cat_labels:
        print("\nCategories counted as expenses this month were: " + ", ".join(cat_labels))
    
def list_expense_transactions_for_month_grouped_export(sel_month: Optional[str] = None, write_xlsx: bool = True):
    """Export expense transactions for a chosen month (grouped view data) to Excel/CSV/HTML.

    Produces a flat table suitable for Excel printing; filter/sort there as needed.
    """
    df = load_main_df()
    cf = compute_inflow_outflow(df)

    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    months_present = [m for m in month_order if m in set(cf["Month"].dropna().astype(str))]
    if not months_present:
        print("No monthly data available.")
        return

    print("\nAvailable months: " + ", ".join(months_present))
    if not sel_month:
        sel = input("Enter month name to EXPORT EXPENSE transactions (blank to cancel): ").strip()
        if not sel:
            return
        sel_month = sel.title()
    if sel_month not in months_present:
        print(f"Unknown month '{sel}'. Valid: {', '.join(months_present)}")
        return

    exp_tx = cf[(cf["Month"].astype(str) == sel_month) & (cf["is_expense"])].copy()
    if exp_tx.empty:
        print(f"\nNo expense transactions found for {sel_month}.")
        return

    exp_tx["AmountAbs"] = exp_tx["Amount"].abs()
    cols = [c for c in ["Category", "Date", "Month", "Transact", "Description", "Amount", "ACCOUNT"] if c in exp_tx.columns]
    out_df = exp_tx[cols].sort_values(["Category", "Date"], kind="stable").reset_index(drop=True)
    export_print_friendly(
        out_df,
        base_name=f"Expense_Transactions_{sel_month}",
        currency_cols={"Amount"} if "Amount" in out_df.columns else None,
        timestamped=True,
        write_xlsx=write_xlsx,
    )


def display_monthly_and_quarterly_summary_export(year=None, include_incomplete=True, write_xlsx: bool = True):
    """Export Option 5 (quarterly expense summary) to CSV/XLSX/HTML.

    One row per Category per Quarter with Month1, Month2, Month3, Total, Mean columns.
    """
    import calendar
    from datetime import date

    df = load_main_df()
    dfn = normalize_transactions(df)

    if "date" not in dfn.columns or dfn["date"].isna().all():
        print("No usable dates found for quarterly export.")
        return

    def month_name(m): return calendar.month_name[m]
    def quarter_months(q): return [3*(q-1)+1, 3*(q-1)+2, 3*(q-1)+3]

    today = date.today()
    year = int(year) if year is not None else get_active_year()
    current_q = (today.month - 1) // 3 + 1
    any_exported = False
    for q in range(1, 5):
        q_months = quarter_months(q)
        # For consistency with Option 5, show all three months of the quarter; if include_incomplete=False,
        # values for future months in current quarter will be 0.0
        mask = (
            (dfn["date"].dt.year == year)
            & (dfn["date"].dt.month.isin(q_months))
            & (dfn["is_expense"])
        )
        dsub = dfn.loc[mask, ["date","category","outflow"]].copy()
        dsub["category"] = dsub["category"].astype(str).fillna("Uncategorized")
        dsub["Month"] = dsub["date"].dt.month_name()

        pivot = (
            dsub.pivot_table(
                index="category",
                columns="Month",
                values="outflow",
                aggfunc="sum",
                fill_value=0.0,
            ) if not dsub.empty else pd.DataFrame()
        )

        labels = [month_name(m) for m in quarter_months(q)]
        # Ensure three month columns exist, even if zero
        for ml in labels:
            if ml not in pivot.columns:
                pivot[ml] = 0.0
        # Reorder strictly
        pivot = pivot[labels] if not pivot.empty else pd.DataFrame(columns=labels)
        # Totals
        pivot["Total"] = pivot.sum(axis=1) if not pivot.empty else []
        pivot["Mean"] = pivot[labels].mean(axis=1) if not pivot.empty else []

        # Build export frame for this quarter
        if pivot.empty:
            # Emit an empty structure with headers so the file exists
            out_df = pd.DataFrame(columns=["Category"] + labels + ["Total","Mean"])
        else:
            out_df = (
                pivot.sort_values("Total", ascending=False)
                     .reset_index()
                     .rename(columns={"index":"Category"})
            )

        export_print_friendly(
            out_df,
            base_name=f"Quarterly_Summary_{year}_Q{q}",
            currency_cols=set(labels) | {"Total","Mean"},
            timestamped=True,
            write_xlsx=write_xlsx,
        )
        any_exported = True

    if not any_exported:
        print("No quarterly expense data to export.")


def monthly_vs_average_expenses_export(year: Optional[int] = None, month_name: Optional[str] = None, write_xlsx: bool = True):
    """Export Option 5.2 (Monthly vs Average expenses) as CSV/XLSX/HTML."""
    import calendar
    from datetime import date

    df = load_main_df()
    dfn = normalize_transactions(df)
    if "date" not in dfn.columns or dfn["date"].isna().all():
        print("No usable dates found for monthly-vs-average export.")
        return

    year = int(year) if year is not None else get_active_year()
    valid_months = [calendar.month_name[m] for m in range(1, 13)]
    if not month_name:
        month_name = input("Enter month name for 5.2x (e.g., August): ").strip().title()
    if month_name not in valid_months:
        print(f"Unknown month '{month_name}'. Valid: {', '.join(valid_months)}")
        return

    dsub = dfn[(dfn["date"].dt.year == year) & (dfn["is_expense"])].copy()
    if dsub.empty:
        print("No expense rows for the selected year.")
        return

    dsub["Month"] = dsub["date"].dt.month_name()
    dsub["category"] = dsub["category"].astype(str).fillna("Uncategorized")

    piv = (
        dsub.pivot_table(index="category", columns="Month", values="outflow", aggfunc="sum", fill_value=0.0)
           .reindex(columns=valid_months, fill_value=0.0)
    )

    this_m = piv.get(month_name)
    if this_m is None:
        this_m = pd.Series(0.0, index=piv.index)

    others = piv.drop(columns=[month_name]) if month_name in piv.columns else piv.copy()
    active_counts = (others > 0).sum(axis=1)
    sums_others = others.sum(axis=1)
    avg_other = sums_others / active_counts.replace(0, 1)
    avg_other = avg_other.where(active_counts > 0, 0.0)

    diff = this_m - avg_other
    out = pd.DataFrame({
        "Category": this_m.index.astype(str),
        "This Month": this_m.values,
        "Avg/Month": avg_other.values,
        "Diff": diff.values,
    })
    # Percent change
    nonzero_avg = out["Avg/Month"].replace(0.0, pd.NA)
    pct = (out["This Month"] - nonzero_avg) / nonzero_avg * 100.0
    out["% Change"] = pct.astype("Float64").round(1)
    out = out.sort_values(by="Diff", key=lambda s: s.abs(), ascending=False)

    export_print_friendly(
        out,
        base_name=f"Monthly_vs_Average_{month_name}_{year}",
        currency_cols={"This Month","Avg/Month","Diff"},
        # Leave % Change as float with 2 decimals (handled by export rounding)
        timestamped=True,
        write_xlsx=write_xlsx,
    )


def monthly_review_exports():
    """Run a batch of exports: 5x, 5.2x, 8x, 8.2x, 14x.

    Prompts once for a month (used for 5.2x and 8.2x). Others run as-is.
    """
    from datetime import date, timedelta
    import calendar

    # Determine last completed month as default
    today = date.today()
    last_month_end = (today.replace(day=1) - timedelta(days=1))
    default_month = calendar.month_name[last_month_end.month]

    sel = input(f"Month for review (Enter for {default_month}): ").strip()
    month_name = sel.title() if sel else default_month

    try:
        display_monthly_and_quarterly_summary_export()
    except Exception as e:
        print(f"5x export failed: {e}")
    try:
        monthly_vs_average_expenses_export(month_name=month_name)
    except Exception as e:
        print(f"5.2x export failed: {e}")
    try:
        cash_flow_by_month_export()
    except Exception as e:
        print(f"8x export failed: {e}")
    try:
        list_expense_transactions_for_month_grouped_export(month_name)
    except Exception as e:
        print(f"8.2x export failed: {e}")
    try:
        category_spend_insights_export()
    except Exception as e:
        print(f"14x export failed: {e}")
    print("\nMonthly review exports completed. See the 'exports' folder.")


# --- HTML-only export wrappers ---
def cash_flow_by_month_export_html():
    cash_flow_by_month_export(write_xlsx=False)


def category_spend_insights_export_html():
    category_spend_insights_export(write_xlsx=False)


def list_expense_transactions_for_month_grouped_export_html():
    # Will prompt for month inside
    list_expense_transactions_for_month_grouped_export(write_xlsx=False)


def display_monthly_and_quarterly_summary_export_html():
    display_monthly_and_quarterly_summary_export(write_xlsx=False)


def monthly_vs_average_expenses_export_html():
    # Will prompt for month inside
    monthly_vs_average_expenses_export(write_xlsx=False)


def monthly_review_exports_html():
    """Run the export batch (5x, 5.2x, 8x, 8.2x, 14x) but HTML/CSV only (no XLSX)."""
    from datetime import date, timedelta
    import calendar

    today = date.today()
    last_month_end = (today.replace(day=1) - timedelta(days=1))
    default_month = calendar.month_name[last_month_end.month]

    sel = input(f"Month for HTML-only review (Enter for {default_month}): ").strip()
    month_name = sel.title() if sel else default_month

    try:
        display_monthly_and_quarterly_summary_export(write_xlsx=False)
    except Exception as e:
        print(f"5xh export failed: {e}")
    try:
        monthly_vs_average_expenses_export(month_name=month_name, write_xlsx=False)
    except Exception as e:
        print(f"5.2xh export failed: {e}")
    try:
        cash_flow_by_month_export(write_xlsx=False)
    except Exception as e:
        print(f"8xh export failed: {e}")
    try:
        list_expense_transactions_for_month_grouped_export(month_name, write_xlsx=False)
    except Exception as e:
        print(f"8.2xh export failed: {e}")
    try:
        category_spend_insights_export(write_xlsx=False)
    except Exception as e:
        print(f"14xh export failed: {e}")
    print("\nMonthly review HTML-only exports completed. See the 'exports' folder.")


def quarterly_summary_combined_export_html(year=None, include_incomplete=True):
    """Export all four quarterly expense summaries into a single HTML page (CSV/HTML only).

    Mirrors Option 5 layout per quarter, stacked Q1..Q4 on one page with print CSS.
    """
    import os
    import calendar
    from datetime import date, datetime

    def month_name(m):
        return calendar.month_name[m]

    def quarter_months(q):
        return [3 * (q - 1) + 1, 3 * (q - 1) + 2, 3 * (q - 1) + 3]

    df = load_main_df()
    dfn = normalize_transactions(df)
    if "date" not in dfn.columns or dfn["date"].isna().all():
        print("No usable dates found for combined quarterly export.")
        return

    year = int(year) if year is not None else get_active_year()

    os.makedirs("exports", exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_html = os.path.join("exports", f"Quarterly_Summary_{year}_Combined_{ts}.html")

    sections = []
    for q in range(1, 5):
        q_months = quarter_months(q)
        mask = (
            (dfn["date"].dt.year == year)
            & (dfn["date"].dt.month.isin(q_months))
            & (dfn["is_expense"]) 
        )
        dsub = dfn.loc[mask, ["date", "category", "outflow"]].copy()
        dsub["category"] = dsub["category"].astype(str).fillna("Uncategorized")
        dsub["Month"] = dsub["date"].dt.month_name()

        labels = [month_name(m) for m in quarter_months(q)]
        if dsub.empty:
            pivot = pd.DataFrame(columns=["Category"] + labels + ["Total", "Mean"])
        else:
            pivot = (
                dsub.pivot_table(index="category", columns="Month", values="outflow", aggfunc="sum", fill_value=0.0)
            )
            for ml in labels:
                if ml not in pivot.columns:
                    pivot[ml] = 0.0
            pivot = pivot[labels]
            pivot["Total"] = pivot.sum(axis=1)
            pivot["Mean"] = pivot[labels].mean(axis=1)
            pivot = pivot.sort_values("Total", ascending=False).reset_index()
            pivot = pivot.rename(columns={"category": "Category"}) if "category" in pivot.columns else pivot
            pivot[[*labels, "Total", "Mean"]] = pivot[[*labels, "Total", "Mean"]].apply(lambda s: pd.to_numeric(s, errors="coerce").round(2))
            pivot.insert(0, "Category", pivot.pop("category") if "category" in pivot.columns else pivot["Category"]) if "category" in pivot.columns or "Category" in pivot.columns else None
            pivot = pivot[["Category", *labels, "Total", "Mean"]]

        sections.append((q, labels, pivot))

    css = (
        "<style>"
        "body{font-family:Consolas,'Courier New',monospace;font-size:11pt;margin:0.5in;}"
        "h2{margin:0.2in 0 0.1in;}"
        "table{border-collapse:collapse;width:100%;margin-bottom:0.35in;}"
        "th,td{border:1px solid #999;padding:4px 6px;text-align:right;}"
        "th:first-child,td:first-child{text-align:left;}"
        "th{background:#f2f2f2;}"
        "@page{size:A4 landscape;margin:0.5in;}"
        "</style>"
    )

    html_parts = ["<html><head>", css, "</head><body>"]
    html_parts.append(f"<h1>Quarterly Expense Summary - {year}</h1>")
    for q, labels, tbl in sections:
        html_parts.append(f"<h2>Q{q}</h2>")
        html_parts.append(tbl.to_html(index=False, border=0))
    html_parts.append("</body></html>")

    with open(out_html, "w", encoding="utf-8") as f:
        f.write("".join(html_parts))

    print(f"Saved: {out_html}")

def review_monthly_expense_categories_with_comparison(db_path, year, month):
    from sqlalchemy import create_engine
    import pandas as pd
    import os

    def get_expenses_by_category(path, y, m):
        engine = create_engine(f"sqlite:///{path}")
        table_name = "NEW_ONE_BIG_ACCOUNT_data_2025" if "2025" in path else "ONE_BIG_ACCOUNT_data_2024"
        df = pd.read_sql_table(table_name, engine)

        # Filter expenses
        income_categories = ["PAYCHECK", "S_S", "INCOME ? KP", "Security", "WORK"]
        exclude_categories = ["Security", "CITY CC PAYMENT", "USAA CC PAYMENT", "TRANSFER", 
                              "COSTCO REBATE", "ACCOUNT INTEREST", "CC PAYMENT"]
        df = df[df["Amount"] > 0]
        df["Transact"] = df["Transact"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
        df = df[~df["Category"].isin(income_categories + exclude_categories)]
        df = df[df["Month"].str.lower() == m.lower()]
        df["Amount"] = df["Amount"].round(2)
        return df.groupby("Category")["Amount"].sum().sort_values(ascending=False), df

    # Load current year data
    current_totals, month_df = get_expenses_by_category(db_path, year, month)

    # Try loading previous year if available
    prev_year = str(int(year) - 1)
    prev_path = db_path.replace(year, prev_year)
    prev_totals = None
    if os.path.exists(prev_path):
        try:
            prev_totals, _ = get_expenses_by_category(prev_path, prev_year, month)
        except Exception:
            prev_totals = None

    # Prepare and display table
    all_cats = sorted(set(current_totals.index).union(set(prev_totals.index if prev_totals is not None else [])),
                      key=lambda x: current_totals.get(x, 0), reverse=True)

    print(f"\n📊 Category Spending Comparison - {month} {year} vs {prev_year if prev_totals is not None else '—'}")
    print(f"{'Category':<20} | {year} Amount | {prev_year if prev_totals is not None else '—'} Amount | Difference | Status")
    print("-" * 80)

    for cat in all_cats:
        cur = current_totals.get(cat, 0)
        prev = prev_totals.get(cat, 0) if prev_totals is not None else 0
        diff = cur - prev
        status = "⬆️ Higher" if diff > 0 else ("⬇️ Lower" if diff < 0 else "➖ Equal")
        print(f"{cat:<20} | ${cur:>10,.2f} | ${prev:>10,.2f} | ${diff:>9,.2f} | {status}")

    # Interactive drilldown
    while True:
        selected = input("\n🔍 Enter a category to list transactions or press Enter to skip: ").strip()
        if not selected:
            break
        if selected in month_df["Category"].unique():
            subset = month_df[month_df["Category"] == selected]
            subset["Transact"] = subset["Transact"].str.slice(0, 50)
            print(f"\n📋 Transactions in category '{selected}' - {month} {year}:\n")
            print(subset[["Date", "Transact", "Amount", "Category"]].to_string(index=False))
            print(f"\n🧮 Total for '{selected}': ${subset['Amount'].sum():,.2f}")
        else:
            print("⚠️ Category not found. Please try again.")

#9_15_25

def compare_cash_flow_2024_vs_2025():
    from sqlalchemy import create_engine

    def _load(db_path, table):
        return pd.read_sql_table(table, create_engine(f"sqlite:///{db_path}"))

    df24 = _load("ONE_BIG_ACCOUNT_combined_data2024.db", "ONE_BIG_ACCOUNT_data_2024")
    df25 = _load("ONE_BIG_ACCOUNT_combined_data2025.db", "NEW_ONE_BIG_ACCOUNT_data_2025")

    cf24 = compute_inflow_outflow(df24)
    cf25 = compute_inflow_outflow(df25)

    inc24 = cf24.groupby("Month", observed=False)["inflow"].sum()
    exp24 = cf24.groupby("Month", observed=False)["outflow"].sum()
    net24 = inc24.subtract(exp24, fill_value=0)

    inc25 = cf25.groupby("Month", observed=False)["inflow"].sum()
    exp25 = cf25.groupby("Month", observed=False)["outflow"].sum()
    net25 = inc25.subtract(exp25, fill_value=0)

    months = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]

    print("\n📊 COMPARISON: NET CASH FLOW (2024 vs 2025)")
    print("Month       | Net 2024     | Net 2025     | Difference     | Status")
    print("--------------------------------------------------------------------")
    total_diff = 0.0
    for m in months:
        a, b = float(net24.get(m, 0.0)), float(net25.get(m, 0.0))
        diff = b - a
        total_diff += diff
        status = "⬆️ Higher" if diff > 0 else ("⬇️ Lower" if diff < 0 else "➖ Equal")
        print(f"{m:<11} ${a:>10,.2f} | ${b:>10,.2f} | ${diff:>10,.2f}   {status}")
    print(f"\n🧮 Total Net Difference 2025 vs 2024: ${total_diff:,.2f}")

    print("\n📊 COMPARISON: INCOME (2024 vs 2025)")
    print("Month       | Income 2024  | Income 2025  | Difference     | Status")
    print("--------------------------------------------------------------------")
    inc_diff_total = 0.0
    for m in months:
        a, b = float(inc24.get(m, 0.0)), float(inc25.get(m, 0.0))
        d = b - a; inc_diff_total += d
        status = "⬆️ Higher" if d > 0 else ("⬇️ Lower" if d < 0 else "➖ Equal")
        print(f"{m:<11} ${a:>10,.2f} | ${b:>10,.2f} | ${d:>10,.2f}   {status}")
    print(f"\n🧮 Total Income Difference 2025 vs 2024: ${inc_diff_total:,.2f}")

    print("\n📊 COMPARISON: EXPENSES (2024 vs 2025)")
    print("Month       | Expense 2024 | Expense 2025 | Difference     | Status")
    print("--------------------------------------------------------------------")
    exp_diff_total = 0.0
    for m in months:
        a, b = float(exp24.get(m, 0.0)), float(exp25.get(m, 0.0))
        d = b - a; exp_diff_total += d
        status = "⬆️ Higher" if d > 0 else ("⬇️ Lower" if d < 0 else "➖ Equal")
        print(f"{m:<11} ${a:>10,.2f} | ${b:>10,.2f} | ${d:>10,.2f}   {status}")
    print(f"\n🧮 Total Expense Difference 2025 vs 2024: ${exp_diff_total:,.2f}")

#9_15_25
def forecast_year_end():
    """
    Forecast 2025 full-year net cash flow compared to 2024.

    Steps:
    1. Totals 2024 actual income, expenses, and net from the SQL database.
    2. Totals 2025 YTD (Jan–Sep) income, expenses, and net.
    3. Forecasts Oct–Dec 2025:
       - Expenses = 2025 YTD average monthly expenses.
       - Income = 2024 Oct–Dec average monthly income (assumes 401k max-out bump).
    4. Prints side-by-side results for 2024 actual vs 2025 forecast.
    """
    # --- Load 2024 + 2025 data ---
    df24 = pd.read_sql_table("ONE_BIG_ACCOUNT_data_2024",
                             create_engine("sqlite:///ONE_BIG_ACCOUNT_combined_data2024.db"))
    df25 = load_main_df()

    cf24 = compute_inflow_outflow(df24)
    cf25 = compute_inflow_outflow(df25)

    # --- 2024 totals ---
    inc24 = cf24["inflow"].sum()
    exp24 = cf24["outflow"].sum()
    net24 = inc24 - exp24

    # --- 2025 YTD (Jan–Sep) ---
    today = date.today()
    ytd_months = range(1, min(today.month, 10))  # up to September
    cf25_ytd = cf25[cf25["Date"].dt.month.isin(ytd_months)]

    inc25_ytd = cf25_ytd["inflow"].sum()
    exp25_ytd = cf25_ytd["outflow"].sum()
    net25_ytd = inc25_ytd - exp25_ytd

    avg_exp_2025 = exp25_ytd / len(ytd_months)

    # --- 2024 Q4 average income (to model 401k bump) ---
    cf24_q4 = cf24[cf24["Date"].dt.month.isin([10,11,12])]
    avg_inc_q4_2024 = cf24_q4["inflow"].sum() / 3

    # --- Forecast Oct–Dec 2025 ---
    inc25_forecast = avg_inc_q4_2024 * 3
    exp25_forecast = avg_exp_2025 * 3
    net25_forecast_q4 = inc25_forecast - exp25_forecast

    # --- Totals for 2025 forecast ---
    inc25_total = inc25_ytd + inc25_forecast
    exp25_total = exp25_ytd + exp25_forecast
    net25_total = net25_ytd + net25_forecast_q4

    # --- Print results ---
    print("\n📊 YEAR-END FORECAST (2024 vs 2025)")
    print("               |   2024 Actual   |   2025 Forecast")
    print("---------------------------------------------------")
    print(f"Income         | ${inc24:>12,.2f} | ${inc25_total:>12,.2f}")
    print(f"Expenses       | ${exp24:>12,.2f} | ${exp25_total:>12,.2f}")
    print(f"Net Cash Flow  | ${net24:>12,.2f} | ${net25_total:>12,.2f}")
    print("---------------------------------------------------")
    diff = net25_total - net24
    status = "higher" if diff > 0 else "lower"
    print(f"🔮 Forecast: 2025 will end about ${abs(diff):,.2f} {status} than 2024.")



# 9_12_25
# --- Tighten exclusions & de-dup ---

EXCLUDE_CATEGORIES = set([
    # your known non-expense buckets
    "Security",
    "CITY CC PAYMENT",
    "USAA CC PAYMENT",
    "CC PAYMENT",
    "TRANSFER",
    "COSTCO REBATE",
    "ACCOUNT INTEREST",
    "INTEREST",
    "DIVIDEND",
    "INCOME",
    "PAYROLL",
    "PAYCHECK",
])

NON_EXPENSE_KEYWORDS = [
    # anything that hints at payments/refunds/transfers
    "transfer", "xfer", "cc payment", "credit card payment", "payment received",
    "rebate", "refund", "interest", "dividend", "cashback",
]



def _pick_col(df, aliases):
    cols = {c.lower(): c for c in df.columns}
    for a in aliases:
        if a in cols:
            return cols[a]
    return None

def _ensure_series(df, target_name, source_name=None, default=""):
    """Ensure df[target_name] exists as a Series. If source_name exists, copy it, else fill with default."""
    if source_name and source_name in df.columns:
        if target_name != source_name:
            df[target_name] = df[source_name]
    elif target_name not in df.columns:
        df[target_name] = default
    return df[target_name]


#9_15_25

# =========================  OPTION 9: ONE-PASTE PATCH  =========================
# Self-contained helpers + verification for Emergency Fund estimate

import pandas as pd
from datetime import date

# -- Column alias lists (case-insensitive autodetect) --
_DATE = ["date","transaction date","post date","posted date","date posted","trans date","posting date"]
_ACCOUNT = ["account","account name","accountname","acct","source account"]
_CATEGORY = ["category","type","cat"]
_DESC = ["transact","description","memo","details","payee","name","merchant","narrative"]
_DEBIT = ["debit","charge","charges","withdrawal","withdrawals","outflow","amount debit","debits"]
_CREDIT = ["credit","payment","payments","deposit","deposits","inflow","amount credit","credits"]
_AMOUNT = ["amount","transaction amount","value","amt","net amount"]

# -- Filters to keep non-expenses out (tune as needed) --
EXCLUDE_CATEGORIES = set([
    "Security","CITY CC PAYMENT","USAA CC PAYMENT","CC PAYMENT","TRANSFER",
    "COSTCO REBATE","ACCOUNT INTEREST","INTEREST","DIVIDEND","INCOME","PAYROLL","PAYCHECK",
])
NON_EXPENSE_KEYWORDS = [
    "transfer","xfer","cc payment","credit card payment","payment received",
    "rebate","refund","interest","dividend","cashback",
]

def _pick_col(df, aliases):
    cols = {c.lower(): c for c in df.columns}
    for a in aliases:
        if a in cols:
            return cols[a]
    return None

def _dedupe_rows(df):
    # Ensure expected cols exist as Series (not scalars)
    for col in ["account","category","description"]:
        if col not in df.columns:
            df[col] = ""
    if "net" not in df.columns:
        df["net"] = 0.0
    if "date" not in df.columns:
        df["date"] = pd.NaT
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    sig = (
        df["date"].dt.strftime("%Y-%m-%d").fillna("")
        + "|" + df["account"].astype(str)
        + "|" + df["category"].astype(str)
        + "|" + df["description"].astype(str).str[:64]
        + "|" + df["net"].round(2).astype(str)
    )
    return df.loc[~sig.duplicated(keep="first")].reset_index(drop=True)


#9_15_20   

import os
import pandas as pd

def apply_categories_from_csv(df: pd.DataFrame, csv_path: str = "categories.csv") -> pd.DataFrame:
    """
    Apply simple 'keyword -> category' rules from categories.csv.
    CSV format can be with or without headers:
      keyword,category
      WF HOME MTG,Mortgage
      Fargo,Mortgage
    The keyword is matched case-insensitively against DESCRIPTION and ACCOUNT.
    """
    try:
        if not os.path.exists(csv_path):
            return df
        try:
            rules = pd.read_csv(csv_path)  # try with headers
        except Exception:
            rules = pd.read_csv(csv_path, header=None, names=["keyword", "category"])  # fallback no headers

        # Normalize columns in case CSV had different header names
        cols_lower = {c.lower(): c for c in rules.columns}
        kcol = cols_lower.get("keyword", list(rules.columns)[0])
        ccol = cols_lower.get("category", list(rules.columns)[1] if len(rules.columns) > 1 else None)
        if ccol is None:
            return df

        # Lowercase text haystacks once
        desc = df.get("description", "").astype(str).str.lower()
        acct = df.get("account", "").astype(str).str.lower()

        # Apply each rule
        for _, r in rules.iterrows():
            kw = str(r[kcol]).strip().lower()
            tgt = str(r[ccol]).strip()
            if not kw or not tgt:
                continue
            mask = desc.str.contains(kw, na=False) | acct.str.contains(kw, na=False)
            df.loc[mask, "category"] = tgt
    except Exception:
        # Fail safe: do nothing if CSV is weird
        pass
    return df

def normalize_transactions(df_in: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize transactions for expense-only summaries (Option 5):
      - date (datetime)
      - net: signed transaction amount (positive = outflow/debit, negative = inflow/credit)
      - outflow: absolute amount for rows classified as real expenses
      - is_expense: True for real expenses using the SAME rules as cash-flow (Option 8)

    This aligns Option 5 with Option 8 by reusing the single source of truth:
      is_expense = (~is_income & ~is_excluded) OR category == 'mortgage'
      where is_income uses CF_INCOME_CATS and CF_SS_REGEX,
            is_excluded uses CF_EXCLUDE_CATS.
    """
    df = df_in.copy()

    # Pick columns (case-insensitive)
    src_date = _pick_col(df, _DATE)
    src_acct = _pick_col(df, _ACCOUNT)
    src_cat  = _pick_col(df, _CATEGORY)
    src_desc = _pick_col(df, _DESC)
    src_deb  = _pick_col(df, _DEBIT)
    src_cre  = _pick_col(df, _CREDIT)
    src_amt  = _pick_col(df, _AMOUNT)

    # Canonical columns
    if src_acct: df["account"] = df[src_acct]
    if src_cat:  df["category"] = df[src_cat]
    if src_desc: df["description"] = df[src_desc]
    for col in ["account","category","description"]:
        if col not in df.columns:
            df[col] = ""

    # Fallback: if description blank but we have Transact
    if "Transact" in df.columns:
        df.loc[df["description"].isna() | (df["description"].astype(str).str.strip()==""),
               "description"] = df["Transact"].astype(str)

    # Apply categories.csv (e.g. WF HOME MTG -> Mortgage)
    df = apply_categories_from_csv(df, "categories.csv")

    # Dates
    if src_date:
        df["date"] = pd.to_datetime(df[src_date], errors="coerce")
    else:
        df["date"] = pd.NaT

    # Net signed amount
    if src_deb or src_cre:
        deb = pd.to_numeric(df[src_deb], errors="coerce").fillna(0.0) if src_deb else 0.0
        cre = pd.to_numeric(df[src_cre], errors="coerce").fillna(0.0) if src_cre else 0.0
        df["net"] = deb - cre   # debits = positive outflow, credits = negative inflow
    elif src_amt:
        df["net"] = pd.to_numeric(df[src_amt], errors="coerce").fillna(0.0)
    else:
        df["net"] = 0.0

    # Deduplicate
    df = _dedupe_rows(df)

    # Classification (reuse cash-flow rules)
    cat_raw = df["category"].astype(str)
    cat_up  = cat_raw.str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
    cat_lo  = cat_raw.str.lower().str.strip()

    text_blob = (cat_raw + " " + df["description"].astype(str) + " " + df["account"].astype(str)).str.lower()
    looks_ss = text_blob.str.contains(CF_SS_REGEX, na=False)

    is_income   = cat_up.isin(CF_INCOME_CATS) | looks_ss
    is_excluded = cat_up.isin(CF_EXCLUDE_CATS)
    is_mortgage = cat_lo.eq("mortgage")
    df["is_expense"] = (~is_income & ~is_excluded) | is_mortgage

    df["outflow"] = 0.0
    df.loc[df["is_expense"], "outflow"] = df.loc[df["is_expense"], "net"].abs()
    return df


# 9_15_25
def quick_find_mortgage_rows():
    """
    SEARCH RAW DB (no filters) for anything that looks like housing (mortgage/rent/escrow/HOA/lender names).
    This proves whether the mortgage is even present in your loaded data and under what wording.
    """
    import pandas as pd
    df = load_main_df()

    # Build a text haystack safely (always return a Series, even if column missing)
    def _col_or_blank(df, name):
        return df[name].astype(str) if name in df.columns else pd.Series([""] * len(df), index=df.index)

    hay = (
        _col_or_blank(df, "Transact") + " " +
        _col_or_blank(df, "Description") + " " +
        _col_or_blank(df, "ACCOUNT") + " " +
        _col_or_blank(df, "Category")
    ).str.lower()

    # Broad, simple lender/housing pattern
    pat = r"(mortgage|mtg|mortg|home\s*loan|escrow|hoa|wf\s*home\s*mtg|wells\s*fargo|rocket|pennymac|mr\.?\s*cooper|loancare|newrez|phh|pnc)"

    hits = df[hay.str.contains(pat, regex=True, na=False)].copy()
    if hits.empty:
        print("\n(no rows in RAW DB look like housing; wording may differ or those transactions aren’t in this DB)")
        return

    # Show last 25 matching rows
    if "Date" in hits.columns:
        hits["Date"] = pd.to_datetime(hits["Date"], errors="coerce")
        hits = hits.sort_values("Date")

    cols = [c for c in ["Date","ACCOUNT","Category","Transact","Description","Amount"] if c in hits.columns]
    print("\n--- RAW rows that look like mortgage/rent/escrow/HOA (last 25) ---")
    print(hits[cols].tail(25).to_string(index=False))

    # Monthly totals on raw Amount (as-is)
    if "Date" in hits.columns and "Amount" in hits.columns:
        hits["ym"] = hits["Date"].dt.to_period("M").astype(str)
        totals = hits.groupby("ym")["Amount"].sum().sort_index()
        print("\n--- Monthly totals for these hits (RAW Amount as-is) ---")
        for ym, val in totals.items():
            print(f"  {ym}: {val:,.2f}")



# 9_15_25 debut function. check mortgage -- seeing if included in expenses in emergency fund estimate. 
def debug_check_mortgage(df):
    """
    Shows mortgage/rent/escrow/HOA items that ARE counted as expenses,
    and those that were EXCLUDED (so you can see why).
    """
    dfn = normalize_transactions(df)

    HOUSING_PATTERN = (
        r"(?:mortgage|mtg|mortg|home\s*loan|home\s*mtg|escrow|hoa|"
        r"mr\.?\s*cooper|pennymac|loan\s*care|loancare|rocket|freedom\s*mtg|guild|caliber|"
        r"pnc\s*mtg|wells\s*fargo.*mtg|wf.*home.*mtg|bank\s*of\s*america.*mtg|bofa.*mtg|"
        r"u\.?s\.?\s*bank.*mtg|usbank.*mtg|citi.*mortg|newrez|shellpoint|carrington|ocwen|phh)"
    )

    inc = (
        dfn["category"].astype(str).str.contains(HOUSING_PATTERN, regex=True, na=False) |
        dfn["description"].astype(str).str.contains(HOUSING_PATTERN, regex=True, na=False)
    )

    # Included housing-like rows
    hits_included = dfn.loc[dfn["is_expense"] & inc, ["date","account","category","description","outflow"]].copy()
    hits_included["description"] = hits_included["description"].astype(str).str.slice(0, 60)
    hits_included = hits_included.sort_values(["date","outflow"], ascending=[True, False])

    # Excluded housing-like rows
    hits_excluded = dfn.loc[~dfn["is_expense"] & inc, ["date","account","category","description","outflow"]].copy()
    hits_excluded["description"] = hits_excluded["description"].astype(str).str.slice(0, 60)
    hits_excluded = hits_excluded.sort_values(["date","outflow"], ascending=[True, False])

    if hits_included.empty and hits_excluded.empty:
        print("\n(No mortgage/rent/escrow/HOA wording found anywhere yet.)\n")
        return

    if not hits_included.empty:
        print("\n--- Housing counted as EXPENSE (last 20) ---")
        print(hits_included.tail(20).to_string(index=False))

        dsub = hits_included.copy()
        dsub["ym"] = pd.to_datetime(dsub["date"]).dt.to_period("M").astype(str)
        totals = dsub.groupby("ym")["outflow"].sum().sort_index()
        print("\n--- Monthly housing totals (included) ---")
        for ym, val in totals.items():
            print(f"  {ym}: ${val:,.2f}")

    if not hits_excluded.empty:
        print("\n--- Housing-like but EXCLUDED (last 20) ---")
        print(hits_excluded.tail(20).to_string(index=False))
        print("\n(If a line here is a real mortgage/rent, copy its wording and we’ll whitelist it.)\n")


# ---------- Verification helpers ----------
def monthly_expense_totals_table(df_norm, year):
    months = [(year, m) for m in _completed_months_for_year(year)]
    rows = []
    for y, m in months:
        mask = (df_norm["date"].dt.year==y) & (df_norm["date"].dt.month==m) & (df_norm["is_expense"])
        total = float(df_norm.loc[mask, "outflow"].sum())
        rows.append((f"{y}-{m:02d}", total))
    return rows

def category_breakdown_for_month(df_norm, year, month, topn=12):
    mask = (df_norm["date"].dt.year==year) & (df_norm["date"].dt.month==month) & (df_norm["is_expense"])
    by_cat = (
        df_norm.loc[mask]
        .groupby(df_norm["category"].astype(str))["outflow"]
        .sum()
        .sort_values(ascending=False)
        .head(topn)
    )
    return by_cat

def _is_tax_category(cat_series: pd.Series) -> pd.Series:
    """Return True for tax-related category labels."""
    cat_up = cat_series.astype(str).str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
    return cat_up.str.contains(r"\bTAX\b", regex=True, na=False) | cat_up.str.contains("IRS", regex=False, na=False)

def _is_tax_row(df: pd.DataFrame, category_col: str = "Category", text_cols: list[str] | None = None) -> pd.Series:
    """Return True for rows that look tax-related from category and free text."""
    if text_cols is None:
        text_cols = []

    base = df[category_col].astype(str) if category_col in df.columns else pd.Series([""] * len(df), index=df.index)
    mask = _is_tax_category(base)

    blob = base.copy()
    for c in text_cols:
        if c in df.columns:
            blob = blob + " " + df[c].astype(str)
    blob = blob.str.lower()

    text_hit = blob.str.contains(r"\b(?:tax|taxes|irs)\b", regex=True, na=False)
    return mask | text_hit

def _normalize_category_label(label: str) -> str:
    return str(label).upper().strip().replace("  ", " ")

def _prompt_optional_excluded_categories() -> set[str]:
    """
    Optional exclusions for non-essentials (e.g., NANNY TAX-like custom categories).
    Enter comma-separated category names exactly as your category labels.
    """
    raw = input("Exclude non-essential categories? (comma-separated, Enter for none): ").strip()
    if not raw:
        return set()
    return {_normalize_category_label(x) for x in raw.split(",") if str(x).strip()}

def _apply_category_exclusions(df: pd.DataFrame, category_col: str, excluded_categories: set[str] | None) -> pd.DataFrame:
    if not excluded_categories:
        return df
    if category_col not in df.columns:
        return df
    cat_up = df[category_col].astype(str).str.upper().str.strip()
    return df.loc[~cat_up.isin(set(excluded_categories))].copy()

def _load_filtered_emergency_cf_for_year(year: int, excluded_categories: set[str] | None = None) -> pd.DataFrame:
    """Load one year, then apply emergency-fund filters (tax + optional category exclusions)."""
    df = load_main_df(_year_to_tag(int(year)))
    cf = compute_inflow_outflow(df)
    cf = cf.loc[~_is_tax_row(cf, category_col="Category", text_cols=["Description", "Transact", "ACCOUNT"])].copy()
    cf = _apply_category_exclusions(cf, "Category", excluded_categories)
    return cf

def _month_name_from_num(m: int) -> str:
    names = _ordered_months()
    return names[int(m)-1] if 1 <= int(m) <= 12 else str(m)

def _build_emergency_base_comparison(compare_year: int, active_year: int, excluded_categories: set[str] | None = None):
    """Core comparison dataset used by option 9.6 report + chart."""
    cf_old = _load_filtered_emergency_cf_for_year(compare_year, excluded_categories)
    cf_new = _load_filtered_emergency_cf_for_year(active_year, excluded_categories)

    common_months = sorted(set(_completed_months_for_year(compare_year)) & set(_completed_months_for_year(active_year)))
    if not common_months:
        raise ValueError("No overlapping completed months between selected years.")

    rows = []
    totals_old = []
    totals_new = []
    totals_base = []
    for m in common_months:
        mask_old = (cf_old["Date"].dt.year == int(compare_year)) & (cf_old["Date"].dt.month == int(m))
        mask_new = (cf_new["Date"].dt.year == int(active_year)) & (cf_new["Date"].dt.month == int(m))
        old_v = float(cf_old.loc[mask_old, "outflow"].sum())
        new_v = float(cf_new.loc[mask_new, "outflow"].sum())
        base_v = (old_v + new_v) / 2.0
        rows.append((_month_name_from_num(m), old_v, new_v, base_v, new_v - old_v))
        totals_old.append(old_v)
        totals_new.append(new_v)
        totals_base.append(base_v)

    month_names = [_month_name_from_num(m) for m in common_months]

    piv_old = (
        cf_old[(cf_old["Date"].dt.year == int(compare_year)) & (cf_old["outflow"] > 0)]
        .assign(MonthNum=cf_old["Date"].dt.month)
        .pivot_table(index="Category", columns="MonthNum", values="outflow", aggfunc="sum", fill_value=0.0)
    )
    piv_new = (
        cf_new[(cf_new["Date"].dt.year == int(active_year)) & (cf_new["outflow"] > 0)]
        .assign(MonthNum=cf_new["Date"].dt.month)
        .pivot_table(index="Category", columns="MonthNum", values="outflow", aggfunc="sum", fill_value=0.0)
    )
    piv_old = piv_old.reindex(columns=common_months, fill_value=0.0)
    piv_new = piv_new.reindex(columns=common_months, fill_value=0.0)
    cat_union = sorted(set(piv_old.index).union(set(piv_new.index)))
    old_tot_by_cat = piv_old.reindex(cat_union, fill_value=0.0).sum(axis=1)
    new_tot_by_cat = piv_new.reindex(cat_union, fill_value=0.0).sum(axis=1)
    delta_by_cat = new_tot_by_cat - old_tot_by_cat

    return {
        "compare_year": int(compare_year),
        "active_year": int(active_year),
        "months": common_months,
        "month_names": month_names,
        "rows": rows,
        "totals_old": totals_old,
        "totals_new": totals_new,
        "totals_base": totals_base,
        "base_monthly_avg": float(np.mean(np.array(totals_base, dtype=float))),
        "old_tot_by_cat": old_tot_by_cat,
        "new_tot_by_cat": new_tot_by_cat,
        "delta_by_cat": delta_by_cat,
        "excluded_categories": sorted(excluded_categories) if excluded_categories else [],
    }

def emergency_base_funds_comparison_report():
    """Option 9.6: compare two years by month and category to build a base-funds number."""
    active_year = get_active_year()
    raw = input(f"Compare {active_year} against which year? [default {active_year-1}]: ").strip()
    compare_year = int(raw) if raw.isdigit() else (active_year - 1)
    excluded = _prompt_optional_excluded_categories()

    try:
        data = _build_emergency_base_comparison(compare_year, active_year, excluded_categories=excluded)
    except Exception as exc:
        print(f"Could not build comparison: {exc}")
        return

    y0 = data["compare_year"]
    y1 = data["active_year"]
    print(f"\n=== BASE FUNDS COMPARISON ({y0} vs {y1}) ===")
    print("Method: monthly base = average of both years for the same month (tax excluded).")
    if data["excluded_categories"]:
        print("Additional exclusions: " + ", ".join(data["excluded_categories"]))

    print("\nMonth       | {:>12} | {:>12} | {:>12} | {:>12}".format(str(y0), str(y1), "Base Month", "Delta"))
    print("-" * 70)
    for month_name, old_v, new_v, base_v, delta_v in data["rows"]:
        print(f"{month_name:<11} | ${old_v:>11,.2f} | ${new_v:>11,.2f} | ${base_v:>11,.2f} | ${delta_v:>11,.2f}")

    base_mo = float(data["base_monthly_avg"])
    print("-" * 70)
    print(f"Suggested base monthly spend for estimator: ${base_mo:,.2f}")
    print(f"6-month fund:  ${base_mo*6:,.2f}")
    print(f"9-month fund:  ${base_mo*9:,.2f}")
    print(f"12-month fund: ${base_mo*12:,.2f}")

    cat_delta = data["delta_by_cat"]
    old_cat = data["old_tot_by_cat"]
    new_cat = data["new_tot_by_cat"]
    top = cat_delta.reindex(cat_delta.abs().sort_values(ascending=False).index).head(15)
    print("\nTop category deltas across compared months:")
    print(f"{'Category':<24} | {y0:>12} | {y1:>12} | {'Delta':>12}")
    print("-" * 70)
    for cat, d in top.items():
        label = "(Uncategorized)" if (pd.isna(cat) or str(cat).strip() == "") else str(cat)
        print(f"{label[:24]:<24} | ${float(old_cat.get(cat,0.0)):>11,.2f} | ${float(new_cat.get(cat,0.0)):>11,.2f} | ${float(d):>11,.2f}")

def emergency_base_funds_comparison_chart_html():
    """Option 9.6ch: HTML chart of monthly spending comparison + suggested base line."""
    active_year = get_active_year()
    raw = input(f"Compare {active_year} against which year? [default {active_year-1}]: ").strip()
    compare_year = int(raw) if raw.isdigit() else (active_year - 1)
    excluded = _prompt_optional_excluded_categories()

    try:
        data = _build_emergency_base_comparison(compare_year, active_year, excluded_categories=excluded)
    except Exception as exc:
        print(f"Could not build chart: {exc}")
        return

    labels = [m[:3] for m in data["month_names"]]
    s_old = [float(v) for v in data["totals_old"]]
    s_new = [float(v) for v in data["totals_new"]]
    s_base = [float(v) for v in data["totals_base"]]

    max_val = max([*s_old, *s_new, *s_base, 1.0])
    width, height = 1100, 420
    left, right, top, bottom = 60, 20, 30, 60
    chart_w = width - left - right
    chart_h = height - top - bottom
    step_x = chart_w / max(1, len(labels)-1)

    def _y(v: float) -> float:
        return top + chart_h - (v / max_val) * chart_h

    def _line_points(vals):
        pts = []
        for i, v in enumerate(vals):
            x = left + step_x * i
            pts.append((x, _y(float(v))))
        return pts

    p_old = _line_points(s_old)
    p_new = _line_points(s_new)
    p_base = _line_points(s_base)

    parts = [_svg_header(width, height)]
    parts.append(f"<line x1='{left}' y1='{top+chart_h}' x2='{left+chart_w}' y2='{top+chart_h}' stroke='#333' stroke-width='1' />")
    parts.append(f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top+chart_h}' stroke='#333' stroke-width='1' />")

    for i, lab in enumerate(labels):
        x = left + step_x * i
        parts.append(f"<text x='{x:.1f}' y='{top+chart_h+16}' text-anchor='middle' font-size='10'>{lab}</text>")

    def _poly(pts, color):
        poly = " ".join([f"{x:.1f},{y:.1f}" for x, y in pts])
        return f"<polyline fill='none' stroke='{color}' stroke-width='2' points='{poly}' />"

    parts.append(_poly(p_old, "#6d4c41"))
    parts.append(_poly(p_new, "#1565c0"))
    parts.append(_poly(p_base, "#2e7d32"))

    for pts, color in ((p_old, "#6d4c41"), (p_new, "#1565c0"), (p_base, "#2e7d32")):
        for x, y in pts:
            parts.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='2.5' fill='{color}' />")

    y0 = data["compare_year"]
    y1 = data["active_year"]
    lx, ly = left + 10, top + 10
    parts.append(f"<line x1='{lx}' y1='{ly+5}' x2='{lx+15}' y2='{ly+5}' stroke='#6d4c41' stroke-width='2' /><text x='{lx+20}' y='{ly+10}' font-size='11'>{y0}</text>")
    parts.append(f"<line x1='{lx+90}' y1='{ly+5}' x2='{lx+105}' y2='{ly+5}' stroke='#1565c0' stroke-width='2' /><text x='{lx+110}' y='{ly+10}' font-size='11'>{y1}</text>")
    parts.append(f"<line x1='{lx+180}' y1='{ly+5}' x2='{lx+195}' y2='{ly+5}' stroke='#2e7d32' stroke-width='2' /><text x='{lx+200}' y='{ly+10}' font-size='11'>Base</text>")
    parts.append("</svg>")

    base_mo = float(data["base_monthly_avg"])
    body = (
        f"<p>Suggested base monthly spend: <b>${base_mo:,.2f}</b></p>"
        + "".join(parts)
    )
    title = f"Emergency Base Funds Comparison ({y0} vs {y1})"
    html = _html_wrap(title, body)

    out_dir = os.path.join("exports", EXPORTS_SUBDIR) if (EXPORTS_SUBDIR and str(EXPORTS_SUBDIR).strip()) else "exports"
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = os.path.join(out_dir, f"Emergency_Base_Comparison_{y0}_vs_{y1}_{ts}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved: {path}")

def audit_exclusions_for_month(df_norm, year, month, min_amount=200):
    # Mirror filters
    exclude_words = NON_EXPENSE_KEYWORDS
    exclude_cats = EXCLUDE_CATEGORIES

    m = (df_norm["date"].dt.year==year) & (df_norm["date"].dt.month==month)
    hay = (df_norm["category"].astype(str)+" "+df_norm["description"].astype(str)+" "+df_norm["account"].astype(str)).str.lower()
    kw_excl  = hay.str.contains("|".join(exclude_words), regex=True, na=False)
    cat_excl = df_norm["category"].astype(str).isin(exclude_cats)

    dropped = df_norm[m & (~df_norm["is_expense"]) & (df_norm["outflow"] >= min_amount)].copy()
    dropped["reason"] = ""
    dropped.loc[dropped.index.intersection(df_norm[kw_excl].index), "reason"] += "|keyword"
    dropped.loc[dropped.index.intersection(df_norm[cat_excl].index), "reason"] += "|category"

    cols = ["date","account","category","description","outflow","reason"]
    return dropped.sort_values("outflow", ascending=False)[cols].head(20)

# ---------- Option 9: verbose + verified ----------
def show_emergency_fund_estimate(df, exclude_categories: set[str] | None = None):
    df_norm = normalize_transactions(df)
    df_norm = df_norm.loc[~_is_tax_row(df_norm, category_col="category", text_cols=["description", "account"])].copy()
    df_norm = _apply_category_exclusions(df_norm, "category", exclude_categories)

    # Guard: usable dates?
    if "date" not in df_norm.columns or df_norm["date"].isna().all():
        print("\n=== EMERGENCY FUND ESTIMATE ===")
        print("No usable dates found. Map your date column and retry.")
        return

    active_year = get_active_year()
    completed = [(active_year, m) for m in _completed_months_for_year(active_year)]
    if not completed:
        print("\n=== EMERGENCY FUND ESTIMATE ===")
        print("No completed months this year yet.")
        return

    rows = monthly_expense_totals_table(df_norm, active_year)
    vals = [v for _, v in rows]
    if not vals:
        print("\n=== EMERGENCY FUND ESTIMATE ===")
        print("No expenses found in completed months.")
        return

    baseline = sum(vals) / len(vals)

    print("\n=== EMERGENCY FUND ESTIMATE ===")
    print("Note: Tax categories are excluded from this estimate.")
    print("Months used:")
    print("  " + ", ".join(m for m, _ in rows))

    print("\nPer-month totals (expenses only):")
    for m, v in rows:
        print(f"  {m}: ${v:,.2f}")

    print(f"\nAverage monthly expenses: ${baseline:,.2f}\n")
    for months in [6, 9, 12]:
        print(f"{months}-month fund: ${baseline * months:,.2f}")

    # Category breakdown for last completed month
    last_y, last_m = completed[-1]
    print(f"\nTop categories in {last_y}-{last_m:02d}:")
    cats = category_breakdown_for_month(df_norm, last_y, last_m, topn=12)
    if cats.empty:
        print("  (No categories)")
    else:
        for cat, amt in cats.items():
            print(f"  - {cat or '(Uncategorized)'}: ${amt:,.2f}")

    # Exclusion audit (largest dropped outflows)
    print(f"\nExcluded (largest outflows) in {last_y}-{last_m:02d}:")
    audit = audit_exclusions_for_month(df_norm, last_y, last_m, min_amount=200)
    if audit.empty:
        print("  (No large exclusions)")
    else:
        tmp = audit.copy()
        tmp["description"] = tmp["description"].astype(str).str.slice(0, 60)
        print(tmp.to_string(index=False))
    print("")
# =======================  END OPTION 9: ONE-PASTE PATCH  =======================

# 9_15_25 debug emergency fund estimate !!

def debug_verify_emergency_fund(df):
    """
    Prints:
      - Per-month expense totals actually used for the baseline
      - Top categories for the last completed month
      - Largest EXCLUDED outflows (so you can spot CC payments/transfers/dupes)
    """
    import pandas as pd
    from datetime import date

    dfn = normalize_transactions(df)

    # Choose completed months this year
    active_year = get_active_year()
    months = [(active_year, m) for m in _completed_months_for_year(active_year)]
    if not months:
        print("No completed months this year.")
        return

    # 1) Per-month totals
    print("\n--- Per-month totals (expenses only) ---")
    per_month = []
    for y, m in months:
        mask = (dfn["date"].dt.year==y) & (dfn["date"].dt.month==m) & (dfn["is_expense"])
        total = float(dfn.loc[mask, "outflow"].sum())
        per_month.append(total)
        print(f"  {y}-{m:02d}: ${total:,.2f}")

    if per_month:
        avg = sum(per_month)/len(per_month)
        print(f"\nComputed average from these months: ${avg:,.2f}")

    # 2) Top categories for last completed month
    y, m = months[-1]
    print(f"\n--- Top categories in {y}-{m:02d} ---")
    mask = (dfn["date"].dt.year==y) & (dfn["date"].dt.month==m) & (dfn["is_expense"])
    cats = (
        dfn.loc[mask]
        .groupby(dfn["category"].astype(str))["outflow"]
        .sum()
        .sort_values(ascending=False)
        .head(12)
    )
    if cats.empty:
        print("  (No categories)")
    else:
        for cat, amt in cats.items():
            print(f"  - {cat or '(Uncategorized)'}: ${amt:,.2f}")

    # 3) Exclusion audit: biggest outflows we DROPPED
    # Use your global filters if present; else fall back to defaults
    exclude_words = NON_EXPENSE_KEYWORDS if 'NON_EXPENSE_KEYWORDS' in globals() else [
        "transfer","xfer","cc payment","credit card payment","payment received",
        "rebate","refund","interest","dividend","cashback",
    ]
    exclude_cats = EXCLUDE_CATEGORIES if 'EXCLUDE_CATEGORIES' in globals() else set([
        "Security","CITY CC PAYMENT","USAA CC PAYMENT","CC PAYMENT","TRANSFER",
        "COSTCO REBATE","ACCOUNT INTEREST","INTEREST","DIVIDEND","INCOME","PAYROLL","PAYCHECK",
    ])

    print(f"\n--- Excluded (largest outflows) in {y}-{m:02d} ---")
    m_mask = (dfn["date"].dt.year==y) & (dfn["date"].dt.month==m)
    hay = (dfn["category"].astype(str)+" "+dfn["description"].astype(str)+" "+dfn["account"].astype(str)).str.lower()
    kw_excl  = hay.str.contains("|".join(exclude_words), regex=True, na=False)
    cat_excl = dfn["category"].astype(str).isin(exclude_cats)

    dropped = dfn[m_mask & (~dfn["is_expense"]) & (dfn["outflow"] >= 200)].copy()
    if dropped.empty:
        print("  (No large exclusions)")
        return

    dropped["reason"] = ""
    dropped.loc[dropped.index.intersection(dfn[kw_excl].index), "reason"] += "|keyword"
    dropped.loc[dropped.index.intersection(dfn[cat_excl].index), "reason"] += "|category"

    # trim long desc for readability
    tmp = dropped.sort_values("outflow", ascending=False)[["date","account","category","description","outflow","reason"]].head(20).copy()
    tmp["description"] = tmp["description"].astype(str).str.slice(0, 60)
    print(tmp.to_string(index=False))
    print("")






# 9_12_25
def show_emergency_fund_estimate(df, exclude_categories: set[str] | None = None):
    """
    Calculate a cost-of-living baseline from completed months this year
    and print 6-, 9-, and 12-month emergency fund estimates.
    """
    df_norm = normalize_transactions(df)
    df_norm = df_norm.loc[~_is_tax_row(df_norm, category_col="category", text_cols=["description", "account"])].copy()
    df_norm = _apply_category_exclusions(df_norm, "category", exclude_categories)

    # Ensure we have a date column
    if "date" not in df_norm.columns:
        print("No date column found in DataFrame.")
        return

    # Only use completed months of the current year
    active_year = get_active_year()
    completed = [(active_year, m) for m in _completed_months_for_year(active_year)]
    if not completed:
        print("No completed months this year yet.")
        return

    # Optionally use only the most recent N completed months
    raw_n = input("Use how many recent months for average? (Enter for all): ").strip()
    if raw_n:
        try:
            n = int(raw_n)
            if n > 0:
                completed = completed[-n:]
        except Exception:
            print("Invalid input; using all completed months.")

    # Compute monthly totals
    monthly_totals = []
    for (y, m) in completed:
        mask = (df_norm["date"].dt.year == y) & (df_norm["date"].dt.month == m) & (df_norm["is_expense"])
        total = df_norm.loc[mask, "outflow"].sum()
        monthly_totals.append(total)

    if not monthly_totals:
        print("No expenses found in completed months.")
        return

    baseline = sum(monthly_totals) / len(monthly_totals)

    print("\n=== EMERGENCY FUND ESTIMATE ===")
    print("Note: Tax categories are excluded from this estimate.")
    print(f"Months used: {', '.join(f'{y}-{m:02d}' for (y,m) in completed)}")
    print("Per-month totals:")
    for (y, m), total in zip(completed, monthly_totals):
        print(f"  {y}-{m:02d}: ${float(total):,.2f}")
    print(f"\nAverage monthly expenses: ${baseline:,.2f}\n")
    for months in [6, 9, 12]:
        print(f"{months}-month fund: ${baseline * months:,.2f}")
    print("")

    # Optional: show top excluded rows (transfers/CC payments/etc.) for audit
    show_excl = input("Show top excluded rows per month? (y/N): ").strip().lower()
    if show_excl in {"y", "yes"}:
        for (y, m) in completed:
            m_mask = (df_norm["date"].dt.year == y) & (df_norm["date"].dt.month == m)
            excl = df_norm[m_mask & (~df_norm["is_expense"])].copy()
            if excl.empty:
                continue
            # Excluded rows have outflow=0 by definition; show magnitude via net instead.
            if "net" in excl.columns:
                excl["AmountAbs"] = excl["net"].abs()
            elif "Amount" in excl.columns:
                excl["AmountAbs"] = excl["Amount"].abs()
            else:
                excl["AmountAbs"] = 0.0
            excl = excl.sort_values("AmountAbs", ascending=False)
            cols = [c for c in ["date", "account", "category", "description", "AmountAbs"] if c in excl.columns]
            print(f"\n--- Excluded rows for {y}-{m:02d} (top 5) ---")
            tmp = excl[cols].head(5).copy()
            if "description" in tmp.columns:
                tmp["description"] = tmp["description"].astype(str).str.slice(0, 60)
            print(tmp.to_string(index=False))

#9_16_25
from datetime import date

# ---------- helpers for the merged emergency-fund view ----------

def _month_label(y, m):
    return f"{y}-{m:02d}"

def _top_categories_for_month(cf, year, month, topn=12):
    """
    Return list of (category, amount) for a month using SGOT (outflow only).
    """
    mask = (
        (cf["Date"].dt.year == year) &
        (cf["Date"].dt.month == month) &
        (cf["outflow"] > 0)
    )
    if not mask.any():
        return []
    by_cat = (
        cf.loc[mask]
          .groupby(cf.loc[mask, "Category"].astype(str))["outflow"]
          .sum()
          .sort_values(ascending=False)
          .head(topn)
    )
    return list(by_cat.items())

def _format_block_for_month(y, m, pairs):
    """
    Build the exact text block you like for one month.
    """
    header = f"--- Top categories in {_month_label(y, m)} ---"
    if not pairs:
        lines = ["  (none)"]
    else:
        lines = [f"  - {cat}: ${amt:,.2f}" for cat, amt in pairs]
    return [header] + lines

def _print_blocks_side_by_side(blocks, columns=2, col_width=46):
    """
    Print blocks in side-by-side columns for a big-picture audit.
    """
    if columns <= 1:
        for b in blocks:
            print()
            for line in b:
                print(line)
        print()
        return

    # group blocks into rows of N columns
    for i in range(0, len(blocks), columns):
        row = blocks[i:i+columns]
        max_h = max(len(b) for b in row)
        padded = [b + [""]*(max_h - len(b)) for b in row]
        for r in zip(*padded):
            print("   ".join(s.ljust(col_width) for s in r))
        print()  # spacer between row groups

# ---------- MERGED: Emergency Fund + Month-by-Month Category Audit ----------

def show_emergency_fund_estimate_drilled_down(topn=12, columns=2, exclude_categories: set[str] | None = None):
    """
    Emergency Fund (merged view)
    - Baseline = AVERAGE monthly expenses across all *completed* months this year (SGOT outflows only)
    - Prints 6/9/12-month targets
    - Then prints the same 'Top categories in YYYY-MM' block for EVERY completed month,
      side-by-side (columns=2 by default) for a big-picture audit.

    Args:
        topn (int): how many top categories per month to show
        columns (int): 1 = sequential, 2 = side-by-side view
    """
    df = load_main_df()
    cf = compute_inflow_outflow(df)
    cf = cf.loc[~_is_tax_row(cf, category_col="Category", text_cols=["Description", "Transact", "ACCOUNT"])].copy()
    cf = _apply_category_exclusions(cf, "Category", exclude_categories)

    year = get_active_year()
    completed_months = _completed_months_for_year(year)

    if not completed_months:
        print("\n=== EMERGENCY FUND ESTIMATE ===")
        print("No completed months this year yet.\n")
        return

    # Per-month totals (expenses only, SGOT outflows)
    monthly_totals = []
    for m in completed_months:
        mask = (cf["Date"].dt.year == year) & (cf["Date"].dt.month == m)
        total = float(cf.loc[mask, "outflow"].sum())
        monthly_totals.append(total)

    if not monthly_totals:
        print("\n=== EMERGENCY FUND ESTIMATE ===")
        print("No expenses found in completed months.\n")
        return

    baseline = sum(monthly_totals) / len(monthly_totals)

    # ---------- Header + targets ----------
    print("\n=== EMERGENCY FUND ESTIMATE (Merged) ===")
    print("Note: Tax categories are excluded from this estimate.")
    print("Baseline uses the AVERAGE monthly expenses across all COMPLETED months this year.")
    print("The month-by-month category blocks below are for audit/trust only;")
    print("they do not change the baseline.\n")

    # months used + per-month totals
    print("Months used (completed):")
    print("  " + ", ".join(_month_label(year, m) for m in completed_months))

    print("\nPer-month totals (expenses only):")
    for m, v in zip(completed_months, monthly_totals):
        print(f"  {_month_label(year, m)}: ${v:,.2f}")

    print(f"\nAverage monthly expenses: ${baseline:,.2f}\n")
    for n in (6, 9, 12):
        print(f"{n}-month fund: ${baseline * n:,.2f}")

    # ---------- Big-picture audit: every month’s top categories ----------
    print("\n\n=== Month-by-Month Category Audit (Top {topn}) ===".replace("{topn}", str(topn)))
    blocks = []
    for m in completed_months:
        pairs = _top_categories_for_month(cf, year, m, topn=topn)
        blocks.append(_format_block_for_month(year, m, pairs))

    _print_blocks_side_by_side(blocks, columns=columns, col_width=46)

# 9_16_25 better !!!!!!!!!!!!!! gives mean/median/and gets rid out outlyers

from datetime import date
import numpy as np

# ===== helpers reused for the big-picture category audit =====

def _month_label(y, m):
    return f"{y}-{m:02d}"

def _top_categories_for_month(cf, year, month, topn=12):
    mask = (
        (cf["Date"].dt.year == year) &
        (cf["Date"].dt.month == month) &
        (cf["outflow"] > 0)
    )
    if not mask.any():
        return []
    by_cat = (
        cf.loc[mask]
          .groupby(cf.loc[mask, "Category"].astype(str))["outflow"]
          .sum()
          .sort_values(ascending=False)
          .head(topn)
    )
    return list(by_cat.items())

def _format_block_for_month(y, m, pairs):
    header = f"--- Top categories in {_month_label(y, m)} ---"
    if not pairs:
        lines = ["  (none)"]
    else:
        lines = [f"  - {cat}: ${amt:,.2f}" for cat, amt in pairs]
    return [header] + lines

def _print_blocks_side_by_side(blocks, columns=2, col_width=46):
    if columns <= 1:
        for b in blocks:
            print()
            for line in b:
                print(line)
        print()
        return
    for i in range(0, len(blocks), columns):
        row = blocks[i:i+columns]
        max_h = max(len(b) for b in row)
        padded = [b + [""]*(max_h - len(b)) for b in row]
        for r in zip(*padded):
            print("   ".join(s.ljust(col_width) for s in r))
        print()

# ===== baseline + forecast helpers =====

def _completed_months_this_year():
    year = get_active_year()
    return year, _completed_months_for_year(year)

DEFAULT_FLEX_SPEND_CATEGORIES = {
    "AMAZON", "RESTAURANT", "VACATION", "MOVIES", "RECREATION",
    "SUBSCRIPTION", "SPORTS", "SPORTING GOODS", "HOBBIES",
    "CLOTHING", "CHRISTMASS2024", "LOOK INTO",
}
DEFAULT_IRREGULAR_ESSENTIAL_CATEGORIES = {
    "AUTO", "REGISTRATOIN ?", "TAXES", "NANNY TAX",
}
DEFAULT_STANDARD_INCOME_CATEGORIES = {
    "PAYCHECK", "S_S", "S S", "SS", "SOCIAL SECURITY", "SSA", "SSA INCOME",
    "WORK", "SECURITY", "INCOME ? KP",
}

def _normalize_category_series(cat_series: pd.Series) -> pd.Series:
    return cat_series.astype(str).str.upper().str.replace(r"\s+", " ", regex=True).str.strip()

def _monthly_expense_totals(cf, year, months):
    totals = []
    for m in months:
        mask = (cf["Date"].dt.year == year) & (cf["Date"].dt.month == m)
        totals.append(float(cf.loc[mask, "outflow"].sum()))
    return np.array(totals, dtype=float)

def _compute_baselines(values: np.ndarray):
    vals = values[np.isfinite(values)]
    if len(vals) == 0:
        return None

    mean = float(np.mean(vals))
    median = float(np.median(vals))

    # trimmed mean (drop min and max if possible)
    if len(vals) >= 3:
        trimmed_vals = np.sort(vals)[1:-1]
        trimmed = float(np.mean(trimmed_vals)) if len(trimmed_vals) else mean
    else:
        trimmed = mean

    # outlier-adjusted via IQR rule
    if len(vals) >= 4:
        q1, q3 = np.percentile(vals, [25, 75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        filtered = vals[(vals >= lower) & (vals <= upper)]
        if len(filtered) >= 2:
            outlier_adj = float(np.mean(filtered))
        else:
            # fallback to trimmed if IQR filter is too aggressive
            outlier_adj = trimmed
    else:
        outlier_adj = trimmed

    return {
        "Mean": mean,
        "Median": median,
        "Trimmed": trimmed,
        "Outlier-Adjusted": outlier_adj,
    }

def _monthly_flow_totals(cf, year: int, months: list[int], *, mode: str = "expense", mask: pd.Series | None = None) -> np.ndarray:
    vals = []
    base_mask = mask if mask is not None else pd.Series([True] * len(cf), index=cf.index)
    for m in months:
        ym = (cf["Date"].dt.year == int(year)) & (cf["Date"].dt.month == int(m)) & base_mask
        if mode == "income":
            vals.append(float(cf.loc[ym, "inflow"].sum()))
        else:
            vals.append(float(cf.loc[ym, "outflow"].sum()))
    return np.array(vals, dtype=float)

def show_big_picture_savings_summary():
    """
    Big-picture terminal summary for working-years cash flow and safe transfer sizing.

    Prints:
      - monthly standard income / all income / all spending / base recurring / irregular / flexible
      - baseline choices for standard income and spending
      - conservative / working / stretch transfer targets
      - included categories by bucket so the model is auditable
    """
    active_year = get_active_year()
    df = load_main_df(_year_to_tag(active_year))
    cf = compute_inflow_outflow(df)
    cf = cf[(cf["Date"].dt.year == int(active_year))].copy()

    months = _completed_months_for_year(active_year)
    if not months:
        print("\n=== BIG PICTURE SAVINGS VIEW ===")
        print("No completed months available for this year yet.")
        return

    cf = cf[cf["Date"].dt.month.isin(months)].copy()
    if cf.empty:
        print("\n=== BIG PICTURE SAVINGS VIEW ===")
        print(f"No rows found for completed months in {active_year}.")
        return

    cat_up = _normalize_category_series(cf["Category"])
    flex_mask = cat_up.isin(DEFAULT_FLEX_SPEND_CATEGORIES)
    irregular_mask = cat_up.isin(DEFAULT_IRREGULAR_ESSENTIAL_CATEGORIES) & cf["is_expense"]
    base_mask = (~flex_mask) & (~irregular_mask) & cf["is_expense"]
    income_mask = cf["is_income"]
    standard_income_mask = income_mask & cat_up.isin(DEFAULT_STANDARD_INCOME_CATEGORIES)

    month_names = _ordered_months()
    month_labels = [month_names[m - 1] for m in months]

    income_monthly = _monthly_flow_totals(cf, active_year, months, mode="income", mask=income_mask)
    income_standard_monthly = _monthly_flow_totals(cf, active_year, months, mode="income", mask=standard_income_mask)
    spend_all_monthly = _monthly_flow_totals(cf, active_year, months, mode="expense")
    spend_base_monthly = _monthly_flow_totals(cf, active_year, months, mode="expense", mask=base_mask)
    spend_irregular_monthly = _monthly_flow_totals(cf, active_year, months, mode="expense", mask=irregular_mask)
    spend_flex_monthly = _monthly_flow_totals(cf, active_year, months, mode="expense", mask=flex_mask & cf["is_expense"])
    net_monthly = income_monthly - spend_all_monthly

    income_base = _compute_baselines(income_monthly)
    income_standard_base = _compute_baselines(income_standard_monthly)
    spend_all_base = _compute_baselines(spend_all_monthly)
    spend_base_base = _compute_baselines(spend_base_monthly)
    spend_irregular_base = _compute_baselines(spend_irregular_monthly)
    spend_flex_base = _compute_baselines(spend_flex_monthly)
    net_base = _compute_baselines(net_monthly)

    if any(x is None for x in [income_base, spend_all_base, spend_base_base, spend_irregular_base, spend_flex_base, net_base]):
        print("\n=== BIG PICTURE SAVINGS VIEW ===")
        print("Not enough completed-month data to build baselines.")
        return

    use_standard_income = bool(income_standard_base is not None and np.any(income_standard_monthly > 0))
    income_reliable = float((income_standard_base if use_standard_income else income_base)["Median"])
    all_conservative = float(spend_all_base["Mean"])
    all_working = float(spend_all_base["Outlier-Adjusted"])
    base_working = float(spend_base_base["Outlier-Adjusted"])
    irregular_working = float(spend_irregular_base["Outlier-Adjusted"])
    flex_working = float(spend_flex_base["Outlier-Adjusted"])
    buffer = max(250.0, income_reliable * 0.05)

    transfer_conservative = max(0.0, income_reliable - all_conservative - buffer)
    transfer_working = max(0.0, income_reliable - all_working - buffer)
    transfer_stretch = max(0.0, income_reliable - (base_working + irregular_working) - buffer)

    base_cat_monthly = (
        cf.loc[base_mask].groupby("Category", observed=False)["outflow"].sum().sort_values(ascending=False) / max(len(months), 1)
    )
    irregular_cat_monthly = (
        cf.loc[irregular_mask].groupby("Category", observed=False)["outflow"].sum().sort_values(ascending=False) / max(len(months), 1)
    )
    flex_cat_monthly = (
        cf.loc[flex_mask & cf["is_expense"]].groupby("Category", observed=False)["outflow"].sum().sort_values(ascending=False) / max(len(months), 1)
    )
    income_cat_monthly = (
        cf.loc[income_mask].groupby("Category", observed=False)["inflow"].sum().sort_values(ascending=False) / max(len(months), 1)
    )
    standard_income_cat_monthly = (
        cf.loc[standard_income_mask].groupby("Category", observed=False)["inflow"].sum().sort_values(ascending=False) / max(len(months), 1)
    )
    base_categories = sorted([str(x) for x in base_cat_monthly.index.tolist()])
    irregular_categories = sorted([str(x) for x in irregular_cat_monthly.index.tolist()])
    flex_categories = sorted([str(x) for x in flex_cat_monthly.index.tolist()])
    standard_income_categories = sorted([str(x) for x in standard_income_cat_monthly.index.tolist()])

    print(f"\n=== BIG PICTURE SAVINGS VIEW ({active_year}) ===")
    print("Goal: show real spending, core/base spending, and a savings-transfer range for high-yield cash.")
    print("Savings estimate uses standard recurring income first when available.")
    print("Flexible spending bucket categories:")
    print("  " + ", ".join(sorted(DEFAULT_FLEX_SPEND_CATEGORIES)))
    print("Irregular / sinking-fund bucket categories:")
    print("  " + ", ".join(sorted(DEFAULT_IRREGULAR_ESSENTIAL_CATEGORIES)))

    print("\nMonths used:")
    print("  " + ", ".join([f"{active_year}-{m:02d}" for m in months]))

    print("\nMonth       | Std Income | All Income |  All Spend | Base Core | Irregular | Flex Spend |        Net")
    print("------------------------------------------------------------------------------------------------------")
    for label, inc_std, inc_all, all_sp, base_sp, irr_sp, flex_sp, net in zip(
        month_labels, income_standard_monthly, income_monthly, spend_all_monthly, spend_base_monthly, spend_irregular_monthly, spend_flex_monthly, net_monthly
    ):
        print(
            f"{label:<11} | ${inc_std:>9,.2f} | ${inc_all:>9,.2f} | ${all_sp:>9,.2f} | "
            f"${base_sp:>8,.2f} | ${irr_sp:>8,.2f} | ${flex_sp:>9,.2f} | ${net:>10,.2f}"
        )

    print("\n--- Baseline Summary (monthly) ---")
    print(f"{'Metric':<34} | {'Amount':>12}")
    print("-" * 51)
    if use_standard_income:
        print(f"{'Reliable standard income (Median)':<34} | ${income_reliable:>11,.2f}")
        print(f"{'All income (Median)':<34} | ${float(income_base['Median']):>11,.2f}")
    else:
        print(f"{'Reliable income (Median)':<34} | ${income_reliable:>11,.2f}")
    print(f"{'All spending (Mean)':<34} | ${all_conservative:>11,.2f}")
    print(f"{'All spending (Outlier-Adjusted)':<34} | ${all_working:>11,.2f}")
    print(f"{'Base recurring spend (Outlier-Adjusted)':<34} | ${base_working:>11,.2f}")
    print(f"{'Irregular reserve (Outlier-Adjusted)':<34} | ${irregular_working:>11,.2f}")
    print(f"{'Flexible spending (Outlier-Adjusted)':<34} | ${flex_working:>11,.2f}")
    print(f"{'Net cash flow (Median)':<34} | ${float(net_base['Median']):>11,.2f}")
    print(f"{'Safety buffer (5% / $250 min)':<34} | ${buffer:>11,.2f}")

    print("\n--- Savings Transfer Guide ---")
    print(f"{'Conservative: keep current lifestyle':<42} ${transfer_conservative:,.2f}")
    print(f"{'Working target: smooth spike months':<42} ${transfer_working:,.2f}")
    print(f"{'Stretch: fund base + irregular only':<42} ${transfer_stretch:,.2f}")
    print(f"{'Potential upside from flexible spend':<42} ${max(0.0, transfer_stretch - transfer_working):,.2f}")

    print("\n--- Income Categories Used ---")
    if standard_income_categories:
        print("Standard recurring income categories:")
        print("  " + ", ".join(standard_income_categories))
    else:
        print("Standard recurring income categories: (none matched, using all income rows instead)")
    if income_cat_monthly.empty:
        print("  (no income rows)")
    else:
        for cat, amt in income_cat_monthly.items():
            print(f"  - {cat}: ${float(amt):,.2f}/mo")

    print("\n--- Spending Buckets ---")
    print("Base recurring categories included:")
    print("  " + (", ".join(base_categories) if base_categories else "(none)"))
    print("Irregular / sinking-fund categories included:")
    print("  " + (", ".join(irregular_categories) if irregular_categories else "(none)"))
    print("Flexible spending categories included:")
    print("  " + (", ".join(flex_categories) if flex_categories else "(none)"))

    print("\n--- Top Base Recurring Categories (avg/mo across months used) ---")
    if base_cat_monthly.empty:
        print("  (none)")
    else:
        for cat, amt in base_cat_monthly.head(10).items():
            print(f"  - {cat}: ${float(amt):,.2f}")

    print("\n--- Irregular / Sinking-Fund Categories (avg/mo across months used) ---")
    if irregular_cat_monthly.empty:
        print("  (none)")
    else:
        for cat, amt in irregular_cat_monthly.head(10).items():
            print(f"  - {cat}: ${float(amt):,.2f}")

    print("\n--- Top Flexible Categories (avg/mo across months used) ---")
    if flex_cat_monthly.empty:
        print("  (none)")
    else:
        for cat, amt in flex_cat_monthly.head(10).items():
            print(f"  - {cat}: ${float(amt):,.2f}")

    print("\nRead this as:")
    print("  Conservative = what you can move if you keep spending as-is.")
    print("  Working target = same lifestyle, but smooth out unusual months.")
    print("  Stretch = what you could move if flexible spending is trimmed and irregulars are handled as reserves.")

def _q4_income_baseline_from_previous_year(active_year: int):
    """Use previous year's Oct-Dec inflow average as the income model."""
    source_year = int(active_year) - 1
    df_prev = load_main_df(_year_to_tag(source_year))
    cf_prev = compute_inflow_outflow(df_prev)
    q4mask = (cf_prev["Date"].dt.year == source_year) & (cf_prev["Date"].dt.month.isin([10, 11, 12]))
    inc_q4_total = float(cf_prev.loc[q4mask, "inflow"].sum())
    return (inc_q4_total / 3.0), source_year, inc_q4_total

def _ytd_totals_for_year(cf, year: int):
    """YTD totals for current year; full year totals for past years."""
    y = int(year)
    today = date.today()
    if y == today.year:
        months = list(range(1, today.month))
    else:
        months = list(range(1, 13))

    if not months:
        return 0.0, 0.0, 0.0, 0

    mask = (cf["Date"].dt.year == y) & (cf["Date"].dt.month.isin(months))
    inc = float(cf.loc[mask, "inflow"].sum())
    exp = float(cf.loc[mask, "outflow"].sum())
    return inc, exp, inc - exp, len(months)

def _forecast_full_year(cf, year: int, baseline_expense: float, months_left: int):
    """
    Forecast remaining months for selected year:
    - expenses from selected baseline
    - income from previous-year Q4 average (fallback to selected-year YTD avg)
    """
    inc_ytd, exp_ytd, net_ytd, used_months = _ytd_totals_for_year(cf, year)

    try:
        income_mo, source_year, source_q4_total = _q4_income_baseline_from_previous_year(year)
        model_note = f"from {source_year} Q4 average (Q4 total ${source_q4_total:,.2f} / 3)"
    except Exception:
        income_mo = (inc_ytd / used_months) if used_months > 0 else 0.0
        source_year = int(year)
        source_q4_total = 0.0
        model_note = f"fallback: {year} YTD average (${inc_ytd:,.2f} / {max(used_months,1)} months)"

    inc_future = float(income_mo) * int(months_left)
    exp_future = float(baseline_expense) * int(months_left)
    return {
        "inc_total": inc_ytd + inc_future,
        "exp_total": exp_ytd + exp_future,
        "net_total": net_ytd + (inc_future - exp_future),
        "income_mo_model": float(income_mo),
        "income_model_year": int(source_year),
        "income_model_q4_total": float(source_q4_total),
        "income_model_note": model_note,
    }

# ===== MERGED Emergency Fund + Baselines + Forecast + Audit =====

def show_emergency_fund_estimate_drilled_down_better(topn=12, columns=2, default_baseline="Outlier-Adjusted", exclude_categories: set[str] | None = None):
    """
    Emergency Fund (merged view) + Forecast
      - Baseline choices (completed months this year): Mean / Median / Trimmed / Outlier-Adjusted (IQR).
      - Uses *default_baseline* for the 6/9/12-month targets and the Q4 forecast.
      - Prints a comparison table showing how the forecast changes under each baseline.
      - Then prints the month-by-month category audit blocks (side-by-side by default).

    Args:
        topn (int): top categories per month in the audit
        columns (int): 1 = sequential blocks; 2 = side-by-side
        default_baseline (str): which baseline to use by default for targets & forecast
    """
    df = load_main_df()
    cf = compute_inflow_outflow(df)
    cf = cf.loc[~_is_tax_row(cf, category_col="Category", text_cols=["Description", "Transact", "ACCOUNT"])].copy()
    cf = _apply_category_exclusions(cf, "Category", exclude_categories)

    year, completed = _completed_months_this_year()
    if not completed:
        print("\n=== EMERGENCY FUND & FORECAST ===")
        print("No completed months this year yet.\n")
        return

    monthly = _monthly_expense_totals(cf, year, completed)
    baselines = _compute_baselines(monthly)
    if baselines is None:
        print("\n=== EMERGENCY FUND & FORECAST ===")
        print("No expense data found for completed months.\n")
        return

    # clamp default name
    if default_baseline not in baselines:
        default_baseline = "Outlier-Adjusted"

    chosen = baselines[default_baseline]

    # header + months used + per-month totals
    print("\n=== EMERGENCY FUND & YEAR-END FORECAST (Merged) ===")
    print("Baseline options are computed from SGOT outflows for all COMPLETED months this year.")
    print("Use Outlier-Adjusted (IQR) to avoid spike months inflating the baseline.\n")

    print("Months used:")
    print("  " + ", ".join(_month_label(year, m) for m in completed))

    print("\nPer-month totals (expenses only):")
    for m, v in zip(completed, monthly):
        print(f"  {_month_label(year, m)}: ${v:,.2f}")

    # show baselines
    print("\n--- Baseline options (Avg monthly expenses) ---")
    for k in ("Mean", "Median", "Trimmed", "Outlier-Adjusted"):
        if k in baselines:
            mark = " (default)" if k == default_baseline else ""
            print(f"  {k:16}: ${baselines[k]:,.2f}{mark}")

    # emergency fund targets using chosen baseline
    print(f"\n--- Emergency Fund Targets using {default_baseline} ---")
    for n in (6, 9, 12):
        print(f"  {n}-month fund: ${baselines[default_baseline]*n:,.2f}")

    # forecast comparison under each baseline
    # months left in year
    last_completed = max(completed)
    months_left = max(0, 12 - last_completed)
    months_left = min(months_left, 12)  # safety
    print(f"\n--- Forecast Comparison ({year} Full-Year) ---")
    print(f"(Assumes monthly income in remaining months = previous-year Q4 average inflow; months left = {months_left})")
    print(f"Baseline            |   {year} Income   |  {year} Expenses  |  {year} Net")
    print("--------------------|-----------------|------------------|----------------")
    model_meta = None
    for name, base in baselines.items():
        res = _forecast_full_year(cf, year, base, months_left=months_left)
        if model_meta is None:
            model_meta = res
        print(f"{name:20} | ${res['inc_total']:>13,.2f} | ${res['exp_total']:>13,.2f} | ${res['net_total']:>12,.2f}")

    if model_meta is not None:
        print(f"\nIncome model for remaining months (per month): ${model_meta['income_mo_model']:,.2f}")
        print(f"Source: {model_meta['income_model_note']}")

    # Big-picture audit: every month’s top categories
    print(f"\n=== Month-by-Month Category Audit (Top {topn}) ===")
    blocks = []
    for m in completed:
        pairs = _top_categories_for_month(cf, year, m, topn=topn)
        blocks.append(_format_block_for_month(year, m, pairs))
    _print_blocks_side_by_side(blocks, columns=columns, col_width=46)

def _estimate_monthly_ss_income(year: int) -> float:
    """Estimate monthly Social Security income from selected year inflows."""
    df = load_main_df(_year_to_tag(int(year)))
    cf = compute_inflow_outflow(df)
    months = _completed_months_for_year(int(year))
    if not months:
        return 0.0

    in_year = (cf["Date"].dt.year == int(year)) & (cf["Date"].dt.month.isin(months))
    cat_up = cf["Category"].astype(str).str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
    text_blob = (
        _series(cf, "Transact") + " " +
        _series(cf, "Description") + " " +
        _series(cf, "ACCOUNT") + " " +
        _series(cf, "Category")
    ).str.lower()
    is_ss_cat = cat_up.str.contains(r"(?:\bS_S\b|\bSS\b|\bSSA\b|SOCIAL SECURITY)", regex=True, na=False)
    is_ss_text = text_blob.str.contains(CF_SS_REGEX, na=False)
    ss_mask = in_year & (cf["inflow"] > 0) & (is_ss_cat | is_ss_text)
    ss_total = float(cf.loc[ss_mask, "inflow"].sum())
    return ss_total / max(1, len(months))

def _parse_pension_phases(raw: str) -> list[tuple[int, float]]:
    """
    Parse pension phases format:
      '5:12819' or '5:12819,10:9000'
    Returns list of (years, monthly_amount).
    """
    out: list[tuple[int, float]] = []
    for part in [p.strip() for p in str(raw).split(",") if str(p).strip()]:
        if ":" not in part:
            raise ValueError(f"Invalid phase '{part}'. Use years:amount")
        y_txt, amt_txt = [x.strip() for x in part.split(":", 1)]
        years = int(y_txt)
        amount = float(amt_txt.replace("$", "").replace(",", ""))
        if years <= 0:
            raise ValueError(f"Phase years must be > 0: '{part}'")
        out.append((years, amount))
    if not out:
        raise ValueError("No pension phases provided.")
    return out

def retirement_predictor():
    """
    Retirement predictor:
    - Uses emergency-fund spending baseline (tax excluded + optional non-essential exclusions)
    - Income = Social Security + pension phase schedule
    - Shows yearly shortfall/surplus and required savings withdrawals
    """
    active_year = get_active_year()
    compare_raw = input(f"Use which compare year for spending baseline? [default {active_year-1}]: ").strip()
    compare_year = int(compare_raw) if compare_raw.isdigit() else (active_year - 1)
    excluded = _prompt_optional_excluded_categories()

    # Spending baseline from option 9.6 method; fallback to active-year monthly average
    try:
        base_data = _build_emergency_base_comparison(compare_year, active_year, excluded_categories=excluded)
        base_monthly_spend = float(base_data["base_monthly_avg"])
        base_note = f"YoY base from {compare_year} vs {active_year}"
    except Exception:
        cf = _load_filtered_emergency_cf_for_year(active_year, excluded_categories=excluded)
        months = _completed_months_for_year(active_year)
        vals = []
        for m in months:
            mask = (cf["Date"].dt.year == active_year) & (cf["Date"].dt.month == m)
            vals.append(float(cf.loc[mask, "outflow"].sum()))
        base_monthly_spend = float(np.mean(np.array(vals, dtype=float))) if vals else 0.0
        base_note = f"Fallback base from {active_year} completed months"

    ss_default = _estimate_monthly_ss_income(active_year)
    ss_raw = input(f"Monthly Social Security income [default ${ss_default:,.2f}]: ").strip()
    ss_monthly = float(ss_raw.replace("$", "").replace(",", "")) if ss_raw else float(ss_default)

    phases_raw = input("Pension phases years:amount [default 5:12819] (example 5:12819,10:9000): ").strip()
    if not phases_raw:
        phases_raw = "5:12819"
    try:
        pension_phases = _parse_pension_phases(phases_raw)
    except Exception as exc:
        print(f"Invalid pension phases: {exc}")
        return

    # Always project 10 years (even if pension phases are shorter) so you can
    # see the post-pension withdrawal picture.
    horizon_years = 10

    infl_raw = input("Annual spending inflation % [default 0]: ").strip()
    inflation = (float(infl_raw) / 100.0) if infl_raw else 0.0
    ss_cola_raw = input("Annual SS COLA % [default 0]: ").strip()
    ss_cola = (float(ss_cola_raw) / 100.0) if ss_cola_raw else 0.0
    tax_rate_raw = input("Estimated effective tax rate % on gross income [default 12]: ").strip()
    eff_tax_rate = (float(tax_rate_raw) / 100.0) if tax_rate_raw else 0.12

    hc_start_raw = input("Monthly healthcare cost in year 1 [default 0]: ").strip()
    hc_monthly_start = float(hc_start_raw.replace("$", "").replace(",", "")) if hc_start_raw else 0.0
    hc_infl_raw = input(f"Annual healthcare inflation % [default {inflation*100:.2f}]: ").strip()
    hc_inflation = (float(hc_infl_raw) / 100.0) if hc_infl_raw else inflation
    hc_pct_gross_raw = input("Healthcare as % of gross annual income (optional) [default 0]: ").strip()
    hc_pct_gross = (float(hc_pct_gross_raw) / 100.0) if hc_pct_gross_raw else 0.0
    portfolio_raw = input("Current investable portfolio balance (for scorecard) [default 0]: ").strip()
    portfolio_balance = float(portfolio_raw.replace("$", "").replace(",", "")) if portfolio_raw else 0.0
    chunk_ret_raw = input("Chunk view return path % [default 4]: ").strip()
    chunk_return = (float(chunk_ret_raw) / 100.0) if chunk_ret_raw else 0.04
    safe_draw_raw = input("Safe drawdown rate % for readiness ratio [default 4]: ").strip()
    safe_draw_rate = (float(safe_draw_raw) / 100.0) if safe_draw_raw else 0.04
    essential_ratio_raw = input("Essential spending % of total spend [default 70]: ").strip()
    essential_ratio = (float(essential_ratio_raw) / 100.0) if essential_ratio_raw else 0.70
    cash_reserve_raw = input("Current cash reserve balance [default 0]: ").strip()
    cash_reserve = float(cash_reserve_raw.replace("$", "").replace(",", "")) if cash_reserve_raw else 0.0
    extra_raw = input("Extra discretionary spending per month [default 0]: ").strip()
    extra_monthly = float(extra_raw.replace("$", "").replace(",", "")) if extra_raw else 0.0
    extra_start_raw = input("Extra spending start year (1-10) [default 1]: ").strip()
    extra_start_year = int(extra_start_raw) if extra_start_raw.isdigit() else 1
    extra_end_raw = input("Extra spending end year (1-10) [default 10]: ").strip()
    extra_end_year = int(extra_end_raw) if extra_end_raw.isdigit() else 10
    extra_start_year = max(1, min(10, extra_start_year))
    extra_end_year = max(extra_start_year, min(10, extra_end_year))
    current_age_raw = input("Current age [default 56]: ").strip()
    current_age = int(current_age_raw) if current_age_raw.isdigit() else 56
    rmd_age_raw = input("RMD start age [default 75]: ").strip()
    rmd_age = int(rmd_age_raw) if rmd_age_raw.isdigit() else 75
    medicare_age_raw = input("Medicare age for healthcare step-down [default 65]: ").strip()
    medicare_age = int(medicare_age_raw) if medicare_age_raw.isdigit() else 65
    medicare_drop_raw = input("Healthcare cost reduction at Medicare age % [default 35]: ").strip()
    medicare_drop_pct = (float(medicare_drop_raw) / 100.0) if medicare_drop_raw else 0.35
    medicare_drop_pct = max(0.0, min(0.95, medicare_drop_pct))

    years_to_rmd = max(0, int(rmd_age) - int(current_age))
    model_years = max(horizon_years, years_to_rmd)

    # Build pension schedule per projection year
    pension_by_year: list[float] = []
    for years, amount in pension_phases:
        pension_by_year.extend([float(amount)] * int(years))
    if len(pension_by_year) < model_years:
        pension_by_year.extend([0.0] * (model_years - len(pension_by_year)))
    pension_by_year = pension_by_year[:model_years]

    print("\n=== RETIREMENT PREDICTOR ===")
    print(f"Baseline monthly spend: ${base_monthly_spend:,.2f}  ({base_note})")
    print(f"Monthly SS income start: ${ss_monthly:,.2f}")
    print(f"Pension phases: {', '.join([f'{y}y @ ${a:,.2f}/mo' for y, a in pension_phases])}")
    print(f"Estimated effective tax rate: {eff_tax_rate*100:.2f}%")
    print(f"Healthcare model: start ${hc_monthly_start:,.2f}/mo, infl {hc_inflation*100:.2f}%, gross-income factor {hc_pct_gross*100:.2f}%")
    print(f"Extra spending model: ${extra_monthly:,.2f}/mo in projection years {extra_start_year}-{extra_end_year}")
    print(f"Ages: current {current_age}, Medicare step-down {medicare_age} ({medicare_drop_pct*100:.1f}% reduction), RMD age {rmd_age}")
    if excluded:
        print("Additional excluded categories from spending baseline: " + ", ".join(sorted(excluded)))

    print("\n10-Year View (copy/paste format)")
    print(f"{'Year':>4} | {'Age':>3} | {'Gross/Yr':>12} | {'Tax/Yr':>11} | {'Net/Yr':>12} | {'Spend/Yr':>12} | {'Gap/Yr':>11} | {'Withdraw/Yr':>12} | {'Cum Withdraw':>14}")
    print("-" * 120)
    cumulative_withdraw = 0.0
    annual_withdrawals: list[float] = []
    annual_spends: list[float] = []
    annual_gross_incomes: list[float] = []
    annual_net_incomes: list[float] = []
    annual_healthcare: list[float] = []
    for i in range(1, model_years + 1):
        age_i = int(current_age) + (i - 1)
        ss_i = ss_monthly * ((1.0 + ss_cola) ** (i - 1))
        pension_i = pension_by_year[i - 1]
        income_i = ss_i + pension_i
        spend_i = base_monthly_spend * ((1.0 + inflation) ** (i - 1))
        gross_annual_i = income_i * 12.0
        taxes_annual_i = max(0.0, gross_annual_i * eff_tax_rate)
        net_annual_i = gross_annual_i - taxes_annual_i

        hc_annual_fixed_i = (hc_monthly_start * ((1.0 + hc_inflation) ** (i - 1))) * 12.0
        if age_i >= int(medicare_age):
            hc_annual_fixed_i = hc_annual_fixed_i * (1.0 - medicare_drop_pct)
        hc_annual_income_linked_i = gross_annual_i * hc_pct_gross
        hc_annual_i = max(hc_annual_fixed_i, hc_annual_income_linked_i)
        extra_annual_i = (extra_monthly * 12.0) if (extra_start_year <= i <= extra_end_year) else 0.0

        spend_annual_i = (spend_i * 12.0) + hc_annual_i + extra_annual_i
        net_gap_annual_i = spend_annual_i - net_annual_i
        annual_withdraw_i = max(0.0, net_gap_annual_i)
        annual_withdrawals.append(float(annual_withdraw_i))
        annual_spends.append(float(spend_annual_i))
        annual_gross_incomes.append(float(gross_annual_i))
        annual_net_incomes.append(float(net_annual_i))
        annual_healthcare.append(float(hc_annual_i))
        cumulative_withdraw += annual_withdraw_i
        if i <= horizon_years:
            print(
                f"{i:>4} | "
                f"{age_i:>3} | "
                f"${gross_annual_i:>11,.2f} | "
                f"${taxes_annual_i:>10,.2f} | "
                f"${net_annual_i:>11,.2f} | "
                f"${spend_annual_i:>11,.2f} | "
                f"${net_gap_annual_i:>10,.2f} | "
                f"${annual_withdraw_i:>11,.2f} | "
                f"${cumulative_withdraw:>13,.2f}"
            )

    print("\nNotes:")
    print("  - Gross/Yr = SS + pension before taxes.")
    print("  - Tax/Yr uses your effective tax-rate assumption.")
    print("  - Healthcare/Yr = max(inflated fixed healthcare, % of gross income).")
    print("  - Net Gap/Yr > 0 means savings withdrawal needed.")
    first_year_income = ss_monthly + (pension_by_year[0] if pension_by_year else 0.0)
    print(f"  - Year-1 modeled monthly income: ${first_year_income:,.2f}")

    # Retirement readiness scorecard
    print("\n=== RETIREMENT READINESS SCORECARD ===")
    if not annual_spends:
        print("No projection rows available.")
        return

    yr1_spend = float(annual_spends[0])
    yr1_withdraw = float(annual_withdrawals[0]) if annual_withdrawals else 0.0
    yr1_gross = float(annual_gross_incomes[0]) if annual_gross_incomes else 0.0
    yr1_essential = yr1_spend * max(0.0, min(1.0, essential_ratio))
    yr1_guaranteed = yr1_gross  # SS + pension only in this model
    ten_year_draw = float(sum(annual_withdrawals[:horizon_years]))

    if portfolio_balance > 0:
        spend_multiple = portfolio_balance / max(1.0, yr1_spend)
        wr_year1 = yr1_withdraw / portfolio_balance
        draw_pct_10y = ten_year_draw / portfolio_balance
        print(f"1) Spending Multiple: {spend_multiple:,.2f}x annual spend")
        print(f"2) Year-1 Withdrawal Rate: {wr_year1*100:,.2f}%")
        print(f"4) 10-Year Total Draw from Savings: ${ten_year_draw:,.2f} ({draw_pct_10y*100:,.2f}% of portfolio)")
    else:
        print("1) Spending Multiple: enter portfolio balance next run to compute")
        print("2) Year-1 Withdrawal Rate: enter portfolio balance next run to compute")
        print(f"4) 10-Year Total Draw from Savings: ${ten_year_draw:,.2f}")

    coverage = (yr1_guaranteed / yr1_essential) if yr1_essential > 0 else 0.0
    print(f"3) Guaranteed-Income Coverage of Essentials (Year 1): {coverage*100:,.2f}%")

    # Deterministic portfolio scenarios using projected annual withdrawals
    if portfolio_balance > 0:
        def _project_end_balance(start_bal: float, annual_return: float, withdrawals: list[float]) -> float:
            bal = float(start_bal)
            for w in withdrawals:
                bal = max(0.0, bal * (1.0 + float(annual_return)) - float(w))
            return bal
        def _project_balance_path(start_bal: float, annual_return: float, withdrawals: list[float]) -> list[float]:
            """Return start-of-year balances for each year plus final end balance."""
            bal = float(start_bal)
            path = [bal]
            for w in withdrawals:
                bal = max(0.0, bal * (1.0 + float(annual_return)) - float(w))
                path.append(bal)
            return path

        withdrawals_10 = annual_withdrawals[:horizon_years]
        withdrawals_rmd = annual_withdrawals[:years_to_rmd] if years_to_rmd > 0 else []
        path_chunk_full = _project_balance_path(portfolio_balance, chunk_return, annual_withdrawals)

        bal_4 = _project_end_balance(portfolio_balance, 0.04, withdrawals_10)
        bal_8 = _project_end_balance(portfolio_balance, 0.08, withdrawals_10)
        print(f"5) 10-Year Scenario (4% return): ending portfolio ${bal_4:,.2f}")
        print(f"   10-Year Scenario (8% return): ending portfolio ${bal_8:,.2f}")
        if years_to_rmd > 0:
            bal_rmd_4 = _project_end_balance(portfolio_balance, 0.04, withdrawals_rmd)
            bal_rmd_8 = _project_end_balance(portfolio_balance, 0.08, withdrawals_rmd)
            print(f"   Portfolio at RMD age {rmd_age} ({years_to_rmd} years):")
            print(f"     4% return: ${bal_rmd_4:,.2f}")
            print(f"     8% return: ${bal_rmd_8:,.2f}")
        else:
            print(f"   RMD age {rmd_age} is now or already passed (current age {current_age}).")

        run_mc_raw = input("Run Monte Carlo 10-year simulation? (Y/n): ").strip().lower()
        run_mc = (run_mc_raw in {"", "y", "yes"})
        if run_mc:
            mc_ret_raw = input("Monte Carlo expected annual return % [default 6]: ").strip()
            mc_vol_raw = input("Monte Carlo annual volatility % [default 12]: ").strip()
            mc_runs_raw = input("Monte Carlo runs [default 5000]: ").strip()
            mc_mu = (float(mc_ret_raw) / 100.0) if mc_ret_raw else 0.06
            mc_vol = (float(mc_vol_raw) / 100.0) if mc_vol_raw else 0.12
            mc_runs = int(mc_runs_raw) if mc_runs_raw.isdigit() else 5000
            mc_runs = max(500, min(50000, mc_runs))

            rets = np.random.normal(loc=mc_mu, scale=mc_vol, size=(mc_runs, model_years))
            bal = np.full(mc_runs, float(portfolio_balance), dtype=float)
            bal_at_10 = None
            bal_at_rmd = None
            for t in range(model_years):
                bal = np.maximum(0.0, bal * (1.0 + rets[:, t]) - float(annual_withdrawals[t]))
                if (t + 1) == horizon_years:
                    bal_at_10 = bal.copy()
                if years_to_rmd > 0 and (t + 1) == years_to_rmd:
                    bal_at_rmd = bal.copy()

            if bal_at_10 is not None:
                success_rate_10 = float(np.mean(bal_at_10 > 0.0))
                p10 = float(np.percentile(bal_at_10, 10))
                p50 = float(np.percentile(bal_at_10, 50))
                p90 = float(np.percentile(bal_at_10, 90))
                print(f"   Monte Carlo success rate (portfolio > $0 at 10y): {success_rate_10*100:,.2f}%")
                print(f"   Monte Carlo 10y ending balance percentiles: P10=${p10:,.2f}, P50=${p50:,.2f}, P90=${p90:,.2f}")
            if bal_at_rmd is not None:
                success_rate_rmd = float(np.mean(bal_at_rmd > 0.0))
                p10r = float(np.percentile(bal_at_rmd, 10))
                p50r = float(np.percentile(bal_at_rmd, 50))
                p90r = float(np.percentile(bal_at_rmd, 90))
                print(f"   Monte Carlo success rate at RMD age {rmd_age}: {success_rate_rmd*100:,.2f}%")
                print(f"   Monte Carlo RMD-age balance percentiles: P10=${p10r:,.2f}, P50=${p50r:,.2f}, P90=${p90r:,.2f}")

        # Work longer what-if: 1..4 years
        print("\n=== WORK 1-4 MORE YEARS COMPARISON (4% RETURN) ===")
        work_income_raw = input("Work-income gross per year while delaying retirement [default 200000]: ").strip()
        work_income = float(work_income_raw.replace("$", "").replace(",", "")) if work_income_raw else 200000.0
        work_401k_raw = input("Annual 401k contribution while working [default 30000]: ").strip()
        work_401k = float(work_401k_raw.replace("$", "").replace(",", "")) if work_401k_raw else 30000.0
        work_return_raw = input("Assumed annual return for this work-delay comparison % [default 4]: ").strip()
        work_return = (float(work_return_raw) / 100.0) if work_return_raw else 0.04

        def _simulate_with_work_delay(work_years: int, years: int) -> float:
            bal = float(portfolio_balance)
            years = max(0, min(int(years), len(annual_withdrawals)))
            for t in range(years):
                if t < int(work_years):
                    # While still working: no retirement healthcare line item and no portfolio withdrawal.
                    spend_no_hc = float(max(0.0, annual_spends[t] - annual_healthcare[t]))
                    pretax_after_401k = max(0.0, work_income - work_401k)
                    taxable_savings = max(0.0, (pretax_after_401k * (1.0 - eff_tax_rate)) - spend_no_hc)
                    contrib = float(work_401k + taxable_savings)
                    bal = max(0.0, bal * (1.0 + work_return) + contrib)
                else:
                    bal = max(0.0, bal * (1.0 + work_return) - float(annual_withdrawals[t]))
            return bal

        years_for_rmd = years_to_rmd if years_to_rmd > 0 else len(annual_withdrawals)
        print("Years Worked | Portfolio @ Retirement Start | Portfolio @ 10y From Now | Portfolio @ RMD Age | Gain vs Retire-Now @ RMD")
        print("-" * 114)
        baseline_rmd = bal_rmd_4 if years_to_rmd > 0 else None
        for wy in (1, 2, 3, 4):
            bal_start_ret = _simulate_with_work_delay(wy, wy)
            bal_10_from_now = _simulate_with_work_delay(wy, horizon_years)
            bal_rmd_from_now = _simulate_with_work_delay(wy, years_for_rmd)
            if baseline_rmd is not None:
                gain = bal_rmd_from_now - float(baseline_rmd)
                gain_txt = f"${gain:,.2f}"
            else:
                gain_txt = "N/A"
            print(
                f"{wy:>11} | "
                f"${bal_start_ret:>27,.2f} | "
                f"${bal_10_from_now:>22,.2f} | "
                f"${bal_rmd_from_now:>18,.2f} | "
                f"{gain_txt:>24}"
            )
    else:
        print("5) 10-Year Scenario (4%/8% + Monte Carlo): enter portfolio balance next run to compute")

    one_year_cash_target = yr1_spend
    two_year_cash_target = yr1_spend * 2.0
    print(f"6) Liquidity Target: 1 year=${one_year_cash_target:,.2f}, 2 years=${two_year_cash_target:,.2f}")
    print(f"   Current cash reserve entered: ${cash_reserve:,.2f}")

    # Comfort extra-spending guidance
    print("\n=== COMFORT EXTRA-SPENDING GUIDANCE ===")
    if portfolio_balance > 0:
        # Headroom relative to year-1 withdrawal guardrails.
        extra_annual_to_2pct = max(0.0, (0.02 * portfolio_balance) - yr1_withdraw)
        extra_annual_to_3pct = max(0.0, (0.03 * portfolio_balance) - yr1_withdraw)

        # Also cap by total 10-year draw guardrails (30% conservative, 40% moderate).
        max_draw_10y_conservative = 0.30 * portfolio_balance
        max_draw_10y_moderate = 0.40 * portfolio_balance
        remaining_10y_conservative = max(0.0, max_draw_10y_conservative - ten_year_draw)
        remaining_10y_moderate = max(0.0, max_draw_10y_moderate - ten_year_draw)
        extra_annual_10y_conservative = remaining_10y_conservative / max(1, horizon_years)
        extra_annual_10y_moderate = remaining_10y_moderate / max(1, horizon_years)

        extra_annual_conservative = max(0.0, min(extra_annual_to_2pct, extra_annual_10y_conservative))
        extra_annual_moderate = max(0.0, min(extra_annual_to_3pct, extra_annual_10y_moderate))

        print(f"Conservative extra spend: ${extra_annual_conservative:,.2f}/yr (${extra_annual_conservative/12.0:,.2f}/mo)")
        print(f"Moderate extra spend:     ${extra_annual_moderate:,.2f}/yr (${extra_annual_moderate/12.0:,.2f}/mo)")
        print("Method: combines year-1 withdrawal-rate guardrails (2%/3%) and 10-year draw guardrails (30%/40%).")

        # 5-year chunk summary for visual planning + guardrails
        chunk_ret_pct = chunk_return * 100.0
        print(f"\n=== 5-YEAR CHUNK VIEW ({chunk_ret_pct:.2f}% PATH) ===")
        print("Key: Dr% = Draw % of Port, X = Spend Coverage, Rdy = Income+SafeDraw Coverage, CashMo = Cash Months of Draw")
        print(f"{'Ch':>2} | {'Ages':>5} | {'StartPort':>12} | {'NetInc':>10} | {'Spend':>10} | {'Draw':>10} | {'Dr%':>6} | {'X':>6} | {'Rdy':>6} | {'CashMo':>6}")
        print("-" * 102)
        n = len(annual_withdrawals)
        for start in range(0, n, 5):
            end = min(start + 5, n)
            chunk_idx = (start // 5) + 1
            age_start = int(current_age) + start
            age_end = int(current_age) + end - 1
            start_port = float(path_chunk_full[start]) if start < len(path_chunk_full) else 0.0
            avg_spend = float(np.mean(np.array(annual_spends[start:end], dtype=float))) if end > start else 0.0
            avg_draw = float(np.mean(np.array(annual_withdrawals[start:end], dtype=float))) if end > start else 0.0
            avg_net_income = float(np.mean(np.array(annual_net_incomes[start:end], dtype=float))) if end > start else 0.0
            draw_pct = (avg_draw / start_port) if start_port > 0 else 0.0
            x_factor = (start_port / avg_spend) if avg_spend > 0 else 0.0
            safe_draw_amt = start_port * float(safe_draw_rate)
            readiness_ratio = ((avg_net_income + safe_draw_amt) / avg_spend) if avg_spend > 0 else 0.0
            cash_months = (cash_reserve / (avg_draw / 12.0)) if avg_draw > 0 else 999.0
            cash_label = f"{cash_months:,.1f}" if cash_months < 900 else "N/A"
            print(
                f"{('C' + str(chunk_idx)):>2} | "
                f"{age_start:>2}-{age_end:<2} | "
                f"${start_port:>11,.0f} | "
                f"${avg_net_income:>9,.0f} | "
                f"${avg_spend:>9,.0f} | "
                f"${avg_draw:>9,.0f} | "
                f"{draw_pct*100:>5,.2f}% | "
                f"{x_factor:>5,.2f}x | "
                f"{readiness_ratio:>5,.2f}x | "
                f"{cash_label:>6}"
            )

        print("\nGuardrail extra-spend caps (per month) by market mode:")
        print("  - Very bad market: keep extra near $0 to ${:,.0f}/mo".format(extra_annual_conservative / 12.0))
        print("  - Average market:  about ${:,.0f} to ${:,.0f}/mo".format(
            extra_annual_conservative / 12.0, extra_annual_moderate / 12.0
        ))
        print("  - Good market:     up to about ${:,.0f}/mo (temporary, review annually)".format(
            (extra_annual_moderate * 1.25) / 12.0
        ))
    else:
        print("Enter portfolio balance in option 16 to compute extra-spend guidance.")





# 7_1_25
def review_cc_charges_between_dates():
    import pandas as pd
    from sqlalchemy import create_engine
    from datetime import datetime, timedelta
    import colorama
    from colorama import Fore, Style
    colorama.init()

    def load_data(year):
        db = f"ONE_BIG_ACCOUNT_combined_data{year}.db"
        table = f"NEW_ONE_BIG_ACCOUNT_data_{year}" if year == 2025 else f"ONE_BIG_ACCOUNT_data_{year}"
        engine = create_engine(f"sqlite:///{db}")
        return pd.read_sql_table(table, engine)

    today = datetime.today()
    default_end = today.replace(day=9)
    default_start = (default_end - timedelta(days=32)).replace(day=9)

    print("\n🔎 Reviewing charges between credit card cycles")
    print(f"Suggested date range: {default_start.strftime('%b %d')} to {default_end.strftime('%b %d')} ({default_start.strftime('%Y')})")

    use_default = input("Use suggested date range? (y/n): ").strip().lower() == 'y'
    if use_default:
        start_date = default_start
        end_date = default_end
    else:
        start_str = input("Enter start date (YYYY-MM-DD): ").strip()
        end_str = input("Enter end date (YYYY-MM-DD): ").strip()
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_str, "%Y-%m-%d")
        except ValueError:
            print("❌ Invalid date format. Returning to menu.")
            return

    year = start_date.year
    prior_year = year - 1

    df_current = load_data(year)
    df_prior = load_data(prior_year) if prior_year >= 2020 else pd.DataFrame(columns=["Date", "Amount", "Account", "Category", "Transact"])

    def filter_and_group(df):
        df['Date'] = pd.to_datetime(df['Date'])
        filtered = df[(df['Date'] >= start_date) & (df['Date'] < end_date)]

        # Exclude income, transfers, and payments
        exclude_categories = ["PAYCHECK", "TRANSFER", "CITY CC PAYMENT", "USAA CC PAYMENT",
                              "ACCOUNT INTEREST", "Security", "CC PAYMENT"]
        filtered = filtered[~filtered['Category'].str.upper().isin([cat.upper() for cat in exclude_categories])]

        # Convert negative charges to positive values (e.g., mortgage)
        filtered['AbsAmount'] = filtered['Amount'].abs()

        return filtered.groupby('ACCOUNT')['AbsAmount'].sum(), filtered

    current_totals, current_data = filter_and_group(df_current)
    prior_totals, _ = filter_and_group(df_prior)

    print(f"\n🧾 Charges from {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}:")
    print("Account        |  Charges     |  Last Year   |  Difference   |  Status")
    print("--------------------------------------------------------------------")
    all_accounts = sorted(set(current_totals.index).union(set(prior_totals.index)))

    for acct in all_accounts:
        now = current_totals.get(acct, 0)
        prev = prior_totals.get(acct, 0)
        diff = now - prev
        status = "⬆️ Higher" if diff > 0 else ("⬇️ Lower" if diff < 0 else "➖ Equal")
        color = Fore.GREEN if diff < 0 else (Fore.RED if diff > 0 else Fore.YELLOW)
        print(f"{acct:<14} ${now:>10,.2f} | ${prev:>10,.2f} | ${diff:>10,.2f}   {color}{status}{Style.RESET_ALL}")

    view = input("\nWould you like to see transaction details? (y/n): ").strip().lower()
    if view == 'y':
        for acct in all_accounts:
            details = current_data[current_data['ACCOUNT'] == acct]
            if not details.empty:
                print(f"\n📋 Transactions for {acct}:")
                details = details.copy()
                details['Transact'] = details['Transact'].str.slice(0, 50)
                print(details[['Date', 'Transact', 'Amount', 'Category']].to_string(index=False))
                print(f"Total: ${details['Amount'].abs().sum():,.2f}")

    input("\n✅ Done. Press Enter to return to main menu...")


def audit_emergency_month(year=None, month=None, min_excluded=500):
    """
    Verify what's counted in the emergency-fund baseline for a given month.
    - Prints included categories + totals
    - Prints largest EXCLUDED rows (>= min_excluded) so you can sanity-check
    Uses the same simple rules as emergency_fund_from_raw().
    """
    import pandas as pd
    from datetime import date

    df = load_main_df().copy()

    # required columns
    need = {"Date","Amount","Category"}
    miss = need - set(df.columns)
    if miss:
        print(f"DB is missing columns: {miss}")
        return

    # types
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df = df[df["Date"].notna() & df["Amount"].notna()].copy()

    # pick month
    today = date.today()
    year = int(year) if year is not None else get_active_year()
    if month is None:
        month = (today.month - 1) if (year == today.year) else 12
    if month < 1:
        print("No completed months yet.")
        return

    m_mask = (df["Date"].dt.year == year) & (df["Date"].dt.month == month)

    # category text
    cat = df["Category"].astype(str)
    cat_lo = cat.str.strip().str.lower()
    cat_up = cat.str.strip().str.upper()

    # same buckets as emergency_fund_from_raw()
    income_cats = {"PAYCHECK","S_S","INCOME ? KP","WORK"}
    exclude_cats = {
        "SECURITY","CITY CC PAYMENT","USAA CC PAYMENT","TRANSFER",
        "COSTCO REBATE","ACCOUNT INTEREST","CC PAYMENT","VANGUARD INVESTMENT","INVESTMENT"
    }

    is_mortgage = cat_lo.eq("mortgage")
    is_income   = cat_up.isin(income_cats)
    is_excluded = cat_up.isin(exclude_cats)

    is_expense = (~is_income & ~is_excluded) | is_mortgage

    # included for the month
    inc = df[m_mask & is_expense].copy()
    inc["outflow"] = inc["Amount"].abs()

    # excluded for the month (show big ones)
    exc = df[m_mask & (~is_expense)].copy()
    exc["abs_amt"] = exc["Amount"].abs()

    # print summary
    ym = f"{year}-{month:02d}"
    used_total = float(inc["outflow"].sum())

    print(f"\n=== AUDIT: Included vs Excluded for {ym} ===")
    print(f"Included total (used in baseline): ${used_total:,.2f}")

    # included by category
    by_cat = inc.groupby("Category")["outflow"].sum().sort_values(ascending=False)
    print("\n-- Included categories --")
    if by_cat.empty:
        print("  (none)")
    else:
        for k, v in by_cat.items():
            print(f"  {k:<22} ${v:>10,.2f}")

    # call out Uncategorized if present
    unc = by_cat.get("Uncategorized", 0.0)
    if unc:
        print(f"\n⚠️  'Uncategorized' included: ${unc:,.2f} (consider fixing categories.csv)")

    # excluded (largest)
    big = exc[exc["abs_amt"] >= float(min_excluded)].copy()
    show_cols = [c for c in ["Date","ACCOUNT","Category","Transact","Description","Amount"] if c in big.columns]
    print(f"\n-- Largest EXCLUDED rows (>= ${min_excluded:,}) --")
    if big.empty:
        print("  (none)")
    else:
        big = big.sort_values("abs_amt", ascending=False)
        print(big[show_cols].head(25).to_string(index=False))




# --- MENU FOR USER INTERACTION ---
def main_menu():
    while True:
        if _prompt_active_year():
            break
    db_path, table_name = get_db_info()
    print(f"Using year: {get_active_year()}")

    def _load_current_table():
        engine = create_engine(f"sqlite:///{db_path}")
        return pd.read_sql_table(table_name, engine)

    def _recategorize_database():
        recategorize_full_table(db_path, table_name)

    def _show_uncategorized_top50():
        df_current = _load_current_table()
        show_uncategorized(df_current, n=50)

    def _run_emergency_estimate():
        df_current = load_main_df()
        excluded = _prompt_optional_excluded_categories()
        show_emergency_fund_estimate(df_current, exclude_categories=excluded)

    def _run_emergency_estimate_drilldown():
        excluded = _prompt_optional_excluded_categories()
        show_emergency_fund_estimate_drilled_down(topn=12, columns=2, exclude_categories=excluded)

    def _run_emergency_estimate_outlier():
        excluded = _prompt_optional_excluded_categories()
        show_emergency_fund_estimate_drilled_down_better(topn=12, columns=2, exclude_categories=excluded)

    def _run_cash_flow_comparison():
        print("\nRunning Year-over-Year Comparison...")
        compare_cash_flow_2024_vs_2025()

    def _review_category_spending():
        year = input("Enter the year to review (e.g., 2025): ").strip()
        month = input("Enter the month to review (e.g., April): ").strip()
        if not year:
            print("Year is required for this report.")
            return
        db_for_year = f"ONE_BIG_ACCOUNT_combined_data{year}.db"
        review_monthly_expense_categories_with_comparison(db_for_year, year, month)

    def _debug_emergency_verification():
        df_current = load_main_df()
        debug_verify_emergency_fund(df_current)

    def _debug_mortgage_inclusion():
        df_current = load_main_df()
        debug_check_mortgage(df_current)

    def _audit_prompt():
        year_input = input("Year (blank = current year): ").strip()
        month_input = input("Month number 1-12 (blank = last completed): ").strip()
        year_value = int(year_input) if year_input else None
        month_value = int(month_input) if month_input else None
        return year_value, month_value

    def _audit_month():
        year_value, month_value = _audit_prompt()
        audit_emergency_month(year_value, month_value)

    def _audit_month_with_drilldown():
        from datetime import date as _date, timedelta as _timedelta
        import calendar

        year_value, month_value = _audit_prompt()
        audit_emergency_month(year_value, month_value)

        if month_value is None:
            today = _date.today()
            last_month_end = today.replace(day=1) - _timedelta(days=1)
            drill_year = year_value if year_value is not None else last_month_end.year
            month_name = last_month_end.strftime("%B")
        elif 1 <= month_value <= 12:
            drill_year = year_value if year_value is not None else _date.today().year
            month_name = calendar.month_name[month_value]
        else:
            print("Invalid month number. Skipping cash flow drilldown.")
            return

        cash_flow_drilldown(drill_year, month_name)

    def _debug_city_check():
        debug_city_sanity_check()

    def _debug_mortgage_totals():
        debug_mortgage_norm_totals()

    # --- BUDGET INSIGHTS ---
    def category_spend_insights(min_months: int = 0, topn: int | None = None):
        """Show expense categories (YTD), avg per active month, and highest month.

        Notes:
        - Uses compute_inflow_outflow so numbers match cash-flow.
        - Lists ALL categories, sorted from highest total to lowest.
        - The `min_months` argument is ignored when set to 0 (default) so every
          category appears; set it >0 if you want to filter for consistency.
        - If `topn` is provided, output is limited to that many rows after sorting.
        """
        df0 = load_main_df()
        cf0 = compute_inflow_outflow(df0)
        exp = cf0[cf0["is_expense"]].copy()
        if exp.empty:
            print("No expense rows found.")
            return

        exp["AmountAbs"] = exp["Amount"].abs()
        piv = exp.pivot_table(index="Category", columns="Month", values="AmountAbs", aggfunc="sum", fill_value=0.0)
        months_present = (piv > 0).sum(axis=1)
        if int(min_months) > 0:
            filt = months_present >= int(min_months)
            if not filt.any():
                print(f"No categories found with at least {min_months} active months.")
                return
            piv = piv[filt]
        ytd = piv.sum(axis=1)
        active = (piv > 0).sum(axis=1).replace(0, 1)
        avg_active = ytd / active
        hi_month = piv.idxmax(axis=1)
        hi_value = piv.max(axis=1)

        ordered_index = ytd.sort_values(ascending=False).index
        if topn is not None:
            try:
                n = int(topn)
                ordered_index = ordered_index[:n]
            except Exception:
                pass
        print("\nExpense categories (ranked by YTD total):")
        print(f"{'Category':<24} | {'YTD Total':>12} | {'Avg/Active Mo':>13} | {'Highest Month (Amt)':>22} | {'Months':>6}")
        print("-" * 92)
        for cat in ordered_index:
            label = "(Uncategorized)" if (pd.isna(cat) or str(cat).strip()=="") else str(cat)
            print(f"{label:<24} | ${ytd[cat]:>11,.2f} | ${avg_active[cat]:>12,.2f} | {hi_month[cat]:<9} (${hi_value[cat]:,.2f}) | {int(active[cat]):>6}")

    def monthly_savings_simulator_topn(percent: float = 15.0, top_n: int = 4, include_mortgage: bool = False):
        """Simulate reducing top-N expense categories each month by a uniform percent.

        - Excludes Mortgage from target categories by default.
        - Prints savings per category (YTD) and monthly net improvements.
        """
        df0 = load_main_df()
        cf0 = compute_inflow_outflow(df0)

        # Determine calendar months present
        order = ["January","February","March","April","May","June","July","August","September","October","November","December"]
        months = [m for m in order if m in set(cf0["Month"].dropna().astype(str))]
        if not months:
            print("No monthly data available.")
            return

        pct = max(0.0, float(percent)) / 100.0
        top_n = int(top_n)

        savings_by_cat = {}
        lines = []
        for m in months:
            inc = float(cf0.loc[cf0["Month"].astype(str)==m, "inflow"].sum())
            exp = float(cf0.loc[cf0["Month"].astype(str)==m, "outflow"].sum())
            net = inc - exp

            exp_m = cf0[(cf0["Month"].astype(str)==m) & (cf0["is_expense"])].copy()
            if not include_mortgage and "Category" in exp_m.columns:
                exp_m = exp_m[exp_m["Category"].astype(str).str.casefold() != "mortgage"]
            if exp_m.empty:
                lines.append((m, inc, exp, net, exp, net, 0.0))
                continue

            exp_m["AmountAbs"] = exp_m["Amount"].abs()
            by_cat = exp_m.groupby("Category")["AmountAbs"].sum().sort_values(ascending=False)
            top = by_cat.head(top_n)
            month_savings = float((top * pct).sum())
            for cat, amt in top.items():
                savings_by_cat[cat] = savings_by_cat.get(cat, 0.0) + float(amt * pct)

            exp_sim = max(0.0, exp - month_savings)
            net_sim = inc - exp_sim
            delta = net_sim - net  # equals month_savings
            lines.append((m, inc, exp, net, exp_sim, net_sim, delta))

        # Print per-category savings summary (YTD)
        print("\nSavings by category (YTD) with top-N-per-month cut:")
        print(f"{'Category':<24} | {'Savings':>12}")
        print("-" * 40)
        total_sav = 0.0
        for cat, sav in sorted(savings_by_cat.items(), key=lambda kv: kv[1], reverse=True):
            label = "(Uncategorized)" if (pd.isna(cat) or str(cat).strip()=="") else str(cat)
            print(f"{label:<24} | ${sav:>11,.2f}")
            total_sav += sav

        # Print monthly summary table
        print("\nMonthly impact (original vs simulated):")
        print(f"{'Month':<10} | {'Inc':>10} | {'Exp':>10} | {'Net':>10} || {'Exp*':>10} | {'Net*':>10} | {'ΔNet':>10}")
        print("-" * 86)
        for m, inc, exp, net, exp_sim, net_sim, delta in lines:
            print(f"{m:<10} | ${inc:>9,.2f} | ${exp:>9,.2f} | ${net:>9,.2f} || ${exp_sim:>9,.2f} | ${net_sim:>9,.2f} | ${delta:>9,.2f}")

        print(f"\nEstimated improvement to YTD net cash flow: ${total_sav:,.2f} (percent={percent:.1f}%, top_n={top_n}, mortgage_included={include_mortgage})")

    def savings_simulator_selected_categories():
        """Pick categories and a percent per category; estimate YTD + monthly savings.

        Flow:
          1) Print the category spend insights (like option 14) for reference.
          2) Prompt for categories to reduce (comma-separated, case-insensitive exact names).
          3) Confirm selection, then prompt for a percent for each selected category.
          4) Output per-category: Original, Percent, Savings, Reduced, Monthly Cut; plus totals.
        """
        # Show the full insights list for selection context
        try:
            category_spend_insights(min_months=0, topn=None)
        except Exception as _:
            pass

        df0 = load_main_df()
        cf0 = compute_inflow_outflow(df0)
        exp = cf0[cf0["is_expense"]].copy()
        if exp.empty:
            print("No expense rows found.")
            return

        exp["AmountAbs"] = exp["Amount"].abs()
        exp_cat_up = exp["Category"].astype(str).str.upper().str.strip()

        raw_cats = input("\nEnter categories to reduce (comma-separated, exact names as shown; blank to cancel): ").strip()
        if not raw_cats:
            return

        selected = [c.strip() for c in raw_cats.split(',') if c.strip()]
        if not selected:
            print("No categories provided.")
            return

        print("\nYou selected these categories:")
        for c in selected:
            print(f"  - {c}")

        # Gather a percent per category
        percents = {}
        for c in selected:
            while True:
                pr = input(f"Percent reduction for '{c}' (e.g., 15): ").strip()
                try:
                    p = max(0.0, float(pr)) / 100.0
                    percents[c] = p
                    break
                except Exception:
                    print("Please enter a number (e.g., 15 for 15%).")

        # Compute savings per selected category
        rows = []
        total_sav = 0.0
        total_monthly = 0.0
        for cat in selected:
            cat_up = cat.upper()
            mask = exp_cat_up == cat_up
            base = float(exp.loc[mask, "AmountAbs"].sum())
            if base <= 0:
                rows.append((cat, 0.0, percents.get(cat, 0.0)*100.0, 0.0, 0.0, 0.0))
                continue
            pct = percents.get(cat, 0.0)
            sav = base * pct
            reduced = base - sav
            monthly_cut = sav / 12.0
            total_sav += sav
            total_monthly += monthly_cut
            rows.append((cat, base, pct*100.0, sav, reduced, monthly_cut))

        print("\nSavings simulation (selected categories, YTD):")
        print(f"{'Category':<24} | {'Original':>12} | {'Percent':>8} | {'Savings':>12} | {'Reduced':>12} | {'Monthly Cut':>12}")
        print("-" * 96)
        for cat, base, pct100, sav, reduced, monthly_cut in rows:
            print(f"{cat:<24} | ${base:>11,.2f} | {pct100:>7.1f}% | ${sav:>11,.2f} | ${reduced:>11,.2f} | ${monthly_cut:>11,.2f}")

        print("-" * 96)
        print(f"Estimated improvement to YTD net cash flow: ${total_sav:,.2f}")
        print(f"Average monthly reduction required across selected categories: ${total_monthly:,.2f}")

        # Optional: apply these custom percents to the monthly cash flow view
        try:
            apply_q = input("\nApply these reductions to the monthly cash flow view? (y/N): ").strip().lower()
        except Exception:
            apply_q = ""
        if apply_q in {"y", "yes"}:
            cf_all = cf0  # from above
            order = [
                "January","February","March","April","May","June",
                "July","August","September","October","November","December"
            ]
            months = [m for m in order if m in set(cf_all["Month"].dropna().astype(str))]
            lines = []

            # Map for fast lookup
            percents_up = {k.upper().strip(): v for k, v in percents.items()}

            for m in months:
                mask_m = cf_all["Month"].astype(str) == m
                inc = float(cf_all.loc[mask_m, "inflow"].sum())
                exp = float(cf_all.loc[mask_m, "outflow"].sum())
                net = inc - exp

                # Expense rows for month m
                exp_m = cf_all[(mask_m) & (cf_all["is_expense"])].copy()
                if exp_m.empty:
                    lines.append((m, inc, exp, net, exp, net, 0.0))
                    continue

                cat_up_m = exp_m.get("Category").astype(str).str.upper().str.strip()
                pct_m = cat_up_m.map(percents_up).fillna(0.0)
                amt_abs = exp_m["Amount"].abs()
                month_savings = float((amt_abs * pct_m).sum())

                exp_sim = max(0.0, exp - month_savings)
                net_sim = inc - exp_sim
                delta = net_sim - net  # equals month_savings
                lines.append((m, inc, exp, net, exp_sim, net_sim, delta))

            print("\nMonthly impact (original vs simulated with selected categories):")
            print(f"{'Month':<10} | {'Inc':>10} | {'Exp':>10} | {'Net':>10} || {'Exp*':>10} | {'Net*':>10} | {'ΔNet':>10}")
            print("-" * 86)
            total_delta = 0.0
            for m, inc, exp, net, exp_sim, net_sim, delta in lines:
                total_delta += float(delta)
                print(f"{m:<10} | ${inc:>9,.2f} | ${exp:>9,.2f} | ${net:>9,.2f} || ${exp_sim:>9,.2f} | ${net_sim:>9,.2f} | ${delta:>9,.2f}")

            print(f"\nSimulated improvement to YTD net cash flow (sum of monthly ΔNet): ${total_delta:,.2f}")

    def _show_quick_start():
        print("\nFirst Review & Printouts (Quick Start):")
        print("  Use these for your first review and printing:")
        print("    - 4   Lookup transactions by month and category")
        print("    - 5   Monthly and quarterly summary breakdown")
        print("    - 5x  Export quarterly summary (Excel/CSV/HTML)")
        print("    - 5.2 Monthly vs average (expenses)")
        print("    - 5.2x Export monthly vs average (Excel/CSV/HTML)")
        print("    - 8p  Cash flow overview (printer-friendly)")
        print("    - 8.2p Expense transactions grouped (printer-friendly)")
        print("    - 14p Category insights (printer-friendly)")
        print("    - 8x  Export cash flow overview (Excel/CSV/HTML)")
        print("    - 8.2x Export expense transactions (Excel/CSV/HTML)")
        print("    - 14x Export category insights (Excel/CSV/HTML)")
        print("    - 15x Monthly review: export 5x, 5.2x, 8x, 8.2x, 14x")
        print("    Tip: Use 'xd' in Setup to set exports subfolder (e.g., printed YYYY-MM-DD)")

    def _show_menu(menu_sections, compact: bool = True):
        print("\n======== FINANCE PROGRAM MENU ========")
        try:
            _cur_sub = EXPORTS_SUBDIR if (EXPORTS_SUBDIR and str(EXPORTS_SUBDIR).strip()) else None
        except NameError:
            _cur_sub = None
        eff_dir = f"exports/{_cur_sub}" if _cur_sub else "exports/"
        print(f"Year: {get_active_year()} | Exports folder: {eff_dir}")

        if compact:
            print("\nCompact view (less scrolling):")
            for section, options in menu_sections:
                keys = ", ".join([str(key) for key, _label, _ in options])
                print(f"  {section}: {keys}")
            print("\nCommands: m=full menu, c=compact menu, qs=quick start, y=switch year, 0=exit")
            return

        for section, options in menu_sections:
            print(f"\n{section}:")
            for key, label, _ in options:
                print(f"  {key:>5} - {label}")
        print("\nCommands: c=compact menu, qs=quick start, y=switch year, 0=exit")

    menu_sections = [
        ("Setup & Maintenance", [
            ("1", "Rebuild database from latest bank exports", create_data_base),
            ("2", "Re-categorize database with latest categories.csv", _recategorize_database),
            ("3", "Show uncategorized transactions (top 50)", _show_uncategorized_top50),
            ("ab", "Enter account balance snapshot", enter_account_balance_snapshot),
            ("xd", "Set export subfolder (under 'exports')", set_export_subfolder),
        ]),
        ("Reports & Lookups", [
            ("4", "Lookup transactions by month and category", lookup_by_month_and_category),
            ("5", "Display monthly and quarterly summary breakdown", display_monthly_and_quarterly_summary),
            ("5.1", "Quarterly income summary", display_quarterly_income_summary),
            ("5.2", "Monthly vs average (expenses)", monthly_vs_average_expenses),
            ("6", "Show transactions marked 'LOOK INTO'", show_look_into_transactions),
            ("6.5", "Print NANNY TAX transactions for active year", print_nanny_tax_transactions_for_year),
            ("6.6", "Show taxes paid by month + total", show_taxes_paid_by_month),
            ("6.7", "Compare Costco credit card payments by month (2024-2026)", show_city_cc_payments_by_month_comparison),
            ("7", "Show transactions grouped by category", show_all_transactions_grouped_by_category),
            ("8", "Cash flow overview by month", cash_flow_by_month),
            ("8p", "Cash flow overview by month (printer-friendly)", cash_flow_by_month_printable),
            ("8.1", "List income transactions for a month", list_income_transactions_for_month),
            ("8.2", "List expense transactions for a month (grouped)", list_expense_transactions_for_month_grouped),
            ("8.2p", "List expense transactions for a month (printer-friendly)", list_expense_transactions_for_month_grouped_printable),
            ("14p", "Category insights (printer-friendly)", category_spend_insights_printable),
            ("14", "Consistent expense categories (min 6 months)", category_spend_insights),
            ("14.1", "Monthly savings simulator (top 4 @ 15%)", monthly_savings_simulator_topn),
            ("14.2", "Savings simulator (pick categories, custom %)", savings_simulator_selected_categories),
            ("9", "Emergency fund estimate (standard)", _run_emergency_estimate),
            ("9.5", "Emergency fund estimate drilldown (side-by-side)", _run_emergency_estimate_drilldown),
            ("9.8", "Emergency fund estimate drilldown with outlier trim", _run_emergency_estimate_outlier),
            ("9.6", "Base funds comparison (YoY + category deltas)", emergency_base_funds_comparison_report),
            ("9.7", "Big picture savings view (base spend + transfer guide)", show_big_picture_savings_summary),
            ("9.75", "Account balance trend + funded bucket status", show_account_balance_trend_and_funding_status),
            ("10", "Forecast year-end net cash flow (2025 vs 2024)", forecast_year_end),
            ("11", "Compare monthly net cash flow: 2024 vs 2025", _run_cash_flow_comparison),
            ("12", "Review category spending with comparison", _review_category_spending),
            ("13", "Review transactions between custom dates", review_cc_charges_between_dates),
            ("16", "Retirement predictor (SS + pension + savings draw)", retirement_predictor),
        ]),
        ("Exports", [
            ("5x", "Export quarterly summary (Excel/CSV/HTML)", display_monthly_and_quarterly_summary_export),
            ("5.2x", "Export monthly vs average (expenses)", monthly_vs_average_expenses_export),
            ("8x", "Export cash flow overview by month (Excel/CSV/HTML)", cash_flow_by_month_export),
            ("8.2x", "Export expense transactions for a month (Excel/CSV/HTML)", list_expense_transactions_for_month_grouped_export),
            ("14x", "Export category insights (Excel/CSV/HTML)", category_spend_insights_export),
            ("15x", "Monthly review: export 5x, 5.2x, 8x, 8.2x, 14x", monthly_review_exports),
        ]),
        ("HTML-Only Exports", [
            ("5xh", "Export quarterly summary (CSV/HTML only)", display_monthly_and_quarterly_summary_export_html),
            ("5xhc", "Export quarterly summary combined (HTML only)", quarterly_summary_combined_export_html),
            ("5.2xh", "Export monthly vs average (CSV/HTML only)", monthly_vs_average_expenses_export_html),
            ("8xh", "Export cash flow overview (CSV/HTML only)", cash_flow_by_month_export_html),
            ("8.2xh", "Export expense transactions (CSV/HTML only)", list_expense_transactions_for_month_grouped_export_html),
            ("14xh", "Export category insights (CSV/HTML only)", category_spend_insights_export_html),
            ("15xh", "Monthly review: HTML-only exports", monthly_review_exports_html),
        ]),
        ("Charts (HTML)", [
            ("8ch", "Cash flow by month (chart)", cash_flow_by_month_chart_html),
            ("14ch", "Category insights Top 10 (chart)", category_insights_chart_html),
            ("5.2ch", "Monthly vs average (chart)", monthly_vs_average_chart_html),
            ("9.6ch", "Base funds comparison (chart)", emergency_base_funds_comparison_chart_html),
        ]),
        ("Emergency Fund Audits & Debug", [
            ("92", "Audit emergency fund month + cash flow drilldown", _audit_month_with_drilldown),
            ("93", "Audit emergency fund month (included vs excluded)", _audit_month),
            ("94", "Check if mortgage is counted in expenses", _debug_mortgage_inclusion),
            ("95", "Emergency fund (raw category quick calc)", emergency_fund_from_raw),
            ("96", "City Visa sanity check", _debug_city_check),
            ("97", "Find mortgage rows in raw data", quick_find_mortgage_rows),
            ("98", "Mortgage totals used by reports", _debug_mortgage_totals),
            ("99", "Emergency fund verification (normalized)", _debug_emergency_verification),
        ]),
    ]

    actions = {}
    for _, options in menu_sections:
        for key, _label, handler in options:
            actions[key] = handler

    menu_compact = True
    while True:
        _show_menu(menu_sections, compact=menu_compact)
        choice = input("\nSelect an option: ").strip().lower()
        if choice == "0":
            print("Exiting...")
            break
        if choice == "m":
            menu_compact = False
            continue
        if choice == "c":
            menu_compact = True
            continue
        if choice == "qs":
            _show_quick_start()
            continue
        if choice == "y":
            if _prompt_active_year():
                db_path, table_name = get_db_info()
                print(f"Switched to year: {get_active_year()}")
            continue

        action = actions.get(choice)
        if action is None:
            print("Invalid choice. Please try again.")
            continue

        try:
            action()
        except Exception as exc:
            print(f"Error running option {choice}: {exc}")
def debug_mortgage_norm_totals():
    """
    Prints the mortgage totals that ALL reports use (normalized outflows).
    Zero REPL. Zero imports. Just run from the menu.
    """
    import pandas as pd

    df = load_main_df()                  # read from your DB
    dn = normalize_transactions(df)      # use your normalizer

    mort = dn[(dn["is_expense"]) & (dn["category"].astype(str).str.casefold()=="mortgage")].copy()

    if mort.empty:
        print("\n(No mortgage rows counted as expenses in the normalized data.)")
        return

    mort["ym"] = pd.to_datetime(mort["date"]).dt.to_period("M").astype(str)
    by_month = mort.groupby("ym")["outflow"].sum().sort_index()

    print("\n=== Mortgage totals used by Option 5/8/9 (normalized outflow) ===")
    for ym, val in by_month.items():
        print(f"  {ym}: ${val:,.2f}")


def debug_city_sanity_check():
    df = load_main_df()
    city = df[df["ACCOUNT"]=="COSTCO CITY BANK"].copy()

    nan_pct = round(city["Amount"].isna().mean()*100, 2) if len(city) else 0.0
    print("\n=== City Visa Sanity Check ===")
    print(f"Rows: {len(city)} | % Amount NaN: {nan_pct}%")

    month = "August"  # change if you want
    g_sum = float(city[(city["Month"]==month) & (city["Category"].str.casefold()=="grocery")]["Amount"].sum())
    print(f"{month} Grocery sum (City only): ${g_sum:,.2f}")

    pay_sum = float(city[(city["Month"]==month) & (city["Category"].str.contains('CC PAYMENT', case=False, na=False))]["Amount"].sum())
    print(f"{month} CC PAYMENT sum (City only): ${pay_sum:,.2f}\n")

# v2025.10.19 - menu cleaned, git baseline tagged

if __name__ == "__main__":
        main_menu()


###########################################
# WORKFLOW SUMMARY
###########################################

## NOTE Current Flow Recap (Your Setup)

## NOTE Download multiple CSVs (bank, credit card, etc.)
# - CSVs downloaded manually from your banks/credit cards

## NOTE Normalize them to a unified column format
# - Handled using a flexible config dictionary that maps column names

## NOTE Concatenate into one pandas DataFrame
# - All cleaned DataFrames are combined with pd.concat()

## NOTE Categorize each transaction (using a custom dictionary)
# - Keyword-based using categories.csv !!!!!
# - Automatically tags transactions
#
#    ##-- how to fix this, streamline review, and prevent rework
#    - All uncategorized transactions are printed with top counts
#    - You can update categories.csv and re-run categorization without reloading CSVs
#    - Review top missed descriptions directly in console with script 

## NOTE Store in a database
# - Data is stored in an SQLite .db file
# - Table name is version-controlled (NEW_ONE_BIG_ACCOUNT_data_2025)

## NOTE Analyze in main.py (monthly/quarterly breakdowns)
# - Supports pivot tables, charts, and exports to Excel or summary printouts

## next steps -------------------------------as of 4/8/25
# ╔══════════════════════════════════════════════════════════════════╗
# ║ 🎯 PROJECT ROADMAP — NEXT PHASES                                ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ 📊 1. Cash Flow + Cost-of-Living Monthly Analysis                ║
# ║ 📅 2. Year-over-Year Comparison                                  ║
# ║ 💰 3. Emergency Fund Estimator                                   ║
# ║ 🌐 4. Web Dashboard (Flask + React)                              ║
# ║ 📱 5. Mobile App to Share Monthly Feedback with Family           ║
# ║ ✂️  6. Recurring Expense Trim + Cloud Backup Cost Review  
#           +AMAZON CHARGES║

# ╚══════════════════════════════════════════════════════════════════╝
# ⚡ Let's build it all — one goal at a time!


