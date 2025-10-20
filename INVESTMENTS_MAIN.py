
################################################
# NOTE NEW NEW NEW 10/15/24 coppied some from the old program 
##################################################




# 10-15-24
# advise from AI 

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


#from Finance_python_program_main6_24_23 import *
#from FINANCE_PROGRAM_MODULE_6_24_23 import *

# from 
#from TALLY_FUNCTIONS_6_26_23 import *

import openpyxl
from openpyxl import Workbook
import xlsxwriter
import openpyxl 
from datetime import datetime
import seaborn as sns


# analyzing Ford 
# IMPORT GLOB TO PUT CONCAT ALL THE CSV FILES IN THE FOLDER
import glob
import os
# Define the folder path
folder_path = r'C:\Users\webzt\Dropbox\PC\Desktop\REVAMP2 python fincance 10_11_23\FORD_2024'

# Use glob to get all .csv files in the folder
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

# Initialize an empty list to hold DataFrames
df_list = []

# Loop through the list of CSV files and read each one
for file in csv_files:
    df = pd.read_csv(file)  # Read the CSV file
    df_list.append(df)      # Append the DataFrame to the list

# Concatenate all the DataFrames into one
FORD24 = pd.concat(df_list, ignore_index=True)




# Define the folder path
folder_path23 = r'C:\Users\webzt\Dropbox\PC\Desktop\REVAMP2 python fincance 10_11_23\FORD_2023'

# Use glob to get all .csv files in the folder
csv_files23 = glob.glob(os.path.join(folder_path23, "*.csv"))

# Initialize an empty list to hold DataFrames
df_list23 = []

# Loop through the list of CSV files and read each one
for file in csv_files23:
    df23 = pd.read_csv(file)  # Read the CSV file
    df_list23.append(df23)      # Append the DataFrame to the list

# Concatenate all the DataFrames into one
FORD23 = pd.concat(df_list23, ignore_index=True)

# MADE THIS SIMPLER 10_15_24

#FORD23 = pd.concat(
 #   map(pd.read_csv, ['FORD_JAN_23.csv','FORD_OCT_23.csv',
 #                     'FORD_NOV_23.csv','FORD_DEC_23.csv',
 #                     'FORD_SEPT_23.csv','FORD_JULY_23.csv',
 #                     'FORD_AUGUST_23.csv','FORD_FEB_23.csv',
  #                    'FORD_MARCH_23.csv','FORD_APRIL_23.csv','FORD_MAY_23.csv',
  #                    'FORD_JUNE_23.csv',]),ignore_index=True)     

#FORD24 = pd.concat(
 #   map(pd.read_csv, ['FORD_JAN_24.csv','FORD_FEB_24.csv',
 #                     'FORD_MARCH_24.csv','FORD_APRIL_24.csv',
 #                     'FORD_MAY_24.csv','FORD_JUNE_24.csv','FORD_JULY_24.csv','FORD_AUGUST_24.csv']),ignore_index=True)


FORD_ADVANTAGE23 = pd.DataFrame()
FORD_ADVANTAGE24 = pd.DataFrame()

# FORD ACCOUNT DATA FRAME PLEASE
FORD_ADVANTAGE23['Transact'] = FORD23['<Description>']
FORD_ADVANTAGE23['Amount'] = FORD23['<Deposit Amount>']
FORD_ADVANTAGE23['Date'] = pd.to_datetime(FORD23['<Date>'])
FORD_ADVANTAGE23['Month'] = pd.DatetimeIndex(FORD_ADVANTAGE23['Date']).month_name()
#set the index to DATE. Try doing this at the beginning
FORD_ADVANTAGE23 = FORD_ADVANTAGE23.set_index('Date', drop=False)
#print(FORD_ADVANTAGE)

# FORD ACCOUNT DATA FRAME PLEASE 

FORD_ADVANTAGE24['Transact'] = FORD24['<Description>']
FORD_ADVANTAGE24['Amount'] = FORD24['<Deposit Amount>']
FORD_ADVANTAGE24['WITHDRAW'] = FORD24['<Withdrawal Amount>']
#FORD_ADVANTAGE24['Amount'] = FORD24['<Withdrawal Amount>']
FORD_ADVANTAGE24['Date'] = pd.to_datetime(FORD24['<Date>'])
FORD_ADVANTAGE24['ACCOUNT'] = 'FORD ACCOUNT'
FORD_ADVANTAGE24['Month'] = pd.DatetimeIndex(FORD_ADVANTAGE24['Date']).month_name()
#set the index to DATE. Try doing this at the beginning

