





#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ONLY USE THIS FILE TO MAKE THE DATA FRAMES AS BELOW AND 
# CREATE THE BIG DATA BASE !!!!
# OTHERWISE USE THE MAIN.PY
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!








# NEW FINANCE PROGRAM START, USING WHAT I HAVE LEARNED 10_11_24
# MADE 10/10/24 TO FIX THE CITY BANK COSTCO CHARGES. 
# EMPOWER IS NOT DOWNLOADING EVERYTHING, GOING TO BYPASS IT NOW AND WENT TO CITY WEBSITE. 
# GOING TO USE SEARCH BY DATES TO BETTER MATCH CITY BANK STATEMENT DATES, GET MORE ACCURATE OF WHAT THE CC BILL WILL BE. 
# WILL ALSO USE FLASK TO SHOW IN HTM FORMAT ???? WORK ON FLASK SKILLS ????



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


import openpyxl
from openpyxl import Workbook
import xlsxwriter
import openpyxl 
from datetime import datetime
import seaborn as sns



# my CATEGORY MAPPING FOR NOW - COULD MOVE THIS INTO ANOTHER MODULE. 10/11/24
# ONLY HAVE TO USE ONE WORD !!!!!! IF NEEDED. 

category_mapping = {
    'FUEL': ['ARCO#07098ARCO #07098','SHELL','7-ELEVEN','EXXON','SINCLAIR','CHEVRON', 'COSTCO GAS','FUEL', 'GAS'],
    'Grocery': ['FARMS','MAYERS','FRED','CARROT','WALGREENS','WAL-MART','COSTCO','NEW SEASONS MARKET','TRADER JOE','SAFEWAY', 'FRED-MEYER', 'Supermarket','CHUCKS'],

    'Subscription': ['Norton','OPENAI','Adobe','Strava','OpenAI','Ngrok','Digitalocea','Prime','MEDIUM','STORAGE','TRAININGPKS','Kindle','LUCIDSOFTWA','EVERNOTE','YOUTUBE','NETFLIX', 'SPOTIFY', 'DROPBOX'],
    'Utilities': ['Verizon','WASTE','UTILITIES','NATURAL','COMCAST'],
    'AMAZON' :['AMZN','Amazon','AMAZON'],
    'PET' :[ 'CHEWY','PETCO','MUD BAY'],

    'RESTAURANT' :['ICE CREAM',
                   'FOOD','RUSTIC','NOSTRA','DABOBA','MMS','TAMALES',
                   'GRILL','CHICK','BURGER','DOMINO','JAPANESE','BURGERVILL',
                   'PIZZERIA','COFFEE','MENCHIES FROYO MENB518','BASKIN','YOGURT',
                   'THE DOT SHOP','DK HEWN','BUTTERCUP','RESTAURANT','PIZZA',
                   'BRIDGESIDE','SHARIS','BAGEL','CUISINE','CAFE','TREAT','KRISPY',
                   'SUSHI','THAI','DAIRY QUEEN','STARBUCKS','MCDONALD','CHIPOTLE',
                   'PANDA EXPRESS','HOCKINSON MARKET','Subway','ALADDIN CAFE',
                   'ASIAN MARKET'],

    'HOUSEHOLD' :['BLINDS','Walmart','WALMART','JOANN','DEPOT','NAILS','MCFARLANES','IKEA','SALON','LAWN','LOWES','HAIR','USPS','DOLLAR','HARBOR','PROPANE'],
    'KID' :['Pumpkin','SPIRIT HALLOWEEN'],
    'AUTO' : ['PARKING','NAPA','REILLY','AUTO','VEHICLE LICENSING'],
    'RECREATION' : ['CLUB','ReflectionRun','ALS','CLIMBING','Sky Zone','ScaryRun','IMAX'],
    'MEDICAL' :['MEDICAL','PHARMACY','DENTAL','KP'],
    'EXERCISE' :['BODYWORKS'],
    'KIDS SCHOOL' :['PHOTO','Check','Cascadia','GARDNER','CASCADIA','SQUARE','Gardner','CHESS','Scholastic','Photo'],
    'MOVIES' : ['FANDANGO * FANDANGO.COM C','PLAZA 10','AMC 0614 VANCOUVER MAL'],
    'VACATION' :['Eats','Uber','HAYDEN','STEAMBOAT','INNS','PDX','RUTLAND','Bristol','ALASKA','ZOO','BRISTOL','RESORT','JETBLUE','MAKETPLACE','BOSTON','DELAWARE'],
    'SPORTING GOODS' :['SPORTING'],
    'WORK' :[ 'NCCPA','DEA','TRAINING',],
    'CME' :['EMRAP','ANTIMICROBIAL','ROSH','ACADEMY','Hippoeduc',],
    'NANNY TAX' : ['ESD','Esd'],
    'LOOK INTO' : ['PP*P32C7C17AD 402-935-7733','MICROSOFT','Online','Teva','0034541195','eBay','ALLCITYPRIN'],
    'CLOTHING' : ['TJMAXX #0376','MACYS VANCOUVER','ZAPPOS.COM','OUAC','FOOT','Patagonia','LANDS','GOODWILL'],
    'MEMBERSHIP' : ['Membership'],
    'LICENSE' : ['LICENSE'],
    'KIDS' : ['POKEMON'],
    'REGISTRATOIN ? ' :['CITY','CLARK',],
    'CITY CC PAYMENT' :['Citi'],
    'USAA CC PAYMENT'  :['Card'],
    'NANNY PAY' :['Marlena','Tremback'],
    'TRANSFER' :['Transfer','TRANSFER'],
    'Security' :['Security'],
    'ACCOUNT INTEREST' :['Interest'],
    'Mortgage' :['Fargo'],
    'TAXES' :['Treasury','IRS'],
    'INSURANCE' :['Insurance'],
    'MOTORCYCLE INSURANCE' :['Progressive'],
    'PAYCHECK'  :['Foundation'],
    'INCOME ? KP' : ['Financial'],
    'VANGUARD INVESTMENT' :['Vanguard'],
    'SHOPPING' :['SUPERCENTER'],
    'EXTRA':['Mobile Deposit'],
    'Christmass2024':['ART','Mountain','Columbia',],
    'Christmass2025':['Universalcy','HOBBY-LOBBY #930','',],
    'USAA INSURANCE DIVID':['Dividend'],
    'Hobbies':['PARKROSE HARDWARE',]




    # Add more mappings as needed
}

