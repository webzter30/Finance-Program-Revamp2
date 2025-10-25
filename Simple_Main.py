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
from sqlalchemy import create_engine
import pandas as pd
from datetime import date

# --- CONFIGURATION ---
YEAR = 'FULL_YEAR_25'
category_mapping_file = "categories.csv"


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

#_______________________
# this loads the sql table into the load_main_df to be used easily in functions. added 6_23_25

def load_main_df(year_tag=YEAR):
    # Extract year digits from the tag (e.g., '25') and convert to full year
    short_year = ''.join(filter(str.isdigit, year_tag))  # → '25'
    full_year = f"20{short_year}"  # → '2025'

    db_file = f"ONE_BIG_ACCOUNT_combined_data{full_year}.db"
    table_name = f"NEW_ONE_BIG_ACCOUNT_data_{full_year}"

    engine = create_engine(f"sqlite:///{db_file}")
    return pd.read_sql_table(table_name, engine)


# --- CATEGORY LOADING ---
def load_category_map(filepath):
    df = pd.read_csv(filepath)
    return dict(zip(df['keyword'].str.lower(), df['category']))

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
account_csv_configs = {
    "JEFF_CHECKING_USAA": {
        "filepath": f"JEFF_CHECKING_USAA_{YEAR}.csv",
        "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
        "account_name": "JEFF CHECKING"
    },
    "JEFF_SAVINGS_USAA": {
        "filepath": f"JEFF_SAVINGS_USAA_{YEAR}.csv",
        "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
        "account_name": "JEFF SAVINGS"
    },
    "JOINT_CHECKING_USAA": {
        "filepath": f"JOINT_CHECKING_USAA_{YEAR}.csv",
        "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
        "account_name": "JOINT CHECKING"
    },
    "USAA_VISA": {
        "filepath": f"USAA_VISA_{YEAR}.csv",
        "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
        "account_name": "USAA VISA"
    },
    "Ohenry_USAA": {
        "filepath": f"Ohenry_USAA_{YEAR}.csv",
        "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
        "account_name": "OHENRY"
    },
    "NANNY_USAA": {
        "filepath": f"NANNY_USAA_{YEAR}.csv",
        "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
        "account_name": "NANNY"
    }, 

    #### CHANGE THE CITY_VISA_YEAR CSV FILE HERE AFTER DOWNLOADING NEW ONE FOR THE MONTH!!!
    "City_Visa": {
        "filepath": f"City_Visa_Year to date_download_10_19_2025.CSV",
        "columns": {"Amount": "Debit", "Description": "Description", "Date": "Date"},
        "account_name": "COSTCO CITY BANK",
        "strip_symbols_from_amount": True
    }
}

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
    df["Transact"] = df["Description"]
    df = apply_categorization(df)
    df["ACCOUNT"] = config["account_name"]

    return df[["Date", "Month", "Transact", "Amount", "Category", "ACCOUNT"]]



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
    print(f"\n⚠️ Found {len(uncategorized)} uncategorized transactions:")
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

    # 🏷️ Apply categories using the 'Transact' column
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


    
    # 🔎 Debug: show what matched
    print("🔍 Manual override applied to Costco:")
    print(df[costco_cond][['Date', 'Transact', 'Amount', 'Category']])

    print("🔍 Manual override applied to USAA Transfer:")
    print(df[usaa_cond][['Date', 'Transact', 'Amount', 'Category']])

    print("🔍 Manual override applied to CC Costco PAYMENT:")
    print(df[ccpay_cond][['Date', 'Transact', 'Amount', 'Category']])

    

    # 💾 Save re-categorized data back to DB
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print("✅ Re-categorized table based on updated categories.csv and manual overrides.")



# --- CREATE DB ---
def create_data_base():
    engine = create_engine('sqlite:///ONE_BIG_ACCOUNT_combined_data2025.db')
    table_name = 'NEW_ONE_BIG_ACCOUNT_data_2025'
    all_dataframes = [load_account_data(cfg) for cfg in account_csv_configs.values()]
    ONE_BIG_ACCOUNT = pd.concat(all_dataframes, ignore_index=True)
    ONE_BIG_ACCOUNT.to_sql(table_name, engine, if_exists='replace', index=False)
    print("✅ Streamlined DB created!")
    show_uncategorized(ONE_BIG_ACCOUNT)