#print(FORD_ADVANTAGE)
#print(FORD_ADVANTAGE24.to_string())

# TRUST

TRUST = pd.DataFrame()

#df3 = pd.read_csv(f"TRUST_FULL_YEAR_2024_VANGUARDFORMAT.csv", error_bad_lines=False)
df3 = pd.read_csv("TRUST_FULL_YEAR_2024_VANGUARDFORMAT.csv", on_bad_lines='skip')

#print(df3.to_string())


df3['Trade Date'] = pd.to_datetime(df3['Trade Date'], errors='coerce')

TRUST['TICKER'] = df3['Investment Name']
TRUST['Transact'] = df3['Transaction Description']
TRUST['TRADE DATE'] = pd.to_datetime(df3['Trade Date'])
TRUST['TRADE DATE'] = df3['Trade Date']
TRUST['Month'] = pd.DatetimeIndex(TRUST['TRADE DATE']).month_name()
TRUST['Amount'] = df3['Net Amount'] 
TRUST['ACCOUNT'] = 'TRUST'

# DROP THE SOME SELECT  COLUMN
#TRUST.drop(['TRADE DATE'],axis=1,inplace=True)

#print('__________TRUST_FULL_YEAR_2024_VANGUARDFORMAT___AS OF 6/18/24________')
#print(TRUST.to_string())


# sum it all up for plan contributions. 
print('################ TRUST SUMMARY ################################')
x = TRUST.groupby(['Transact']).aggregate({'Amount':['sum']}, index=False)
print(x.to_string())
print('transactions')
#TRUST_filter_df = TRUST[(TRUST['Transact'] == 'Dividend Reinvestment')]
#print(TRUST_filter_df.to_string())
print('##################################################################')
print('\n')
print('\n'),print('\n')


# VANGUARD

# 403b 9/30/24

df4 =pd.read_csv(r"C:\Users\webzt\Dropbox\PC\Desktop\REVAMP2 python fincance 10_11_23\Vanguard Accounts 9_30_24\vanguard_403b_2024.csv")

## shaping the df3 database 
# creat TRUST data frame csv
KP_403b = pd.DataFrame()
df4['Trade Date'] = pd.to_datetime(df4['Trade Date'], errors='coerce')
KP_403b['Category'] = df4['Transaction Description']
#TRUST['TICKER'] = df3['Investment Name']
KP_403b['Transact'] = df4['Investment Name']
infer_datetime_format=True
KP_403b['Trade Date'] = pd.to_datetime(df4['Trade Date'])
KP_403b['Trade Date'] = df4['Trade Date']
KP_403b['Amount'] =df4['Dollar Amount']
KP_403b['Month'] = pd.DatetimeIndex(df4['Trade Date']).month_name()
KP_403b['ACCOUNT'] ='KP_403b'

#print(KP_403b.head(10))

# sum it all up for plan contributions. 
print('################ KP_403B SUMMARY ################################')
x = KP_403b.groupby(['Category']).aggregate({'Amount':['sum']}, index=False)
print(x.to_string())
print('##################################################################')
print('\n')
print('\n'),print('\n')


## KP UNION


df5 =pd.read_csv(r"C:\Users\webzt\Dropbox\PC\Desktop\REVAMP2 python fincance 10_11_23\Vanguard Accounts 9_30_24\vanguard_UNION_2024.csv")


## shaping the df3 database 
# creat TRUST data frame csv
KP_UNION = pd.DataFrame()
df5['Trade Date'] = pd.to_datetime(df5['Trade Date'], errors='coerce')
KP_UNION['Category'] = df5['Transaction Description']
#TRUST['TICKER'] = df3['Investment Name']
KP_UNION['Transact'] = df5['Investment Name']
infer_datetime_format=True
KP_UNION['Trade Date'] = pd.to_datetime(df5['Trade Date'])
KP_UNION['Trade Date'] = df5['Trade Date']
KP_UNION['Amount'] =df5['Dollar Amount']
KP_UNION['Month'] = pd.DatetimeIndex(df5['Trade Date']).month_name()
KP_UNION['ACCOUNT'] ='KP_UNION'

# sum it all up for plan contributions. 
print('################ KP_UNION SUMMARY ################################')
x = KP_UNION.groupby(['Category']).aggregate({'Amount':['sum']}, index=False)
print(x.to_string())
print('##################################################################')
print('\n')
print('\n'),print('\n')

