import dataclasses
import json
import sys
import time
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from kafka import KafkaProducer
from models import ride_from_row

# Download NYC green taxi trip data
url = "https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2025-10.parquet"
# Keep only these columns
columns = [
    "lpep_pickup_datetime",
    "lpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "passenger_count",
    "trip_distance",
    "tip_amount",
    "total_amount",
]
# Fill na values with 0
df = pd.read_parquet(url, columns=columns).fillna(0)


def ride_serializer(ride):
    ride_dict = dataclasses.asdict(ride)
    json_str = json.dumps(ride_dict)
    return json_str.encode("utf-8")


server = "localhost:9092"

producer = KafkaProducer(bootstrap_servers=[server], value_serializer=ride_serializer)
t0 = time.time()

topic_name = "green-trips"

for _, row in tqdm(df.iterrows(), total=len(df)):
    ride = ride_from_row(row, ride_type="green")
    producer.send(topic_name, value=ride)

producer.flush()

t1 = time.time()
print(f"took {(t1 - t0):.2f} seconds")
