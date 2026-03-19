import json
from dataclasses import dataclass


@dataclass
class YellowRide:
    PULocationID: int
    DOLocationID: int
    trip_distance: float
    total_amount: float
    tpep_pickup_datetime: int  # epoch milliseconds


@dataclass
class GreenRide:
    lpep_pickup_datetime: str
    lpep_dropoff_datetime: str
    PULocationID: int
    DOLocationID: int
    passenger_count: int
    trip_distance: float
    tip_amount: float
    total_amount: float


def yellow_ride_from_row(row):
    return YellowRide(
        PULocationID=int(row["PULocationID"]),
        DOLocationID=int(row["DOLocationID"]),
        trip_distance=float(row["trip_distance"]),
        total_amount=float(row["total_amount"]),
        tpep_pickup_datetime=int(row["tpep_pickup_datetime"].timestamp() * 1000),
    )


def ride_from_row(row, ride_type="yellow"):
    if ride_type == "yellow":
        return YellowRide(
            PULocationID=int(row["PULocationID"]),
            DOLocationID=int(row["DOLocationID"]),
            trip_distance=float(row["trip_distance"]),
            total_amount=float(row["total_amount"]),
            tpep_pickup_datetime=int(row["tpep_pickup_datetime"].timestamp() * 1000),
        )
    elif ride_type == "green":
        return GreenRide(
            lpep_pickup_datetime=str(row["lpep_pickup_datetime"]),
            lpep_dropoff_datetime=str(row["lpep_dropoff_datetime"]),
            PULocationID=int(row["PULocationID"]),
            DOLocationID=int(row["DOLocationID"]),
            passenger_count=int(row["passenger_count"]),
            trip_distance=float(row["trip_distance"]),
            tip_amount=float(row["tip_amount"]),
            total_amount=float(row["total_amount"]),
        )


def ride_deserializer(data, ride_type="yellow"):
    json_str = data.decode("utf-8")
    ride_dict = json.loads(json_str)
    if ride_type == "yellow":
        return YellowRide(**ride_dict)
    elif ride_type == "green":
        return GreenRide(**ride_dict)