# Roth IRA Jeff 


df6 =pd.read_csv(r"C:\Users\webzt\Dropbox\PC\Desktop\REVAMP2 python fincance 10_11_23\Vanguard Accounts 9_30_24\vanguard_JEFF_ROTH_2024.csv")
#print(df6.head(20))

## shaping the df3 database 
# creat TRUST data frame csv
JEFF_ROTH = pd.DataFrame()
df6['Trade Date'] = pd.to_datetime(df6['Trade Date'], errors='coerce')
JEFF_ROTH['Category'] = df6['Transaction Type']
JEFF_ROTH['Transact'] = df6['Transaction Description']
infer_datetime_format=True
JEFF_ROTH['Trade Date'] = pd.to_datetime(df6['Trade Date'])
JEFF_ROTH['Trade Date'] = df6['Trade Date']
JEFF_ROTH['Amount'] =df6['Net Amount']
JEFF_ROTH['Month'] = pd.DatetimeIndex(df6['Trade Date']).month_name()
JEFF_ROTH['ACCOUNT'] ='JEFF_ROTH'

# sum it all up for plan contributions. 
print('################ JEFF ROTH IRA SUMMARY ################################')
x = JEFF_ROTH.groupby(['Category']).aggregate({'Amount':['sum']}, index=False)
print(x.to_string())
print('##################################################################')
print('\n')
print('\n'),print('\n')

# JEFF ROLLOVER IRA


df7 =pd.read_csv(r"C:\Users\webzt\Dropbox\PC\Desktop\REVAMP2 python fincance 10_11_23\Vanguard Accounts 9_30_24\vanguard_ROLLOVER_IRA_2024.csv")
#print(df6.head(20))

## shaping the df3 database 
# creat TRUST data frame csv
JEFF_IRA = pd.DataFrame()
df7['Trade Date'] = pd.to_datetime(df7['Trade Date'], errors='coerce')
JEFF_IRA['Category'] = df7['Transaction Type']
JEFF_IRA['Transact'] = df7['Transaction Description']
infer_datetime_format=True
JEFF_IRA['Trade Date'] = pd.to_datetime(df7['Trade Date'])
JEFF_IRA['Trade Date'] = df7['Trade Date']
JEFF_IRA['Amount'] =df7['Net Amount']
JEFF_IRA['Month'] = pd.DatetimeIndex(df7['Trade Date']).month_name()
JEFF_IRA['ACCOUNT'] ='JEFF_IRA'

# sum it all up for plan contributions. 
print('################ JEFF IRA SUMMARY ################################')
x = JEFF_IRA.groupby(['Category']).aggregate({'Amount':['sum']}, index=False)
print(x.to_string())
print('##################################################################')
print('\n')
print('\n'),print('\n')

# CORI IRA

df8 =pd.read_csv(r"C:\Users\webzt\Dropbox\PC\Desktop\REVAMP2 python fincance 10_11_23\Vanguard Accounts 9_30_24\vanguard_CORI_ROLLOVER_IRA_2024.csv")
#print(df6.head(20))

## shaping the df3 database 
# creat TRUST data frame csv
CORI_IRA = pd.DataFrame()
df8['Trade Date'] = pd.to_datetime(df8['Trade Date'], errors='coerce')
CORI_IRA['Category'] = df8['Transaction Type']
CORI_IRA['Transact'] = df8['Transaction Description']
infer_datetime_format=True
CORI_IRA['Trade Date'] = pd.to_datetime(df8['Trade Date'])
CORI_IRA['Trade Date'] = df8['Trade Date']
CORI_IRA['Amount'] =df8['Net Amount']
CORI_IRA['Month'] = pd.DatetimeIndex(df8['Trade Date']).month_name()
CORI_IRA['ACCOUNT'] ='CORI_IRA'

# sum it all up for plan contributions. 
print('################ CORI IRA SUMMARY ################################')
x = CORI_IRA.groupby(['Category']).aggregate({'Amount':['sum']}, index=False)
print(x.to_string())
print('##################################################################')
print('\n')
print('\n'),print('\n')

#### TOTALS FOR ALL ACCOUNTS
# HEADER #  Account Number,Investment Name,Symbol,Shares,Share Price,Total Value,


