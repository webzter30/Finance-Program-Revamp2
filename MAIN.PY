


# MAIN.PY CREATED 10/11/2024

# imports
import csv
import gspread
import time
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pylab as plt
import pickle
from sqlalchemy import create_engine  


# imports
import csv
import gspread
import time
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pylab as plt
import pickle
from sqlalchemy import create_engine  


from New_CITY_transactoins10_10_24 import *

import openpyxl
from openpyxl import Workbook
import xlsxwriter
import openpyxl 
from datetime import datetime
import seaborn as sns


# ignore warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)



# Set max_columns to None to allow Pandas to wrap the output to the next line
pd.set_option('display.max_columns', None)


# SET YEAR
YEAR ='FULL_YEAR_25'

if YEAR =='FULL_YEAR_24':
     
        # connect to the database
        engine = create_engine('sqlite:///ONE_BIG_ACCOUNT_combined_data2024.db').connect() 
        # READ THE TABLE OF THE DATABASE INTO PANDAS!!!!!!!!!!!!!!!!!!!
        ONE_BIG_ACCOUNT_DATABASE = pd.read_sql_table('ONE_BIG_ACCOUNT_data_2024', engine)
        #now put it into the variable Combined_account_data_2023

        print("__________________________@@@!!!__________________________________")
        print(" CONNECTED TO ONE_BIG_ACCOUNT_combined_data2024.db")
        print("__________________________@@@!!!__________________________________")

if YEAR =='FULL_YEAR_25':
     
        # connect to the database
        engine = create_engine('sqlite:///ONE_BIG_ACCOUNT_combined_data2025.db').connect() 
        # READ THE TABLE OF THE DATABASE INTO PANDAS!!!!!!!!!!!!!!!!!!!
        ONE_BIG_ACCOUNT_DATABASE = pd.read_sql_table('ONE_BIG_ACCOUNT_data_2025', engine)
        #now put it into the variable Combined_account_data_2023

        print("__________________________@@@!!!__________________________________")
        print(" CONNECTED TO ONE_BIG_ACCOUNT_combined_data2025.db")
        print("__________________________@@@!!!__________________________________")



#df2 = pd.concat([df2,FORD_ADVANTAGE24,TRUST,KP_403b], axis=0)
df2 = pd.concat([ONE_BIG_ACCOUNT_DATABASE], axis=0)

# GETTING DUPLICATES OF USAA CC PAYMENT, COMING FROM THE USAA CC ACCOUNT AND THE JEFF CHECKING ACCOUNT SO DO THIS.
# Filter and drop rows where 'Category' is 'USAA CC PAYMENT' and 'Account' is 'USAA CC FOR THE YEAR'
df2 = df2[~((df2['Category'] == 'USAA CC PAYMENT') & (df2['ACCOUNT'] == 'USAA CC FOR YEAR'))]

# Optional: Reset the index after dropping the rows (if needed)
df2.reset_index(drop=True, inplace=True)

#print(df2.head(10))



# NOTE LETS GET TOTAL SS BEFORE I RECATEGORIZE IT INTO INCOME FOR THE PIVOT TABLE. 
#filter_transfer_df = df3[(df3['Category'] == 'TRANSFER') & (df3['Month'] == 'September')]
#total_cost_of_living = pivot_df['Cost of Living'].sum().round(0)
SS_df2 = df2[(df2['Category'] == 'S_S')]
Security_df2 = df2[(df2['Category'] == 'Security')]
sumdf = SS_df2['Amount'].sum().round()
Securdf = Security_df2['Amount'].sum().round()
Paycheckdf = df2[(df2['Category'] == 'PAYCHECK')]
Paycheck_total = Paycheckdf['Amount'].sum().round()
added_S_S = sumdf + Securdf

print('######### INCOME ### AS OF November ########')
print(f'Total S_S    : {added_S_S}')
print(f'Total Paychecks : {Paycheck_total}')
print("-------------------------------------")

#print(F'Total S_S so far is {Total_S_S_df}')