# --- LOOKUP TRANSACTIONS BY MONTH & CATEGORY ---
def lookup_by_month_and_category():
    engine = create_engine("sqlite:///ONE_BIG_ACCOUNT_combined_data2025.db")
    df = pd.read_sql_table("NEW_ONE_BIG_ACCOUNT_data_2025", engine)

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
                total = float(results["Amount"].sum())
                count = int(len(results))
                pos = float(results.loc[results["Amount"] > 0, "Amount"].sum())
                neg = float(results.loc[results["Amount"] < 0, "Amount"].sum())

                print("\n" + "—" * 60)
                print(f"Total for '{selected_cat}' in {month_input}: ${total:,.2f}  ({count} txns)")
                if pos and neg:
                    print(f"  • Sum of positives: ${pos:,.2f}")
                    print(f"  • Sum of negatives: ${neg:,.2f}")
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
    year = year or today.year
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
    today = date.today()
    months = list(range(1, today.month))
    if not months:
        print("No completed months yet.")
        return

    # Per-month totals
    per = []
    used = []
    for m in months:
        mask = (df["Date"].dt.year == today.year) & (df["Date"].dt.month == m) & (df["outflow"] > 0)
        total = float(df.loc[mask, "outflow"].sum())
        used.append(f"{today.year}-{m:02d}")
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
    mask_last = (df["Date"].dt.year == today.year) & (df["Date"].dt.month == last_m) & (df["outflow"] > 0)
    top = (df.loc[mask_last]
             .groupby(df.loc[mask_last, "Category"].astype(str))["outflow"]
             .sum()
             .sort_values(ascending=False)
             .head(12))
    print(f"\n--- Top categories in {today.year}-{last_m:02d} ---")
    if top.empty:
        print("  (none)")
    else:
        for k, v in top.items():
            print(f"  - {k}: ${v:,.2f}")


## THIS SHOWS ALL TRANSACTIONS UNDER EACH INDIVIDUAL CATEGORY SO I CAN SCAN THEM TO MAKE SURE
## THE TRANSACATIONS ARE CATEGORIZED CORRECTLY. 


def show_look_into_transactions():
    """Display transactions tagged as 'LOOK INTO' for quick review."""
    engine = create_engine("sqlite:///ONE_BIG_ACCOUNT_combined_data2025.db")
    df = pd.read_sql_table("NEW_ONE_BIG_ACCOUNT_data_2025", engine)

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

def show_all_transactions_grouped_by_category():
    import pandas as pd
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///ONE_BIG_ACCOUNT_combined_data2025.db")
    df = pd.read_sql_table("NEW_ONE_BIG_ACCOUNT_data_2025", engine)

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
    from sqlalchemy import create_engine

    df = pd.read_sql_table(
        "NEW_ONE_BIG_ACCOUNT_data_2025",
        create_engine("sqlite:///ONE_BIG_ACCOUNT_combined_data2025.db")
    )
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

    df = pd.read_sql_table("NEW_ONE_BIG_ACCOUNT_data_2025",
                           create_engine("sqlite:///ONE_BIG_ACCOUNT_combined_data2025.db")).copy()
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
    Normalize transactions:
      - date (datetime)
      - net: signed transaction amount (positive = inflow, negative = outflow)
      - outflow: absolute amount for real expenses
      - is_expense: True for real expenses (excludes transfers, investments, etc.)
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

    # Expense filter
    text = (df["category"].astype(str) + " " + df["description"].astype(str) + " " + df["account"].astype(str)).str.lower()

    exclude_words = [
        "transfer","xfer","payment","paycheck","salary","wages",
        "rebate","refund","interest","dividend","cashback","income",
        "investment","vanguard","fidelity","schwab","ira","401k","hsa",
    ]
    looks_excluded = text.str.contains("|".join(exclude_words), regex=True, na=False)

    # Always include Mortgage
    is_mortgage = df["category"].astype(str).str.strip().str.lower().eq("mortgage")

    df["is_expense"] = (~looks_excluded) | is_mortgage
    df["outflow"] = 0.0
    df.loc[df["is_expense"], "outflow"] = df.loc[df["is_expense"], "net"].abs()
    print ("test me test me !!!!!!!!!!!!!!!!")
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
    months = [(year, m) for m in range(1, date.today().month)]  # completed months this year
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
def show_emergency_fund_estimate(df):
    df_norm = normalize_transactions(df)

    # Guard: usable dates?
    if "date" not in df_norm.columns or df_norm["date"].isna().all():
        print("\n=== EMERGENCY FUND ESTIMATE ===")
        print("No usable dates found. Map your date column and retry.")
        return

    today = date.today()
    completed = [(today.year, m) for m in range(1, today.month)]
    if not completed:
        print("\n=== EMERGENCY FUND ESTIMATE ===")
        print("No completed months this year yet.")
        return

    rows = monthly_expense_totals_table(df_norm, today.year)
    vals = [v for _, v in rows]
    if not vals:
        print("\n=== EMERGENCY FUND ESTIMATE ===")
        print("No expenses found in completed months.")
        return

    baseline = sum(vals) / len(vals)

    print("\n=== EMERGENCY FUND ESTIMATE ===")
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
    today = date.today()
    months = [(today.year, m) for m in range(1, today.month)]
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
def show_emergency_fund_estimate(df):
    """
    Calculate a cost-of-living baseline from completed months this year
    and print 6-, 9-, and 12-month emergency fund estimates.
    """
    df_norm = normalize_transactions(df)

    # Ensure we have a date column
    if "date" not in df_norm.columns:
        print("No date column found in DataFrame.")
        return

    # Only use completed months of the current year
    today = date.today()
    completed = [(today.year, m) for m in range(1, today.month)]
    if not completed:
        print("No completed months this year yet.")
        return

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
    print(f"Months used: {', '.join(f'{y}-{m:02d}' for (y,m) in completed)}")
    print(f"Average monthly expenses: ${baseline:,.2f}\n")
    for months in [6, 9, 12]:
        print(f"{months}-month fund: ${baseline * months:,.2f}")
    print("")

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