df9 =pd.read_csv(r"C:\Users\webzt\Dropbox\PC\Desktop\REVAMP2 python fincance 10_11_23\Vanguard Accounts 9_30_24\All_VANGUARD_ACCOUNTS_2024.csv")
#print(df6.head(20))

## shaping the df3 database 
# creat TRUST data frame csv
VANGUARD_TOTALS = pd.DataFrame()
#df9['Trade Date'] = pd.to_datetime(df9['Trade Date'], errors='coerce')
VANGUARD_TOTALS['ACCOUNT NUMBER'] = df9['Account Number']
VANGUARD_TOTALS['Investment Name'] = df9['Investment Name']
infer_datetime_format=True
#VANGUARD_TOTALS['Trade Date'] = pd.to_datetime(df9['Trade Date'])
VANGUARD_TOTALS['Symbol'] = df9['Symbol']
VANGUARD_TOTALS['Amount'] =df9['Total Value']
#VANGUARD_TOTALS['Month'] = pd.DatetimeIndex(df9['Trade Date']).month_name()
VANGUARD_TOTALS['ACCOUNT'] ='VANGUARD ACCOUNTS TOTALS'

# sum it all up for plan contributions. 
print('################ VANGUARD ACCOUNT SUMMARY ################################')
#x = VANGUARD_TOTALS.groupby(['Investment Name']).aggregate({'Amount':['sum']}, index=False)
#print(x.to_string())

#Group by 'ACCOUNT NUMBER' and 'Investment Name' with sums
VANGUARD_GROUPED = VANGUARD_TOTALS.groupby(['ACCOUNT NUMBER', 'Investment Name'])['Amount'].sum().reset_index()

# Display the grouped data in a hierarchical way
# Step 11: Calculate the sum of each column and add as a new row labeled 'Total'

# Add a 'Total' column at the end of the table to sum the investments for each account
#VANGUARD_GROUPED['Total'] = VANGUARD_GROUPED.sum(axis=1)

# Add a 'Grand Total' row at the bottom to sum the totals of all accounts
#VANGUARD_GROUPED.loc['Grand Total'] = VANGUARD_GROUPED.sum()
#print(VANGUARD_GROUPED)

x = VANGUARD_TOTALS.groupby(['ACCOUNT NUMBER']).aggregate({'Amount':['sum']}, index=False)
print(x.to_string())

x = VANGUARD_TOTALS.groupby(['ACCOUNT']).aggregate({'Amount':['sum']}, index=False)
print(x.to_string())
print('##################################################################')
print('\n')
print('\n'),print('\n')



# FUNCTIONS. 


