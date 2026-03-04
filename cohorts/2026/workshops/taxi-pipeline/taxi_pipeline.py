"""Template for building a `dlt` pipeline to ingest data from a REST API."""

import dlt
from dlt.sources.helpers.rest_client.client import RESTClient

taxi_client = RESTClient(
    base_url="https://us-central1-dlthub-analytics.cloudfunctions.net/data_engineering_zoomcamp_api",
)


@dlt.resource
def nyc_taxi():
    page = 1
    while True:
        response = taxi_client.get("", params={"page": page})
        if not response.json():
            break
        yield response.json()
        page += 1


pipeline = dlt.pipeline(
    pipeline_name="taxi_pipeline",
    destination="duckdb",
    dataset_name="taxi_data",
    progress="log",
)


if __name__ == "__main__":
    load_info = pipeline.run(nyc_taxi())
    print(load_info)  # noqa: T201