# THIS IS ALL COSTCO TRANSACTIONS FROM CITYBANK WEBSITE.
#df2 = pd.read_csv(f"City_Year to date_2024.csv")## Date,Description,Debit

# downloaded city bank transactions year to date on 11/4/2024

##############################################################
# for YEAR 2024  -- should be done with this now - have made final for 2024 on 1_31_25 and fixed the others. 
#df2 = pd.read_csv(f"City_Visa_Year to date_download_12_30_2024.CSV")## Date,Description,Debit
##############################################################

############# should be using this now for 2025 ################################################### 
# for year 2025 (1_30_25) !! and change the name -- below to make the data base for 2025
df2 = pd.read_csv(f"City_Visa_Year to date_download_4_3_2025.CSV")## Date,Description,Debit
####################################################################################################


# create the new data fram for city bank
df_City_full_Year = pd.DataFrame()
# C:\Users\webzt\Dropbox\PC\Desktop\revamp python finance program 6_24-23\City_Year to date_2024.CSV
#df_City_full_Year = pd.read_csv(f"City_Year to date_2024.csv")## Date,Description,Debit

#csv_file_path = 'City_Year to date_2024.CSV'  # Replace with your actual file path
#df_City_full_Year = pd.read_csv(csv_file_path)

# drop the payment row 'autopayment"
#df = df_City_full_Year.drop(index=96)
# Step 2: Define your dictionary of categories and keywords
# using 
# my_dictionary_lists

# define the CSV files for YEAR


#  FOR THE YEAR
#YEAR = 'FULL_YEAR_24'
YEAR = 'FULL_YEAR_25'

JCK_YEAR = pd.read_csv(f"JEFF_CHECKING_USAA_{YEAR}.csv")
JEFF_SAVE_USAA = pd.read_csv(f"JEFF_SAVINGS_USAA_{YEAR}.csv")
JointCK_year = pd.read_csv(f"JOINT_CHECKING_USAA_{YEAR}.csv")
USAA_CC_YEAR =pd.read_csv(f"USAA_VISA_{YEAR}.csv")
Ohenry_year = pd.read_csv(f"Ohenry_USAA_{YEAR}.csv")
Nanny_year = pd.read_csv(f"NANNY_USAA_{YEAR}.csv")

