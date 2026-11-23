import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from datetime import datetime
import boto3
import io
import re

# ============================================================
# S3 CONFIGURATION
# ============================================================

S3_ENDPOINT = "http://localhost:4566"
AWS_ACCESS_KEY = "test"
AWS_SECRET_KEY = "test"
AWS_REGION = "us-east-1"

BUCKET_NAME = "my-bucket"
FILE_KEY = "raw/mastercat13072024.csv"

# ============================================================
# CONNECT TO FLOCI S3
# ============================================================

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

print("Successfully connected to Floci S3.")

# ============================================================
# EXTRACT CSV DATA
# ============================================================

def extract_csv_from_s3(bucket, file_key):

    try:
        # Retrieve CSV object from S3
        response = s3.get_object(
            Bucket=bucket,
            Key=file_key
        )

        # Read raw file bytes
        raw_data = response["Body"].read()

        # Convert CSV bytes into Pandas DataFrame
        df = pd.read_csv(
            io.BytesIO(raw_data),
            sep=";",
            encoding="utf-8",
            low_memory=False
        )

        print("CSV successfully extracted from Floci S3.")
        print(f"Total records extracted: {len(df)}")
        print(f"Total columns extracted: {len(df.columns)}")

        return df

    except UnicodeDecodeError:
        # Retry using an alternative encoding
        df = pd.read_csv(
            io.BytesIO(raw_data),
            sep=";",
            encoding="latin1",
            low_memory=False
        )

        print("CSV successfully extracted using latin1 encoding.")
        return df

    except Exception as e:
        print(f"Extraction failed: {e}")
        return None


# ============================================================
# XECUTE EXTRACTION
# ============================================================

df = extract_csv_from_s3(
    BUCKET_NAME,
    FILE_KEY
)

# ============================================================
# VALIDATE EXTRACTED DATA
# ============================================================

if df is not None:

    print("\nEXTRACTION SUMMARY")
    print("----------------------------")

    print("\nDataFrame information:")
    print(df.info())

    print("\nExtraction completed successfully.")

else:
    print("Data extraction unsuccessful.")


cols = [
    "Product Code", "FULL Description", "Manufact Code", "Unit", "Balance",
    "Product Type", "Non-stock", "Status", "Frozen", "LOC 01", "Free Stock",
    "Total QTY", "Minimum Stock", "Maximum Stock", "Stock Value",
    "Stock Replacement", "Cost Vs Rep%", "Bin Location", "Last Full Check",
    "Last PI Check", "Label Printed", "Last Sale Date", "Days Last Sold",
    "Last Rec", "Last Rec.1", "Last Supplier", "Stock Supplier",
    "Supplier Name", "Reordering", "Reorder Cat.", "Forecast Avg",
    "Reserve Level", "Excl Search BR", "Excl Search CF", "Standard Cost",
    "Avg Unit", "AVG Cost", "AVG Cost (SL UoM)", "Last Purch Price",
    "Pur Net Cost", "Unit.1", "SL Level", "List", "Base", "Retail",
    "Sales Unit", "Currency", "MU% (from Base)", "GP% (from Avg)",
    "%(Base v Avg)", "%(Base v List)", "%(Base v Nett)", "Upd from Purchase",
    "Prod Marg G", "BR Marg L", "BR Marg U", "Consolidate Delete",
    "Classification", "YTD Num Demands", "LYR Num Demands", "AGE Status",
]

# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

def clean(c: str) -> str:
    c = c.replace("%", " pct ")
    c = re.sub(r"[^0-9a-zA-Z]+", "_", c)
    return c.strip("_").lower()


# ============================================================
# GENERATE CLEAN COLUMN NAMES
# ============================================================

new_names = [clean(c) for c in cols]

# Check for duplicate column names
assert len(set(new_names)) == len(new_names), \
    "Column name collision after cleaning!"


# ============================================================
# VALIDATE EXPECTED COLUMNS
# ============================================================

missing_cols = [c for c in cols if c not in df.columns]

if missing_cols:
    raise ValueError(f"Missing columns: {missing_cols}")


# ============================================================
# SELECT AND RENAME COLUMNS
# ============================================================

df = df[cols].copy()

df.columns = new_names


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("Column standardisation successful!")
print("Total columns:", len(df.columns))
print(df.columns.tolist())


selected_columns = ['product_code','full_description','status','total_qty','minimum_stock',
               'maximum_stock','stock_value','last_full_check','last_sale_date','days_last_sold',
               'stock_supplier','supplier_name','standard_cost','avg_unit','avg_cost','last_purch_price',
                'pur_net_cost','sl_level','list','base','retail','mu_pct_from_base','gp_pct_from_avg','pct_base_v_avg', 
                'pct_base_v_list','pct_base_v_nett','classification','lyr_num_demands','age_status']

df = df[selected_columns].copy()

# ============================================================
# CONVERT DATE COLUMNS
# ============================================================

date_columns = ['last_full_check', 'last_sale_date']

for column in date_columns:

    # Replace invalid date values with NaT
    df[column] = df[column].replace(
        ["--/--/----", "", "NULL", "null"],
        pd.NA
    )

    # Convert text to datetime
    df[column] = pd.to_datetime(
        df[column].astype("string").str.strip(),
        format="%d/%m/%Y",
        errors="coerce"
    )

# ============================================================
# CONVERT NUMERIC COLUMNS
# ============================================================

numeric_columns = ['stock_value','standard_cost','avg_cost','last_purch_price','pur_net_cost','list','base',
                    'retail','mu_pct_from_base','gp_pct_from_avg','pct_base_v_avg','pct_base_v_list','pct_base_v_nett'
]

for column in numeric_columns:

    # Convert values to strings and remove surrounding spaces
    df[column] = df[column].astype("string").str.strip()

    # Replace decimal commas with decimal points
    df[column] = df[column].str.replace(",", ".", regex=False)

    # Convert to numeric; invalid values become NaN
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )
    
    
# ============================================================
# CLEAN AGE STATUS
# ============================================================

# Remove all non-numeric characters
df["age_status"] = (
    df["age_status"]
    .astype("string")
    .str.replace(r"\D", "", regex=True)
)

# Convert to nullable integer
df["age_status"] = pd.to_numeric(
    df["age_status"],
    errors="coerce"
).astype("Int64")


# ============================================================
# ADD DATE MODIFIED COLUMN
# ============================================================

# Current date and time
df["date_modified"] = pd.Timestamp.now().strftime(
    "%d/%m/%Y %H:%M:%S"
)

# ============================================================
# GENERATE CURRENT DATE
# ============================================================

today = datetime.now().strftime("%d%m%Y")


# ============================================================
# DEFINE OUTPUT FILE PATH
# ============================================================

output_path = (
    f"C:/Users/danre/Desktop/Retail Hardware Store/"
    f"masterfilenew_output{today}.csv"
)

# ============================================================
# EXPORT DATAFRAME TO CSV
# ============================================================

df.to_csv(
    output_path,
    index=False,
    sep=";",
    encoding="utf-8"
)


# ============================================================
# CONFIRM EXPORT
# ============================================================

print("CSV export successful!")
print(f"File saved: {output_path}")
print(f"Total records exported: {len(df)}")
print(f"Total columns exported: {len(df.columns)}")