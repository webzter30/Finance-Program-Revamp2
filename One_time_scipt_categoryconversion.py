import csv

# Paste your original category_mapping here:

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
# Write to CSV
with open('categories.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['keyword', 'category'])  # header row

    for category, keywords in category_mapping.items():
        for keyword in keywords:
            if keyword.strip():  # skip blanks
                writer.writerow([keyword.strip(), category])

print("✅ categories.csv has been created.")