## make new data frame for the Year for now. 
jck_year = pd.DataFrame()
Joint_ck_year = pd.DataFrame()
Nanny_data_year = pd.DataFrame()
Ohenry_data_year = pd.DataFrame()
USAA_VISA_YEAR = pd.DataFrame()
Jeff_saving_year = pd.DataFrame()


# Create a function to categorize transactions based on keywords
def categorize_transaction(transaction):
    for category, keywords in category_mapping.items():
        if any(keyword in transaction for keyword in keywords):
            return category
    return 'Other'  # Default category if no match


# JOINT CHECKING FULL YEAR
Joint_ck_year['Amount'] = JointCK_year['Amount']
Joint_ck_year['Transact'] = JointCK_year['Description']
Joint_ck_year['Date'] = pd.to_datetime(JointCK_year['Date'])
Joint_ck_year['Month'] = pd.DatetimeIndex(JointCK_year ['Date']).month_name()
Joint_ck_year['Category'] = JointCK_year['Description'].apply(categorize_transaction)
Joint_ck_year['Category'] = np.where((Joint_ck_year['Amount'] == 2000) & (Joint_ck_year['Transact'] == 'USAA Transfer'), 'S_S', Joint_ck_year['Category'])
Joint_ck_year['ACCOUNT'] = 'JOINT CHECKING FOR YEAR'

#######ohenry_year#############
Ohenry_data_year['Amount'] = Ohenry_year['Amount']
Ohenry_data_year['Transact'] = Ohenry_year['Description']
Ohenry_data_year['Date'] = pd.to_datetime(Ohenry_year['Date'])
Ohenry_data_year['Month'] = pd.DatetimeIndex(Ohenry_year ['Date']).month_name()
Ohenry_data_year['Category'] = Ohenry_year['Description'].apply(categorize_transaction)
Ohenry_data_year['ACCOUNT'] = 'Ohenry_USAA_year'

## nanny data year
Nanny_data_year['Amount'] = Nanny_year['Amount']
Nanny_data_year['Transact'] = Nanny_year['Description']
Nanny_data_year['Date'] = pd.to_datetime(Nanny_year['Date'])
Nanny_data_year['Category'] =Nanny_year['Description'].apply(categorize_transaction)
Nanny_data_year['Month'] = pd.DatetimeIndex(Nanny_year ['Date']).month_name()
Nanny_data_year['ACCOUNT'] = 'NANNY_ACCOUNT_Year'

#JEFF CHECKING FOR YEAR
jck_year['Amount'] = JCK_YEAR['Amount']
jck_year['Transact'] = JCK_YEAR['Description']
jck_year['Date'] = pd.to_datetime(JCK_YEAR['Date'])
jck_year['Month'] = pd.DatetimeIndex(JCK_YEAR ['Date']).month_name()
jck_year['Category'] = JCK_YEAR['Description'].apply(categorize_transaction)
jck_year['ACCOUNT'] = 'JEFF CHECKING FOR YEAR'

# usaa cc visa
USAA_VISA_YEAR['Amount'] = USAA_CC_YEAR['Amount']
USAA_VISA_YEAR['Transact'] = USAA_CC_YEAR['Description']
USAA_VISA_YEAR['Date'] = pd.to_datetime(USAA_CC_YEAR['Date'])
USAA_VISA_YEAR['Month'] = pd.DatetimeIndex(USAA_CC_YEAR ['Date']).month_name()
USAA_VISA_YEAR['Category'] = USAA_CC_YEAR['Description'].apply(categorize_transaction)
USAA_VISA_YEAR['ACCOUNT'] = 'USAA CC FOR YEAR'

#JEFF_SAVE_USAA
Jeff_saving_year['Amount'] = JEFF_SAVE_USAA['Amount']
Jeff_saving_year['Transact'] = JEFF_SAVE_USAA['Description']
Jeff_saving_year['Date'] = pd.to_datetime(JEFF_SAVE_USAA['Date'])
Jeff_saving_year['Month'] = pd.DatetimeIndex(JEFF_SAVE_USAA ['Date']).month_name()
Jeff_saving_year['Category'] = JEFF_SAVE_USAA['Description'].apply(categorize_transaction)
Jeff_saving_year['ACCOUNT'] = 'JEFF SAVINGS FOR YEAR'
#Jeff_saving_year = Jeff_saving_year.set_index('Date', drop = False)


