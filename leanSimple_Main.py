# ==============================
# Finance Program Refactor — 9/15/25
# ==============================

import pandas as pd
from sqlalchemy import create_engine
import re
from datetime import date
from colorama import Fore, Style, init
init(autoreset=True)

# -------------------------------
#  CONFIG
# -------------------------------
YEAR = "2025"
DB_FILE = f"ONE_BIG_ACCOUNT_combined_data{YEAR}.db"
TABLE_NAME = f"NEW_ONE_BIG_ACCOUNT_data_{YEAR}"
CATEGORY_FILE = "categories.csv"

# -------------------------------
#  CSV INGESTION
# -------------------------------
account_csv_configs = {
    "JEFF_CHECKING_USAA": {
        "filepath": f"JEFF_CHECKING_USAA_{YEAR}.csv",
        "columns": {"Amount": "Amount", "Description": "Description", "Date": "Date"},
        "account_name": "JEFF CHECKING"
    },
    "City_Visa": {
        "filepath": f"City_Visa_Year_to_date_download_9_15_2025.CSV",
        "columns": {"Amount": "Debit", "Description": "Description", "Date": "Date"},
        "account_name": "COSTCO CITY BANK",
        "strip_symbols_from_amount": True
    }
    # Add other accounts here
}

def load_category_map(filepath):
    df = pd.read_csv(filepath)
    return dict(zip(df['keyword'].str.lower(), df['category']))

def categorize_transaction(description, category_map):
    description = str(description).lower()
    for keyword, category in category_map.items():
        if keyword in description:
            return category
    return "Uncategorized"

def apply_categorization(df):
    category_mapping = load_category_map(CATEGORY_FILE)
    df["Category"] = df["Description"].apply(lambda d: categorize_transaction(d, category_mapping))
    return df

def load_account_data(config):
    df = pd.read_csv(config["filepath"])
    df = df.rename(columns={v: k for k, v in config["columns"].items()})

    # Normalize Amount
    if config.get("strip_symbols_from_amount", False):
        df["Amount"] = pd.to_numeric(df["Amount"].replace({'\\$': '', ',': ''}, regex=True), errors="coerce")
    else:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")

    # Normalize Date
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Month"] = df["Date"].dt.month_name()

    # Ensure Transact + Description exist
    if "Transact" not in df.columns:
        if "Description" in df.columns:
            df["Transact"] = df["Description"]
        else:
            df["Transact"] = ""
    if "Description" not in df.columns:
        df["Description"] = df["Transact"]

    # Apply categorization
    df = apply_categorization(df)

    # Ensure ACCOUNT exists
    df["ACCOUNT"] = config["account_name"]

    # Enforce schema order
    return df[["Date","Month","Transact","Description","Amount","Category","ACCOUNT"]]

def create_data_base():
    engine = create_engine(f"sqlite:///{DB_FILE}")
    all_dataframes = [load_account_data(cfg) for cfg in account_csv_configs.values()]
    ONE_BIG_ACCOUNT = pd.concat(all_dataframes, ignore_index=True)
    ONE_BIG_ACCOUNT.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
    print("✅ Database rebuilt successfully!")
    show_uncategorized(ONE_BIG_ACCOUNT)

def recategorize_full_table(db_file, table_name):
    engine = create_engine(f"sqlite:///{db_file}")
    df = pd.read_sql_table(table_name, engine)
    df = apply_categorization(df)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    print("✅ Re-categorized table with latest categories.csv.")

def show_uncategorized(df, n=25):
    uncategorized = df[df["Category"]=="Uncategorized"]
    print(f"\n⚠️ Found {len(uncategorized)} uncategorized transactions:")
    print(uncategorized[["Date","Transact","Amount"]].head(n))

# -------------------------------
#  CORE LOGIC
# -------------------------------
CF_INCOME_CATS = {
    "PAYCHECK","S_S","SS","SOCIAL SECURITY","SSA","SSA INCOME",
    "INCOME ? KP","WORK","SECURITY"
}
CF_EXCLUDE_CATS = {
    "CITY CC PAYMENT","USAA CC PAYMENT","CC PAYMENT",
    "TRANSFER","COSTCO REBATE","ACCOUNT INTEREST",
    "VANGUARD INVESTMENT","INVESTMENT"
}
CF_SS_REGEX = re.compile(
    r"(ssa\s*treas|treas\s*310\s*ssa|soc(?:ial)?\s*sec(?:urity)?|ssa\s*deposit|ss\s*income)",
    flags=re.IGNORECASE
)

def load_main_df():
    engine = create_engine(f"sqlite:///{DB_FILE}")
    return pd.read_sql_table(TABLE_NAME, engine)

def compute_inflow_outflow(df):
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce")
    out["Amount"] = pd.to_numeric(out["Amount"], errors="coerce")
    out = out[out["Date"].notna() & out["Amount"].notna()].copy()

    cat_raw = out["Category"].astype(str)
    cat_up = cat_raw.str.upper().str.strip()
    text_blob = (
        out["Transact"].astype(str) + " " +
        out["Description"].astype(str) + " " +
        out["ACCOUNT"].astype(str) + " " +
        cat_raw
    ).str.lower()
    looks_ss = text_blob.str.contains(CF_SS_REGEX, na=False)

    is_income   = cat_up.isin(CF_INCOME_CATS) | looks_ss
    is_excluded = cat_up.isin(CF_EXCLUDE_CATS)
    is_expense  = (~is_income & ~is_excluded) | (cat_up=="MORTGAGE")

    out["inflow"] = 0.0
    out["outflow"] = 0.0
    out.loc[is_income,"inflow"] = out.loc[is_income,"Amount"].abs()
    out.loc[is_expense,"outflow"] = out.loc[is_expense,"Amount"].abs()
    out["is_income"] = is_income
    out["is_expense"] = is_expense
    return out