# NOTE ANYHTING YOU WANT TO SEE IN THE PIVOT TABLE YOU PUT HERE AND RECATIGORISE HERE. 
# IT WILL MAKE A COLUM IN THE PIVOT TABLE WITH THE NAME. 
# !!! IT WILL BE EXCLUDED FROM THE 'TRANSAC FOR M' COLUMN SO YOU HAVE TO MANUALLY
# SUBTRACT IT FROM THE TOTAL TO GET THE CORRECT DIFFERENCE IN THE CALCULATION 
# OF MONTHLY COST OF LIVING. 

category_mapping = {
        #'Utilities': 'Monthly base',
        #'Groceries': 'Monthly base',
        'Mortgage': 'Mortgage',
        #'USAA_Insurance': 'Insurance',
        'PAYCHECK': 'Income',
        'Security': 'Income',
        'S_S' : 'Income',
        'Grocery' : 'Grocery',
        'NANNY PAY' : 'NANNY PAY',
        'AMAZON' :'AMAZON',
        'TAXES': 'TAXES'
    }

    # Create a new DataFrame df2 to store the mapped data
df3 = pd.DataFrame()
df3['Category_group'] = df2['Category'].map(category_mapping).fillna('Other')




    ### note whatever you put in here is then excluded from being nammed 'Transac for M'
    
exclude_categories = ['CITY CC PAYMENT', 'USAA CC PAYMENT', 'VANGUARD INVESTMENT', 'TRANSFER', 'Security', 'PAYCHECK', 'ACCOUNT INTEREST']

    # Only overwrite the values in Category_group that are NOT already mapped (i.e., still 'Other')
df3['Category_group'] = np.where(df3['Category_group'] == 'Other', np.where(df2['Category'].isin(exclude_categories), df2['Category'], 'Transact for M'), df3['Category_group'])

#print(df3)


  # Add the remaining necessary columns from the original DataFrame
df3['Amount'] = df2['Amount']
df3['Month'] = df2['Month']
df3['ACCOUNT'] = df2['ACCOUNT']
df3['Transact'] = df2['Transact']
df3['Category'] = df2['Category']
df3['Date'] = df2['Date']

# Step 4: Define the correct order of months
month_order = ['January', 'February', 'March', 'April',
                    'May', 'June', 'July', 'August', 'September', 
                    'October', 'November', 'December']

    # Step 5: Convert 'Month' column to a categorical type with the defined order
df3['Month'] = pd.Categorical(df2['Month'], categories=month_order, ordered=True)





# and then sums it all up. only for subscriptions. 
#subx = filter.groupby(['Category','Transact']).aggregate({'Category':['count'],'Amount':['sum']}, index=False)
    


    # Step 6: Create a pivot table with 'Month' as rows, 'Category_group' as columns, and sum of 'Amount'
pivot_df = df3.pivot_table(index='Month', columns='Category_group', values='Amount', aggfunc='sum', fill_value=0)




# Create a new column called 'Difference' which is 'Transact for M' - 'Income'
# Assuming the pivot table has single-level columns
#pivot_df['Difference'] =  pivot_df['Income'] - pivot_df['Transact for M'] - pivot_df['Mortgage'] - pivot_df['Grocery']

# this makes everything + so they can be subtracted
pivot_df['Difference'] = (
    pivot_df['Income'] 
    - pivot_df['Transact for M'].abs() 
    - pivot_df['Mortgage'].abs() 
    - pivot_df['Grocery'].abs()
    - pivot_df['TAXES'].abs()
    - pivot_df['AMAZON'].abs()
    - pivot_df['NANNY PAY'].abs()
)

# Assuming 'pivot_df' is your pivot table with 'Income' and 'Difference' columns
# Calculate the monthly cost of living
pivot_df['Cost of Living'] = pivot_df['Income'] - pivot_df['Difference']

# Display the updated pivot table with the new 'Cost of Living' column
#print(pivot_df)

print('###########################cost of living without medical #################################################')