# CITY BANK DATA FROM CITY BANK ONLY NO MORE EMPOWER!! 10/11/24. 
df_City_full_Year['Amount'] = df2['Debit']
df_City_full_Year['Transact'] = df2['Description']
df_City_full_Year['Date']= pd.to_datetime(df2['Date'])
df_City_full_Year['Month'] = pd.DatetimeIndex(df_City_full_Year['Date']).month_name()
df_City_full_Year['ACCOUNT'] = 'COSTCO-FROM-CITYBANK'
#PC_COSTCO_data_year['Category'] = df2['Description'].apply(get_Category)

# Step 3: Create a new column for categories, initializing with NaN to avoid overwriting
df_City_full_Year['Category'] = pd.NA

# Step 2: Convert the 'Debit' column to numeric (remove symbols like '$', ',')
df_City_full_Year['Amount'] = pd.to_numeric(df_City_full_Year['Amount'].replace({'\$': '', ',': ''}, regex=True), errors='coerce')

# Step 3: Convert the 'Debit' column to integers
df_City_full_Year['Amount'] = df_City_full_Year['Amount'].fillna(0).astype(float)

# Step 4: Apply the function to the 'Transaction' column
df_City_full_Year['Category'] = df_City_full_Year['Transact'].apply(categorize_transaction)


#####################################################


# NOW MAKE A DATA BASE AND WORK OFF OF IT. 
# MAKE THIS A FUNCTION 

def create_data_base():
    
    # remember Combined_account_data_2003 is any year that YEAR is set to. 
    # note looks like as is, you have to delete the data base and then run this to create a new database!!! 
    # 6/11/23


    ## as of 1_31_25 make sure to change three spots, create_engine year, table name for 2025 
    ## and above for the full year 2025 ## can sort this out and add another if statement later for 2025
    if YEAR == 'FULL_YEAR_25':
        ## remember to comment out once db has been created.
        engine = create_engine('sqlite:///ONE_BIG_ACCOUNT_combined_data2025.db')  
        # name the table within data base
        table_name = 'ONE_BIG_ACCOUNT_data_2025'

        # !!!!!!!!!!!!!!!!!!!!!!add MAD MAY 2024 ( empower screwed up transactions )!!!!!!!!!!!!!!!!!
        # send it to sql database
        #df5 = PC_COSTCO_data_City_MAY24
        # add it to the combined_account_data_2023 db
        ONE_BIG_ACCOUNT = pd.concat([Nanny_data_year,
                             jck_year,USAA_VISA_YEAR,Joint_ck_year,
                             Jeff_saving_year,df_City_full_Year,Ohenry_data_year,],ignore_index=True)

        # Optionally, reset the index if needed
        #combined.reset_index(drop=True)
        # and now make it into a the sql.
        #print(combined.to_string())
        #print(PC_COSTCO_data_City_MAY24.to_string())
        ONE_BIG_ACCOUNT.to_sql(table_name,engine,if_exists='replace',index=False)
        print("DATBASE created for year 2025 !!!!!!!!!!!")
       




######################################################
#create_data_base()


# Define the date range
# THIS IS THE START AND END DATE FOR THE CREDIT CARD STATEMENT CYCLE. 

##### THESE ARE THE MONTHS FOR CREDIT CARD CLOSING AND OPENTING DATES FOR BILLING. 
# DONE OTHERS. ( expensive month cycle)
#start_date = '2024-08-09'
#end_date = '2024-09-09'

# DONE OTHERS
#start_date = '2024-07-09'
#end_date = '2024-08-08'

# DONE OTHERS
#start_date = '2024-09-10'
#end_date = '2024-10-08'

# all dates as of today !!! 10_10_24
#start_date = '2024-01-01'
#end_date = '2024-10-01'

# 
start_date = '2025-03-01'
end_date = '2025-4-08'

# Filter the DataFrame for the date range
df_City_full_Year_date_filter = df_City_full_Year[(df_City_full_Year['Date'] >= start_date) & (df_City_full_Year['Date'] <= end_date)]

