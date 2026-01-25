#!/usr/bin/env python
# coding: utf-8

import click
import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm


dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64",
}

parse_dates = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]


@click.command()
@click.option("--user", default="root", help="PostgreSQL user")
@click.option("--password", default="root", help="PostgreSQL password")
@click.option("--host", default="localhost", help="PostgreSQL host")
@click.option("--port", default=5432, type=int, help="PostgreSQL port")
@click.option("--db", default="ny_taxi", help="PostgreSQL database name")
@click.option("--table", default="yellow_taxi_data", help="Target table name")
@click.option("--chunksize", default=100_000, type=int, help="Chunk size for reading CSV")
@click.option(
    "--filename", default="yellow_tripdata_2021-07.csv", type=str, help="File name to read"
)
def ingest_data(user, password, host, port, db, table, chunksize, filename):
    url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(url)

    if filename.endswith(".csv"):
        if filename.startswith("yellow"):
            df_iter = pd.read_csv(
                filename,
                parse_dates=parse_dates,
                iterator=True,
                chunksize=chunksize,
            )
        else:
            df_iter = pd.read_csv(
                filename,
                iterator=True,
                chunksize=chunksize,
            )
        first = True
        for df_chunk in tqdm(df_iter):
            if first:
                # Create table schema (no data)
                df_chunk.head(0).to_sql(name=table, con=engine, if_exists="replace")
                first = False
                print("Table created")

            # Insert chunk
            df_chunk.to_sql(name=table, con=engine, if_exists="append")

            print("Inserted:", len(df_chunk))
    elif filename.endswith(".parquet"):
        df_parquet = pd.read_parquet(filename)

        df_parquet.to_sql(name=table, con=engine, if_exists="replace")
    else:
        raise ValueError(f"Cannot read filename '{filename}'. Invalid extension")


if __name__ == "__main__":
    ingest_data()
