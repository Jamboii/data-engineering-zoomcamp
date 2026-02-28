/* @bruin

name: staging.trips
type: duckdb.sql

depends:
  - ingestion.trips
  - ingestion.payment_lookup

materialization:
  type: table
  incremental_key: tpep_pickup_datetime
  time_granularity: date

columns:
  - name: vendorid
    type: string
    description: Unique identifier for the taxi vendor
    primary_key: true
    nullable: false
    checks:
      - name: not_null
  - name: tpep_pickup_datetime
    type: timestamp
    description: When the trip started
    primary_key: true
    nullable: false
    checks:
      - name: not_null
  - name: tpep_dropoff_datetime
    type: timestamp
    description: When the trip ended
    primary_key: true
    nullable: false
    checks:
      - name: not_null
  - name: passenger_count
    type: integer
    description: Number of passengers in the trip
    checks:
      - name: non_negative
  - name: trip_distance
    type: float
    description: Distance traveled in miles
    checks:
      - name: non_negative
  - name: fare_amount
    type: float
    description: Base fare amount in USD
    checks:
      - name: non_negative
  - name: payment_type_id
    type: integer
    description: Payment method identifier
    primary_key: true
    nullable: false
    checks:
      - name: not_null
  - name: payment_type_name
    type: string
    description: Payment method name (e.g., Credit card, Cash)
  - name: total_amount
    type: float
    description: Total fare (including taxes, tips, tolls)

custom_checks:
  - name: no_negative_fare_amount_in_staging
    description: Ensure all staged records have non-negative fare amounts
    query: |
      SELECT COUNT(*) FROM staging.trips WHERE fare_amount < 0
    value: 0

@bruin */

-- Staging layer: clean, deduplicate, and enrich raw trip data
--
-- This query:
-- 1. Deduplicates using a composite key of trip identifiers
-- 2. Joins with payment lookup to add payment type names
-- 3. Filters to the time window for incremental processing
-- 4. Handles any data quality issues from the raw ingestion layer

WITH filtered_trips AS (
  -- Filter to time window and remove invalid records
  SELECT
    VendorID,
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    passenger_count,
    trip_distance,
    RatecodeID,
    PULocationID,
    DOLocationID,
    payment_type,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    total_amount,
    extracted_at
  FROM ingestion.trips
  WHERE tpep_pickup_datetime >= '{{ start_datetime }}'
    AND tpep_pickup_datetime < '{{ end_datetime }}'
    -- Filter out obviously invalid records
    AND tpep_pickup_datetime IS NOT NULL
    AND tpep_dropoff_datetime IS NOT NULL
    AND fare_amount >= 0
),
deduplicated_trips AS (
  -- Deduplicate records based on composite key
  -- (pickup_datetime, dropoff_datetime, pickup_location_id, dropoff_location_id, fare_amount)
  -- This prevents processing duplicate records that may have been ingested multiple times
  SELECT
    VendorID,
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    passenger_count,
    trip_distance,
    RatecodeID,
    PULocationID,
    DOLocationID,
    payment_type,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    total_amount,
    extracted_at,
    ROW_NUMBER() OVER (
      PARTITION BY
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        PULocationID,
        DOLocationID,
        fare_amount
      ORDER BY extracted_at DESC
    ) as rn
  FROM filtered_trips
)

-- Enrich with payment type lookup and apply aliases
SELECT
  dt.VendorID as vendorid,
  dt.tpep_pickup_datetime,
  dt.tpep_dropoff_datetime,
  dt.passenger_count,
  dt.trip_distance,
  dt.RatecodeID,
  dt.PULocationID,
  dt.DOLocationID,
  dt.payment_type as payment_type_id,
  pl.payment_type_name,
  dt.fare_amount,
  dt.extra,
  dt.mta_tax,
  dt.tip_amount,
  dt.tolls_amount,
  dt.total_amount,
  dt.extracted_at
FROM deduplicated_trips dt
LEFT JOIN ingestion.payment_lookup pl
  ON dt.payment_type = pl.payment_type_id
WHERE dt.rn = 1