# Sum the 'Amount' column
#print(Costco_filter.to_string())

#total_amount =df_City_full_Year['Amount'].sum()
#total_count = df_City_full_Year['Amount'].count()

#other_category_df = df[df['Category'] == 'Other']
other_filter_df = df_City_full_Year[df_City_full_Year['Category'] == 'Other']
Grocery_filter_df = df_City_full_Year[df_City_full_Year['Category'] == 'Grocery']
#Grocery_filter_df = Grocery_filter_df[(Grocery_filter_df['Date'] >= start_date)
 #                                                  & (Grocery_filter_df['Date'] <= end_date)]

    # group by month. 
subx_month = df_City_full_Year.groupby(['Category','Month']).aggregate({'Category':['count'],'Amount':['sum']}, index=False)


# Adjust Pandas options to display all rows and columns

# Now print the DataFrame
#print(ONE_BIG_ACCOUNT.to_string())
print("###########other##############")
#4print(other_filter_df.to_string())

print("############transaction for the moth searching###################")

# attach to database to search the whole big database
# because before you were just creating the database now you attach and search it 
# the database for others. 

engine = create_engine('sqlite:///ONE_BIG_ACCOUNT_combined_data2025.db').connect() 
# READ THE TABLE OF THE DATABASE INTO PANDAS!!!!!!!!!!!!!!!!!!!
ONE_BIG_ACCOUNT_DATABASE = pd.read_sql_table('ONE_BIG_ACCOUNT_data_2025', engine)
#now put it into the variable Combined_account_data_2023

print("__________________________@@@!!!__________________________________")
print(" CONNECTED TO ONE_BIG_ACCOUNT_combined_data2024.db")
print("__________________________@@@!!!__________________________________")

seach_db_for_other = ONE_BIG_ACCOUNT_DATABASE[ONE_BIG_ACCOUNT_DATABASE['Category'] == 'Grocery']
print("the database others: ------------->>")
print("xxxxxxxxxxxxxxxxxxxxxxxxxxxx")

print(seach_db_for_other.to_string())

print("#############################")
#print(df_City_full_Year_date_filter.to_string())
print("#################################")
#print(Grocery_filter_df.to_string())
#total_amount =Grocery_filter_df['Amount'].sum()
#total_count = df_City_full_Year['Amount'].count()
#print(df_City_full_Year.to_string())
#print(total_amount)
print("#################################")
#print(subx_month.to_string())
print("#################################")
#print(Joint_ck_year.to_string())
print("#################################")
#print(Ohenry_data_year.to_string())
print("#################################")
#print(Nanny_data_year.to_string())
print("#################################")
#print(jck_year.to_string())
print("#################################")
#print(USAA_VISA_YEAR.to_string())
print("#################################")
#print(Jeff_saving_year.to_string())
print("#################################")
# TO BIG TO BRING THE WHOLE THING HAVE TO USE PARTS. - PUT IT INTO A DATA BASE TO LOOK AT THE WHOLE THING !!!!!
# MAKE A DATA BASE. 
#print(ONE_BIG_ACCOUNT.head(20))

# NOTE    10/11/2024
# NEXT WORK ON USING THE PIVOT TABLE BY MONTH IN A MONDULE FROM HERE LOOK AT THE LAST PROGRAM FILE WITH .PY FILE 
#C:\Users\webzt\Dropbox\PC\Desktop\revamp python finance program 6_24-23\Monthly_data_set2.py 
# CAN DO FURTHER MAPPING FOR CATEGORY MANIPULATION. 
# BIG GOAL IS GRAPHS AND PREDICTIONS OF SPENDING BASD ON PREVIOUS - TO PREDICT SAVINGS AND OPTIMIZE INVESTMENTS
# USE STRINGS TO ASK QUESTIONS AND TALK LIKE AI, YOU NEED TO , MAKE THIS INVESTMENT DEPOSIT AT THESE TIMES - GIVE OUTLINE TO HELP AND 
# AVOID PROCRASTIATION !!!!!!!!!!!!!!!
# CREAT DATABASE EACH TIME OTHER CSV UPDATED


## ONLY CREATE THE DATE BASE FROM THIS FILE

 
#create_data_base()   # this has to go at the top or you will get a error 12/11/2024