def Investment_data_set():
    '''
    # is the database. 
    if YEAR == "2024":
        # connect to the database
        engine = create_engine('sqlite:///mydatabase_combined_data2024.db').connect() 
        # READ THE TABLE OF THE DATABASE INTO PANDAS!!!!!!!!!!!!!!!!!!!
        df = pd.read_sql_table('combined_data_2024', engine)
        #now put it into the variable Combined_account_data_2023


        # PRINT IT
        #print(df.to_string())

    if YEAR == "2023":

        # connect to the database
        engine = create_engine('sqlite:///mydatabase_combined_data2023.db').connect() 
        # READ THE TABLE OF THE DATABASE INTO PANDAS!!!!!!!!!!!!!!!!!!!
        df = pd.read_sql_table('combined_data_2023', engine)
        #now put it into the variable Combined_account_data_2023

    else: 
        print("WE DON\'T HAVE THE YEAR, TRY AGAIN SUCKER !!!!!" )
    # Step 4: Create a dictionary to map categories to custom groups
    '''
    

    #engine = create_engine('sqlite:///mydatabase_combined_data2024.db').connect() 
    # READ THE TABLE OF THE DATABASE INTO PANDAS!!!!!!!!!!!!!!!!!!!
    #df = pd.read_sql_table('combined_data_2024', engine)
    ####################################################################################
   
    # Step 1: Map categories using category_mapping
    # anything you map here will make a colum on the data base and not including it in the total for transact for M(month)
    # it just works out that way, the way it is processed. becuase it is mapping it before it does the 
    # exclude_categories. so this way you can see what the total is with adding or subtracting things !!!!!
    # I also made a column to subrtract items from transact for the month to find was the total supluss is for the 
    # month. So also by looking at the columns at the head of the DB you can see what is not included in the Transact for M, 
    # this is a good way to know in case you forget if you added or subtract, like morgage or something. 
    # then you know what to add in the program to subtract from the Income column to get surplus. 
    # good quick referrence. 
    '''
    category_mapping = {
        #'Utilities': 'Monthly base',
        #'Groceries': 'Monthly base',
        'Mortgage': 'Mortgage',
        #'USAA_Insurance': 'Insurance',
        'Paycheck': 'Income',
        'S_S': 'Income',
        'Amazon' :'Amazon Spending'
        #'Fuel': 'Gas'
    }

    # Create a new DataFrame df2 to store the mapped data
    df2 = pd.DataFrame()
    df2['Category_group'] = df2['Category'].map(category_mapping).fillna('Other')

    # Step 2: Maintain the previous mapping but group specific categories using np.where
    exclude_categories = ['credit card payment', 'USAA_VISA_PAYMENT', 'Vanguard Investment', 'Costco_cc_payment', 'Transfer', 'S_S', 'Paycheck', 'Interest']

    # Only overwrite the values in Category_group that are NOT already mapped (i.e., still 'Other')
    df2['Category_group'] = np.where(df2['Category_group'] == 'Other', np.where(df2['Category'].isin(exclude_categories), df['Category'], 'Transact for M'), df2['Category_group'])
   
    # Add the remaining necessary columns from the original DataFrame
    df2['Amount'] = df2['Amount']
    df2['Month'] = df2['Month']
    df2['ACCOUNT'] = df2['ACCOUNT']
    df2['Transact'] = df2['Transact']
    df2['Category'] = df2['Category']
    
    '''


    # ADD FORD AVANTAGE ACCOUNT
    # NOTE NOTE NOTE NOTE !!! AS OF NOW THIS DOESN'T CONTAIN THE ROTHS, CORI ROTH, OR THE KP UNION. 

    df2 = pd.concat([FORD_ADVANTAGE24,TRUST,KP_403b,JEFF_ROTH,CORI_IRA,KP_UNION,JEFF_IRA], axis=0)
    #print(df2.head(10))

    # Step 4: Define the correct order of months
    month_order = ['January', 'February', 'March', 'April',
                    'May', 'June', 'July', 'August', 'September', 
                    'October', 'November', 'December']

    # Step 5: Convert 'Month' column to a categorical type with the defined order
    df2['Month'] = pd.Categorical(df2['Month'], categories=month_order, ordered=True)

    # Step 6: Create a pivot table with 'Month' as rows, 'Category_group' as columns, and sum of 'Amount'
    #pivot_df = df2.pivot_table(index='Month', columns='Category_group', values='Amount', aggfunc='sum', fill_value=0)
    pivot_df = df2.pivot_table(index='Month', columns='Category', values='Amount', aggfunc='sum', fill_value=0)

     # NOTE FILTER OTHER. 
    # Step 7: Filter the original DataFrame for transactions from the 'COSTCO_CC' account and group by month
    ##pivot_df['OTHER'] = other_df


    #FORD -------------------------------------------------------------->
    #print('----------------- FORD INTEREST 2024 -------------------------------------------')
    ford24_df = df2[df2['ACCOUNT'] =='FORD ACCOUNT'].groupby('Month')['Amount'].sum()  
    pivot_df['Ford Interest'] = ford24_df

    # FORD TRANSFER OUT OF FORD ( USUALLY THE INTEREST TO BE INVESTED IN TRUST )
    #FORD_ADVANTAGE24['WITHDRAW'] = FORD24['<Withdrawal Amount>']
    ford_interest_to_invest24_df = df2[(df2['Transact'] == 'FUNDS TRANSFER')
                                        & (df2['ACCOUNT'] == 'FORD ACCOUNT')].groupby('Month')['WITHDRAW'].sum() 
    pivot_df['Ford transfer out to invest'] = ford_interest_to_invest24_df

    
    # NOTE TRUST DIVIDENDS
    
    #DIVID_TRUST_df = df2[df2['Transact'].str.contains('Dividend Received', case=False)]
    filtered_df = df2[(df2['Transact'] == 'Dividend Received') & (df2['ACCOUNT'] == 'TRUST')].groupby('Month')['Amount'].sum()
    
    #print(filtered_df.to_string())
    pivot_df['TRUST DIVID'] = filtered_df
   
  
    # TRUST BUY - INVESTED 
    
    filtered_df = df2[(df2['Transact'] == 'Buy') & (df2['ACCOUNT'] == 'TRUST')].groupby('Month')['Amount'].sum()
    pivot_df['TUST BUY INVESTED'] = filtered_df
   
    # TRUST HOW MUCH TRANSFERING TO TRUST VS BUY - CAN SEE DIFFERENCE AND HOW MUCH NEEDS TO BE INCREASED IN INVESTING A MONTH

    filtered_df = df2[(df2['Transact'] == 'Buy') & (df2['ACCOUNT'] == 'TRUST')].groupby('Month')['Amount'].sum()
    pivot_df['TUST BUY INVESTED'] = filtered_df

    # TRUST CASH  Funds received via Electronic Bank Transfer INTO FEDERAL MONEY MARKET. 
    # cash means it came in from usaa

    filtered_df = df2[(df2['TICKER'] == 'CASH') & (df2['ACCOUNT'] == 'TRUST')].groupby('Month')['Amount'].sum()
    pivot_df['CASH TRANSFERED TO TRUST'] = filtered_df

    # FILTER JEFF ROTH BUY
    filtered_df = df2[(df2['Transact'] == 'Buy') & (df2['ACCOUNT'] == 'JEFF_ROTH')].groupby('Month')['Amount'].sum()
    pivot_df['JEFF_ROTH_CONTRIBUTIONS'] = filtered_df

    # ADD DIVIDENDS FROM TRUST AND FORD TOGETHER AND PUT IN COLUM 
    