def show_emergency_fund_estimate_drilled_down(topn=12, columns=2):
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

    today = date.today()
    year = today.year
    completed_months = list(range(1, today.month))  # months fully completed this year

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
    today = date.today()
    return today.year, list(range(1, today.month))  # completed months only

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

def _q4_income_baseline_from_2024():
    """Use your 2024 Oct–Dec inflow average as the 'post-401k' income model."""
    df24 = pd.read_sql_table(
        "ONE_BIG_ACCOUNT_data_2024",
        create_engine("sqlite:///ONE_BIG_ACCOUNT_combined_data2024.db")
    )
    cf24 = compute_inflow_outflow(df24)
    q4mask = cf24["Date"].dt.month.isin([10, 11, 12])
    inc_q4_total = float(cf24.loc[q4mask, "inflow"].sum())
    return inc_q4_total / 3.0  # average monthly

def _ytd_totals_2025(cf):
    today = date.today()
    ytd_months = list(range(1, min(today.month, 10)))  # up to Sep in most years at this date
    mask = cf["Date"].dt.month.isin(ytd_months)
    inc = float(cf.loc[mask, "inflow"].sum())
    exp = float(cf.loc[mask, "outflow"].sum())
    return inc, exp, inc - exp, len(ytd_months)

def _forecast_full_year(cf, baseline_expense, q4_months_left=3):
    """
    Using baseline_expense as the monthly expense for remaining months,
    and 2024 Q4 average inflow as the income model for each remaining month.
    """
    q4_income_mo = _q4_income_baseline_from_2024()
    inc_q4 = q4_income_mo * q4_months_left
    exp_q4 = baseline_expense * q4_months_left

    inc_ytd, exp_ytd, net_ytd, ytd_m = _ytd_totals_2025(cf)
    return {
        "inc_total": inc_ytd + inc_q4,
        "exp_total": exp_ytd + exp_q4,
        "net_total": net_ytd + (inc_q4 - exp_q4),
        "q4_income_mo_model": q4_income_mo
    }

# ===== MERGED Emergency Fund + Baselines + Forecast + Audit =====

