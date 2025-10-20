import pandas as pd

# Define file paths
file_statement = r"C:\Users\webzt\Dropbox\PC\Desktop\REVAMP2 python fincance 10_11_23\Costco_Statement_closed_Jun_09_2025.CSV"
file_ytd = r"C:\Users\webzt\Dropbox\PC\Desktop\REVAMP2 python fincance 10_11_23\City_Visa_Year to date_download_7_1_2025.CSV"

# Load CSVs
df_stmt = pd.read_csv(file_statement)
df_ytd = pd.read_csv(file_ytd)

# Normalize columns
df_stmt.columns = [col.strip().lower() for col in df_stmt.columns]
df_ytd.columns = [col.strip().lower() for col in df_ytd.columns]

# Parse dates and debit fields
df_stmt["date"] = pd.to_datetime(df_stmt["date"], errors="coerce")
df_ytd["date"] = pd.to_datetime(df_ytd["date"], errors="coerce")
df_stmt["debit"] = pd.to_numeric(df_stmt["debit"], errors="coerce")
df_ytd["debit"] = pd.to_numeric(df_ytd["debit"], errors="coerce")

# Filter for custom billing range: May 8 – June 7, 2025
start_date = pd.Timestamp("2025-05-07")
end_date = pd.Timestamp("2025-06-07")

f_stmt = df_stmt[(df_stmt["date"] >= start_date) & (df_stmt["date"] <= end_date)].dropna(subset=["debit"])
f_ytd = df_ytd[(df_ytd["date"] >= start_date) & (df_ytd["date"] <= end_date)].dropna(subset=["debit"])

# Sum totals
sum_stmt = f_stmt["debit"].sum()
sum_ytd = f_ytd["debit"].sum()

# Print results
print("📅 Billing Cycle: May 8 – June 7, 2025\n")
print(f"🧾 Costco Statement CSV Total: ${sum_stmt:,.2f}")
print(f"📄 YTD Download CSV Total:     ${sum_ytd:,.2f}")
print(f"🔎 Difference:                 ${abs(sum_stmt - sum_ytd):,.2f}")