# this makes everything + so they can be subtracted
    pivot_df['TRUST+FORD DIVID'] = (
        pivot_df['TRUST DIVID'] 
        + pivot_df['Ford Interest'].abs() 
        
    )

  
    # KP_403b
    
    #filtered_df = #DIVID_TRUST_df = df2[df2['Transact'].str.contains('Dividend Received', case=False)]
    filtered_df = df2[(df2['Category'] == 'Plan Contribution') & (df2['ACCOUNT'] == 'KP_403b')].groupby('Month')['Amount'].sum()
    
    #print(filtered_df.to_string())
    #pivot_df['TRUST DIVID'] = filtered_df[(df2['Transact'] == 'Dividend Received') & (df2['ACCOUNT'] == 'TRUST')].groupby('Month')['Amount'].sum()
    
    #print(filtered_df.to_string())
    pivot_df['KP_403B PLAN CONTRIBUTIONS'] = filtered_df




   # only print the columons needed in summay!!! 10/15/24

    filtered_pivot = pivot_df[['KP_403B PLAN CONTRIBUTIONS', 'JEFF_ROTH_CONTRIBUTIONS','CASH TRANSFERED TO TRUST','Ford Interest',
                             'TRUST DIVID','Ford transfer out to invest', 'TRUST+FORD DIVID','TUST BUY INVESTED','CASH TRANSFERED TO TRUST','JEFF_ROTH_CONTRIBUTIONS',]]
    
    filtered_pivot.loc['Total'] = filtered_pivot.sum().round(0)
    filtered_pivot.loc['Mean'] =filtered_pivot[(filtered_pivot.index != 'Total') & (filtered_pivot != 0).any(axis=1)].mean().round(0).astype(int)

    # Step 11: Calculate the sum of each column and add as a new row labeled 'Total'
    pivot_df.loc['Total'] = pivot_df.sum().round(0)
    
    # Step 12: Calculate the mean of each column and add as a new row labeled 'Mean'
    # this only gives for the monthly total and doesn't include the total row. 
    # and not including the months with total of 0, for the months we have not had yet. 
    # pivot_df.loc['Mean'] = pivot_df.loc[pivot_df.index != 'Total'].mean().round(0).astype(int)
    # pivot_df.loc['Mean'] = pivot_df[(pivot_df != 0).any(axis=1)].mean().round(0).astype(int)
    pivot_df.loc['Mean'] = pivot_df[(pivot_df.index != 'Total') & (pivot_df != 0).any(axis=1)].mean().round(0).astype(int)

    # make it so it doesn't print off the terminal
    pd.set_option('display.max_columns', 20)  # Adjust the number of columns to fit your terminal width
    pd.set_option('display.width', 100)       # Set the output width for better formatting


    # Output the updated pivot table
    print(F'INVESTMENT DATA SET ________________________________________>')
    print(filtered_pivot)
    
    #print(pivot_df)

Investment_data_set()

#print(CORI_IRA.to_string())
# NOTE CHECK OUT CORI ????? IRA - WHERE IS IT ????? 10/15/2024



                           