# -------------------------------
#  REPORTS
# -------------------------------
def category_picker(df, year, month):
    mask = (df["Date"].dt.year==year) & (df["Date"].dt.month_name()==month)
    dsub = df.loc[mask]
    cats = sorted(dsub["Category"].dropna().unique())
    while True:
        print(f"\n📂 Categories for {month} {year}")
        for i, cat in enumerate(cats, 1):
            print(f"{i}. {cat}")
        print("0. Back")
        choice = input("\nSelect category number: ").strip()
        if choice=="0" or choice=="": return
        try:
            cat = cats[int(choice)-1]
        except: 
            print("❌ Invalid choice."); continue
        results = dsub[dsub["Category"]==cat]
        print(f"\n🔍 {len(results)} transactions in {cat}:")
        print(results[["Date","Transact","Amount","Category","ACCOUNT"]]
              .sort_values("Date")
              .to_string(index=False))
        input("\nPress Enter to return...")

def cash_flow_by_month():
    df = load_main_df()
    cf = compute_inflow_outflow(df)
    inc_by_m = cf.groupby("Month")["inflow"].sum()
    exp_by_m = cf.groupby("Month")["outflow"].sum()

    months = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]
    months = [m for m in months if m in inc_by_m.index or m in exp_by_m.index]

    print("\nMonth       |     Income     |    Expenses    |       Net       | Status")
    print("-----------------------------------------------------------------------")
    ytd = 0.0
    for m in months:
        inc, exp = float(inc_by_m.get(m,0)), float(exp_by_m.get(m,0))
        net = inc-exp; ytd += net
        status = f"{Fore.GREEN}Surplus" if net>=0 else f"{Fore.RED}Deficit"
        print(f"{m:<11} | ${inc:>10,.2f} | ${exp:>10,.2f} | ${net:>11,.2f} | {status}{Style.RESET_ALL}")
    print(f"\n📊 YTD Net Cash Flow: ${ytd:,.2f}")

    if input("\n🔎 Drill into a month? (y/n): ").lower()=="y":
        m = input("Enter month name (e.g., April): ").capitalize()
        if m in months: category_picker(df, date.today().year, m)

def compare_cash_flow_2024_vs_2025():
    df24 = pd.read_sql_table("ONE_BIG_ACCOUNT_data_2024", create_engine("sqlite:///ONE_BIG_ACCOUNT_combined_data2024.db"))
    df25 = load_main_df()
    cf24, cf25 = compute_inflow_outflow(df24), compute_inflow_outflow(df25)
    net24 = cf24.groupby("Month")["inflow"].sum() - cf24.groupby("Month")["outflow"].sum()
    net25 = cf25.groupby("Month")["inflow"].sum() - cf25.groupby("Month")["outflow"].sum()

    months = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]

    print("\n📊 NET CASH FLOW (2024 vs 2025)")
    print("Month       | Net 2024     | Net 2025     | Difference     | Status")
    print("--------------------------------------------------------------------")
    for m in months:
        a, b = float(net24.get(m,0)), float(net25.get(m,0))
        diff = b-a
        status = (Fore.GREEN+"⬆️ Higher" if diff>0 else
                  Fore.RED+"⬇️ Lower" if diff<0 else
                  Fore.YELLOW+"➖ Equal")+Style.RESET_ALL
        print(f"{m:<11} ${a:>10,.2f} | ${b:>10,.2f} | ${diff:>10,.2f}   {status}")

def show_emergency_fund_estimate():
    df = load_main_df()
    cf = compute_inflow_outflow(df)
    today = date.today()
    months = range(1,today.month)
    per = []
    for m in months:
        total = cf.loc[(cf["Date"].dt.year==today.year)&(cf["Date"].dt.month==m),"outflow"].sum()
        per.append(total)
    if not per:
        print("\nNo completed months yet."); return
    avg = sum(per)/len(per)
    print("\n=== EMERGENCY FUND ESTIMATE ===")
    for m,t in zip(months,per): print(f"  {today.year}-{m:02d}: ${t:,.2f}")
    print(f"\nAverage monthly expenses: ${avg:,.2f}")
    for n in (6,9,12): print(f"{n}-month fund: ${avg*n:,.2f}")

# -------------------------------
#  MENU
# -------------------------------
def main_menu():
    while True:
        print("\n======== FINANCE PROGRAM MENU ========")
        print("1. Rebuild database from latest CSVs")
        print("2. Re-categorize existing database with categories.csv")
        print("3. Show uncategorized transactions")
        print("4. Cash Flow by Month")
        print("5. Compare Cash Flow 2024 vs 2025")
        print("6. Emergency Fund Estimate")
        print("0. Exit")
        choice = input("\nSelect option: ").strip()
        if choice=="1": create_data_base()
        elif choice=="2": recategorize_full_table(DB_FILE,TABLE_NAME)
        elif choice=="3": show_uncategorized(load_main_df())
        elif choice=="4": cash_flow_by_month()
        elif choice=="5": compare_cash_flow_2024_vs_2025()
        elif choice=="6": show_emergency_fund_estimate()
        elif choice=="0": break
        else: print("Invalid choice.")

if __name__=="__main__":
    main_menu()