def show_emergency_fund_estimate_drilled_down_better(topn=12, columns=2, default_baseline="Outlier-Adjusted"):
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

    print("\n--- Forecast Comparison (2025 Full-Year) ---")
    print(f"(Assumes monthly income in remaining months = 2024 Q4 average inflow; months left = {months_left})")
    print("Baseline            |   2025 Income   |  2025 Expenses  |  2025 Net")
    print("--------------------|-----------------|------------------|----------------")
    # compute once to show the income model used
    q4_income_model = _q4_income_baseline_from_2024()
    for name, base in baselines.items():
        res = _forecast_full_year(cf, base, q4_months_left=months_left)
        print(f"{name:20} | ${res['inc_total']:>13,.2f} | ${res['exp_total']:>13,.2f} | ${res['net_total']:>12,.2f}")

    print(f"\nℹ️ Income model for remaining months (per month): ${q4_income_model:,.2f}  (from 2024 Q4 average)")

    # Big-picture audit: every month’s top categories
    print(f"\n=== Month-by-Month Category Audit (Top {topn}) ===")
    blocks = []
    for m in completed:
        pairs = _top_categories_for_month(cf, year, m, topn=topn)
        blocks.append(_format_block_for_month(year, m, pairs))
    _print_blocks_side_by_side(blocks, columns=columns, col_width=46)





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
    year = year or today.year
    if month is None:
        month = today.month - 1  # last completed month
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
    db_path = "ONE_BIG_ACCOUNT_combined_data2025.db"
    table_name = "NEW_ONE_BIG_ACCOUNT_data_2025"

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
        show_emergency_fund_estimate(df_current)

    def _run_emergency_estimate_drilldown():
        show_emergency_fund_estimate_drilled_down(topn=12, columns=2)

    def _run_emergency_estimate_outlier():
        show_emergency_fund_estimate_drilled_down_better(topn=12, columns=2)

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
    def category_spend_insights(min_months: int = 6, topn: int = 20):
        """Show top expense categories (YTD), avg per active month, and highest month.

        Filters to expense rows via compute_inflow_outflow so numbers match cash-flow.
        Only categories present in at least `min_months` months are listed.
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

        order = ytd.sort_values(ascending=False).head(int(topn)).index
        print("\nConsistent expense categories (ranked by YTD total):")
        print(f"{'Category':<24} | {'YTD Total':>12} | {'Avg/Active Mo':>13} | {'Highest Month (Amt)':>22} | {'Months':>6}")
        print("-" * 92)
        for cat in order:
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

    def _show_menu(menu_sections):
        print("\n======== FINANCE PROGRAM MENU ========")
        for section, options in menu_sections:
            print(f"\n{section}:")
            for key, label, _ in options:
                print(f"  {key:>5} - {label}")
        print("\n  0     - Exit")

    menu_sections = [
        ("Setup & Maintenance", [
            ("1", "Rebuild database from latest bank exports", create_data_base),
            ("2", "Re-categorize database with latest categories.csv", _recategorize_database),
            ("3", "Show uncategorized transactions (top 50)", _show_uncategorized_top50),
        ]),
        ("Reports & Lookups", [
            ("4", "Lookup transactions by month and category", lookup_by_month_and_category),
            ("5", "Display monthly and quarterly summary breakdown", display_monthly_and_quarterly_summary),
            ("6", "Show transactions marked 'LOOK INTO'", show_look_into_transactions),
            ("7", "Show transactions grouped by category", show_all_transactions_grouped_by_category),
            ("8", "Cash flow overview by month", cash_flow_by_month),
            ("8.1", "List income transactions for a month", list_income_transactions_for_month),
            ("8.2", "List expense transactions for a month (grouped)", list_expense_transactions_for_month_grouped),
            ("14", "Consistent expense categories (min 6 months)", category_spend_insights),
            ("14.1", "Monthly savings simulator (top 4 @ 15%)", monthly_savings_simulator_topn),
            ("9", "Emergency fund estimate (standard)", _run_emergency_estimate),
            ("9.5", "Emergency fund estimate drilldown (side-by-side)", _run_emergency_estimate_drilldown),
            ("9.8", "Emergency fund estimate drilldown with outlier trim", _run_emergency_estimate_outlier),
            ("10", "Forecast year-end net cash flow (2025 vs 2024)", forecast_year_end),
            ("11", "Compare monthly net cash flow: 2024 vs 2025", _run_cash_flow_comparison),
            ("12", "Review category spending with comparison", _review_category_spending),
            ("13", "Review transactions between custom dates", review_cc_charges_between_dates),
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

    while True:
        _show_menu(menu_sections)
        choice = input("\nSelect an option: ").strip()
        if choice == "0":
            print("Exiting...")
            break

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