# Calculate total sum and mean for 'Cost of Living' as of September haven't done Octerber yet. 
# so multiple by 9 as of now to get estimates for total year in some years. 
total_cost_of_living = pivot_df['Cost of Living'].sum().round(0)
mean_cost_of_living = pivot_df['Cost of Living'].mean().round(0)
total_taxes = pivot_df['TAXES'].sum().round(0)
total_deference = pivot_df['Difference'].sum().round(0)
total_income = pivot_df['Income'].sum().round(0)
total_income_mean = pivot_df['Income'].mean().round(0)
total_nanny = pivot_df['NANNY PAY'].sum().round(0)

# estimate emergency fund
# estimated by using numbers through september. have not got payed for October yet. 
Months_so_far = 9
Paycheck_total_estimate = (Paycheck_total/Months_so_far).round()
Paycheck_total_estimate = Paycheck_total_estimate * 12
print(f"Total Cost of Living for the year: {total_cost_of_living}")
print(f"Mean Monthly Cost of Living: {mean_cost_of_living}")
print('################################################################################')
print(f"Total EMERGENCY FUND FOR JEFF PAY FOR A YEAR: {Paycheck_total_estimate} ")
print(f"TOTAL EMERGECY FOR COST OF LIVING FOR YEAR  : {mean_cost_of_living * 12 }")
print('################################################################################')
print(f"Total income this year {total_income}")
print('################################################################################')
print(f"Total excess {total_deference}")
print('################################################################################')
print(f"Total nanny {total_nanny}")
print('##################################################################################')


# Print the updated pivot table
#print(pivot_df)

# Step 11: Calculate the sum of each column and add as a new row labeled 'Total'
pivot_df.loc['Total'] = pivot_df.sum().round(0)
    
    # Step 12: Calculate the mean of each column and add as a new row labeled 'Mean'
    # this only gives for the monthly total and doesn't include the total row. 
    # and not including the months with total of 0, for the months we have not had yet. 
    # pivot_df.loc['Mean'] = pivot_df.loc[pivot_df.index != 'Total'].mean().round(0).astype(int)
    # pivot_df.loc['Mean'] = pivot_df[(pivot_df != 0).any(axis=1)].mean().round(0).astype(int)
pivot_df.loc['Mean'] = pivot_df[(pivot_df.index != 'Total') & (pivot_df != 0).any(axis=1)].mean().round(0).astype(int)


#print(df2)

# 10/11/24
# NOTE Next step is to list all transactions under transact for M - to double check what is the discriptions under each transaction and there account. 

# filter out the transactions for Month colum to see what they are. 
 
#filter_df = df3[(df3['Category_group'] == 'Transact for M') & (df3['Month'] == 'January')]



#filter_df = df3[(df3['Month'] == 'January')]
#print(filter_df.to_string())
'''
aggregated = filter_df.groupby('Category', sort=True).agg({
    'Amount': 'sum',
    'Transact': lambda x: list(x)
}).reset_index()

print(aggregated)

'''

'''
grouped = filter_df.groupby('Category', sort=True)['Transact'].apply(list).reset_index()

# Print out each category title with its transaction descriptions:
for idx, row in grouped.iterrows():
    print(f"Category: {row['Category']}")
    for desc in row['Transact']:
        print("  -", desc)
    print()  # Blank line between groups

'''
'''
# Group by 'Category' and create a list of (Transact, Amount) tuples for each group
#------------------------------------------------------------->>>>
filter_df = df3[(df3['Month'] == 'December')]

grouped = filter_df.groupby('Category', sort=True).apply(
    lambda x: list(zip(x['Transact'], x['Amount']))
).reset_index(name='Transactions')

# Print out each category title with its transaction description and amount:
for idx, row in grouped.iterrows():
    print(f"Category: {row['Category']}")
    for transact, amount in row['Transactions']:
        print(f"  - {transact}: {amount}")
    print()  # Blank line between groups
####--------------------------------------------->>>>>
'''

