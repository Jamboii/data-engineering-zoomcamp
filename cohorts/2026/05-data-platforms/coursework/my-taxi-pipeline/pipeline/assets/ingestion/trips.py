"""@bruin

name: ingestion.trips
type: python
image: python:3.11
connection: duckdb-default

materialization:
  type: table
  strategy: append

@bruin"""

import json
import os
from datetime import datetime
from io import BytesIO

from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

import pandas as pd
import requests


def materialize():
    """
    Fetch NYC Taxi trip data from the TLC public endpoint.

    This function:
    1. Parses date range from BRUIN_START_DATE and BRUIN_END_DATE
    2. Gets taxi types from pipeline variables
    3. Constructs URLs for monthly Parquet files
    4. Downloads and combines data into a single DataFrame
    5. Adds extracted_at timestamp for lineage tracking
    6. Returns the DataFrame for Bruin to materialize

    Returns:
        pd.DataFrame: Combined trip data with extracted_at column
    """

    # Parse environment variables
    start_date_str = os.getenv("BRUIN_START_DATE", "2022-01-01")
    end_date_str = os.getenv("BRUIN_END_DATE", "2022-01-31")

    # Parse dates
    start_date = parse_date(start_date_str).date()
    end_date = parse_date(end_date_str).date()

    # Get taxi types from pipeline variables
    bruin_vars_str = os.getenv("BRUIN_VARS", '{"taxi_types": ["yellow"]}')
    bruin_vars = json.loads(bruin_vars_str)
    taxi_types = bruin_vars.get("taxi_types", ["yellow"])

    # Base URL for TLC data
    base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data"

    # Collect DataFrames for all months and taxi types
    dataframes = []
    current_date = start_date

    while current_date <= end_date:
        year = current_date.year
        month = current_date.month

        # Fetch data for each taxi type in this month
        for taxi_type in taxi_types:
            # Construct filename
            filename = f"{taxi_type}_tripdata_{year:04d}-{month:02d}.parquet"
            url = f"{base_url}/{filename}"

            try:
                # Download the parquet file
                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    # Read parquet from bytes
                    df = pd.read_parquet(BytesIO(response.content))

                    # Add metadata column
                    df["extracted_at"] = datetime.utcnow()

                    dataframes.append(df)
                    print(f"✓ Loaded {filename}: {len(df)} rows")
                else:
                    print(f"⚠ Skipped {filename}: HTTP {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"⚠ Failed to download {filename}: {str(e)}")
            except Exception as e:
                print(f"⚠ Error processing {filename}: {str(e)}")

        # Move to next month
        current_date += relativedelta(months=1)

    # Combine all DataFrames
    if dataframes:
        result_df = pd.concat(dataframes, ignore_index=True)
        print(f"\n✓ Total rows ingested: {len(result_df)}")
        return result_df
    else:
        print("⚠ No data was retrieved. Check URLs and date range.")
        # Return empty DataFrame with extracted_at column
        return pd.DataFrame({"extracted_at": pd.Series(dtype="datetime64[ns]")})
