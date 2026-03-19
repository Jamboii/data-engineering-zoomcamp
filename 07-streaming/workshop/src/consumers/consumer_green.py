import sys
from datetime import datetime
from pathlib import Path
from functools import partial

sys.path.insert(0, str(Path(__file__).parent.parent))

from kafka import KafkaConsumer
from models import ride_deserializer

server = "localhost:9092"
topic_name = "green-trips"

consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=[server],
    auto_offset_reset="earliest",
    group_id="rides-console",
    value_deserializer=partial(ride_deserializer, ride_type="green"),
)

print(f"Listening to {topic_name}...")

count = 0
for message in consumer:
    ride = message.value
    pickup_dt = datetime.fromtimestamp(ride.lpep_pickup_datetime / 1000)
    print(
        f"Received: PU={ride.PULocationID}, DO={ride.DOLocationID}, "
        f"distance={ride.trip_distance}, amount=${ride.total_amount:.2f}, "
        f"pickup={pickup_dt}"
    )
    # Count how many rides have a trip distance > 5 km
    if ride.trip_distance > 5:
        count += 1
        print(f"  --> Trip distance > 5: {ride.trip_distance}")
    print(f"Total rides with distance > 5: {count}")

consumer.close()