##------------------------------------------------>>>>
'''
# THIS IS SEARCHED BY THE MONTH !!!!!
# Group by 'Category' and for each group, create a dictionary that includes:
# - a list of (Transact, Amount) tuples
# - the total amount for that category.

filter_df = df3[(df3['Month'] == 'March')]

grouped = filter_df.groupby('Category', sort=True).apply(
    lambda x: {
         "Transactions": list(zip(x['Transact'], x['Amount'])),
         "Total": x['Amount'].sum()
    }
).reset_index(name='Details')

# Print out each category with its transactions and total:
for idx, row in grouped.iterrows():
    print(f"Category: {row['Category']}")
    details = row['Details']
    for transact, amount in details["Transactions"]:
        print(f"  - {transact}: {amount}")
    print(f"Total: {details['Total']}\n")
'''

# ignore warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

##----------------------------------------------->>>>>>>>>>>


## this just prints what columns are available. 

#print([col for col in df3.columns])

## THIS SORTS OUT EACH MONTH , ITERATES THROUG THE YEAR SO SHOWS EACH MONTH !!!!!!!!!!!

# Get unique months (optionally sorted by a specific order)
months = df3['Month'].unique()

for month in months:
    print(f"\n======================")
    print(f"==== {month.upper()} ====")
    print(f"======================\n")

    month_df = df3[df3['Month'] == month]

    # 1. Full transaction list for the month
    print("All Transactions:")
    for idx, row in month_df.iterrows():
        print(f"- {row['Date']} | {row['Transact']} | {row['Category']} | ${row['Amount']:.2f}")
    
    print("\nGrouped by Category:\n")

    # 2. Grouped summary by category
    grouped = month_df.groupby('Category', sort=True).apply(
        lambda x: {
            "Transactions": list(zip(x['Transact'], x['Amount'], x['Date'])),
            "Total": x['Amount'].sum(),
            "TransactionCount": len(x)
        }
    ).reset_index(name='Details')

    for idx, row in grouped.iterrows():
        print(f"Category: {row['Category']}")
        details = row['Details']
        for transact, amount, date in details["Transactions"]:
            print(f"  - {date}: {transact} — ${amount:.2f}")
        print(f"Total: ${details['Total']:.2f}")
        print(f"Number of Transactions: {details['TransactionCount']}\n")

## ----------------------------------------------------------------------------->>>>>


# Optional: standardize column names

#clean summary table under each month that lists:

#Category

#Number of Transactions

#Sum of Transactions (Total)

df3.columns = df3.columns.str.strip()  # remove leading/trailing spaces

# Get sorted list of unique months (optionally define your own order)
months = df3['Month'].unique()

for month in months:
    print(f"\n======================")
    print(f"==== {month.upper()} ====")
    print(f"======================\n")

    month_df = df3[df3['Month'] == month]

    # === 1. All Transactions for the Month ===
    print("All Transactions:")
    for idx, row in month_df.iterrows():
        print(f"- {row['Date']} | {row['Transact']} | {row['Category']} | ${row['Amount']:.2f}")

    # === 2. Grouped Summary by Category ===
    print("\nSummary by Category:\n")
    
    summary = (
        month_df
        .groupby('Category')
        .agg(
            Number_of_Transactions=('Amount', 'count'),
            Total_Amount=('Amount', 'sum')
        )
        .reset_index()
        .sort_values('Category')
    )

    print(f"{'Category':<20} {'# Transactions':<16} {'Total ($)':>10}")
    print("-" * 50)
    for _, row in summary.iterrows():
        print(f"{row['Category']:<20} {row['Number_of_Transactions']:<16} ${row['Total_Amount']:>10.2f}")


#------------------------------------------------------....>>>>>>>
# Full Updated Code with Exclusion + Summary + Top Transaction 4/8/25 - output by quater



import pandas as pd

# 1. Clean column names and convert Amount column
df3.columns = df3.columns.str.strip()
df3['Amount'] = pd.to_numeric(df3['Amount'], errors='coerce')

# 2. Categories to exclude
exclude_categories = ['CITY CC PAYMENT', 'USAA CC PAYMENT', 'Mortgage']
filtered_df = df3[~df3['Category'].isin(exclude_categories)].copy()

# 3. Month order (for consistent display)
month_order = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
filtered_df['Month'] = pd.Categorical(filtered_df['Month'], categories=month_order, ordered=True)

