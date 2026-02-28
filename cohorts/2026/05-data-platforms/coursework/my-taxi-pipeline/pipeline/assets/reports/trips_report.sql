/* @bruin

# Docs:
# - SQL assets: https://getbruin.com/docs/bruin/assets/sql
# - Materialization: https://getbruin.com/docs/bruin/assets/materialization
# - Quality checks: https://getbruin.com/docs/bruin/quality/available_checks

# TODO: Set the asset name (recommended: reports.trips_report).
name: reports.trips_report

# TODO: Set platform type.
# Docs: https://getbruin.com/docs/bruin/assets/sql
# suggested type: duckdb.sql
type: duckdb.sql

# TODO: Declare dependency on the staging asset(s) this report reads from.
depends:
  - staging.trips

# TODO: Choose materialization strategy.
# For reports, `time_interval` is a good choice to rebuild only the relevant time window.
# Important: Use the same `incremental_key` as staging (e.g., pickup_datetime) for consistency.
materialization:
  type: table
  # suggested strategy: time_interval
  strategy: time_interval
  # TODO: set to your report's date column
  incremental_key: tpep_pickup_datetime
  # TODO: set to `date` or `timestamp`
  time_granularity: date

# TODO: Define report columns + primary key(s) at your chosen level of aggregation.
columns:
  - name: vendorid
    type: string
    description: Unique identifier for the taxi vendor
    primary_key: true
  - name: pickup_date
    type: DATE
    description: Date of pickup
    primary_key: true
  - name: passenger_count
    type: BIGINT
    description: Number of passengers in the trip
    checks:
      - name: non_negative

@bruin */

-- Purpose of reports:
-- - Aggregate staging data for dashboards and analytics
-- Required Bruin concepts:
-- - Filter using `{{ start_datetime }}` / `{{ end_datetime }}` for incremental runs
-- - GROUP BY your dimension + date columns

SELECT 
  vendorid,
  DATE(tpep_pickup_datetime) AS pickup_date,
  SUM(passenger_count) AS total_passenger_count
FROM staging.trips
WHERE tpep_pickup_datetime >= '{{ start_datetime }}'
  AND tpep_pickup_datetime < '{{ end_datetime }}'
GROUP BY vendorid, pickup_date