# 4. Create pivot table with totals per category per month
pivot = pd.pivot_table(
    filtered_df,
    values='Amount',
    index='Month',
    columns='Category',
    aggfunc='sum',
    fill_value=0,
    observed=False  # Silences future warning
).round(2)

# 5. Add total and mean rows
pivot.loc['Total'] = pivot.sum(numeric_only=True)
pivot.loc['Mean'] = pivot.mean(numeric_only=True)

# 6. Define quarters
quarters = {
    'Q1': ['January', 'February', 'March'],
    'Q2': ['April', 'May', 'June'],
    'Q3': ['July', 'August', 'September'],
    'Q4': ['October', 'November', 'December']
}

# 7. Display each quarter side-by-side, transposed for readability
for quarter, months in quarters.items():
    print(f"\n===== {quarter} Summary =====\n")
    quarter_df = pivot.loc[months + ['Total', 'Mean']]

    # Filter out empty columns for this quarter
    relevant_cols = quarter_df.loc[months].any(axis=0)
    display_df = quarter_df.loc[:, relevant_cols]

    with pd.option_context('display.max_columns', None, 'display.width', None):
        print(display_df.T.round(2))  # Transposed for vertical scrolling





#filter_df = df3[(df3['Category'] == 'Grocery') & (df3['Month'] == 'September')]
filter_transfer_df = df3[(df3['Category'] == 'TRANSFER') & (df3['Month'] == 'September')]

#filter_nanny_pay_df = df3[(df3['Category'] == 'NANNY PAY') & (df3['Month'] == 'September')]
filter_nanny_pay_df = df3[(df3['Category'] == 'NANNY PAY')] #& (df3['Month'] == 'September')]
  
#sumdf = pd.DataFrame()
#suddf = filter_nanny_pay_df['Amount']
#suddf.loc['Total'] = suddf.sum().round(0)
#print(suddf.to_string())


#sum_nanny_df =filter_nanny_pay_df.sum()
#print (f'sum of nanny_pay = {sum_nanny_df} ')

#filter_nanny_pay_df = df3[(df3['ACCOUNT'] == 'NANNY_ACCOUNT_Year')] # & (df3['Month'] == 'September')]
#filter_nanny_pay_df = df3[(df3['Transact'] == '            Zelle')] # & (df3['Month'] == 'September')]

# Adjust Pandas options to display all rows and columns
    # make it so it doesn't print off the terminal
#pd.set_option('display.max_columns', 5)  # Adjust the number of columns to fit your terminal width
#pd.set_option('display.width', 100)       # Set the output width for better formatting

# Set max_columns to None to allow Pandas to wrap the output to the next line
#pd.set_option('display.max_columns', None)

# Set display width to a large value to avoid wrapping (e.g., 1000 characters)
#pd.set_option('display.width', 1000)

#pd.set_option('display.max_columns', None)  # Show all columns
#pd.set_option('display.width', 1000)        # Set display width to avoid cutting off
#pd.set_option('display.max_colwidth', 50)   # Set maximum column width for readability

#filter_income = df3[(df3['Category_group'] == 'Income') & (df3['Month'] == 'October')]
#print('filter for INCOME as of 11/2024')
#print(filter_income.to_string())


#filter_month = df3[df3['Month'] == 'November']
#print('filter for Month = November ')
#print(filter_month.to_string())

############!!! main one to print start here ################ 1_30_25

#NOTE  my pivot TABLE!!!!!!!!!!!!!!!!!



#print(pivot_df)


#####################################################################


#pivot2_df['OTHER'] = filter_df
#print(filter_transfer_df.to_string())

#print(filter_nanny_pay_df.to_string())
#print(filter_df.to_string())
# NOTE Need to fix marlina nanNy pay - it is tx it as a transfer 
 # should be done - reordered the library 11/14/24

# NOTE DOUBLE CHECK CATEGORIES. 
  # can do this now by filtering above. 11/14/24

# NOTE CHECK THE LOOK UP CATEGORY ???

# NOTE NOW MAKE A MODULE FOR THE INVESTMENT ACCOUNTS/ THIS SOULD JUST BE COPE 
# AND PASTE 10/14/24

#print(ONE_BIG_ACCOUNT_DATABASE.to_string())


