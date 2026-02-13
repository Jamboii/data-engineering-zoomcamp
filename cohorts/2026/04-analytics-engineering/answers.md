# Module 4 Homework: Analytics Engineering with dbt

In this homework, we'll use the dbt project in `04-analytics-engineering/taxi_rides_ny/` to transform NYC taxi data and answer questions by querying the models.

## Setup

1. Set up your dbt project following the [setup guide](../../../04-analytics-engineering/setup/)
2. Load the Green and Yellow taxi data for 2019-2020 into your warehouse
3. Run `dbt build --target prod` to create all models and run tests

> **Note:** By default, dbt uses the `dev` target. You must use `--target prod` to build the models in the production dataset, which is required for the homework queries below.

After a successful build, you should have models like `fct_trips`, `dim_zones`, and `fct_monthly_zone_revenue` in your warehouse.

---

### Question 1. dbt Lineage and Execution

Given a dbt project with the following structure:

```
models/
├── staging/
│   ├── stg_green_tripdata.sql
│   └── stg_yellow_tripdata.sql
└── intermediate/
    └── int_trips_unioned.sql (depends on stg_green_tripdata & stg_yellow_tripdata)
```

If you run `dbt run --select int_trips_unioned`, what models will be built?

- `stg_green_tripdata`, `stg_yellow_tripdata`, and `int_trips_unioned` (upstream dependencies)
- Any model with upstream and downstream dependencies to `int_trips_unioned`
- **`int_trips_unioned` only**
- `int_trips_unioned`, `int_trips`, and `fct_trips` (downstream dependencies)

#### explanation

```zsh
$ dbt run --select int_trips_unioned
03:37:12  Running with dbt=1.10.19
03:37:12  Registered adapter: duckdb=1.10.0
03:37:12  Unable to do partial parsing because config vars, config profile, or config target have changed
03:37:12  Unable to do partial parsing because profile has changed
03:37:13  Found 8 models, 2 seeds, 33 data tests, 2 sources, 618 macros
03:37:14  
03:37:14  Concurrency: 1 threads (target='dev')
03:37:14  
03:37:14  1 of 1 START sql table model dev.int_trips_unioned ............................. [RUN]
03:37:16  1 of 1 OK created sql table model dev.int_trips_unioned ........................ [OK in 1.94s]
03:37:16  
03:37:16  Finished running 1 table model in 0 hours 0 minutes and 2.02 seconds (2.02s).
03:37:16  
03:37:16  Completed successfully
03:37:16  
03:37:16  Done. PASS=1 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=1
```

---

### Question 2. dbt Tests

You've configured a generic test like this in your `schema.yml`:

```yaml
columns:
  - name: payment_type
    data_tests:
      - accepted_values:
          arguments:
            values: [1, 2, 3, 4, 5]
            quote: false
```

Your model `fct_trips` has been running successfully for months. A new value `6` now appears in the source data.

What happens when you run `dbt test --select fct_trips`?

- dbt will skip the test because the model didn't change
- **dbt will fail the test, returning a non-zero exit code**
- dbt will pass the test with a warning about the new value
- dbt will update the configuration to include the new value

---

### Question 3. Counting Records in `fct_monthly_zone_revenue`

After running your dbt project, query the `fct_monthly_zone_revenue` model.

What is the count of records in the `fct_monthly_zone_revenue` model?

- 12,998
- 14,120
- **12,184**
- 15,421

#### explanation

```python
import ibis
ibis.options.interactive = True
con = ibis.duckdb.connect("taxi_rides_ny/taxi_rides_ny.duckdb")
zr = con.table("fct_monthly_zone_revenue", database="prod")
zr.count()
┌───────┐
│ 12184 │
└───────┘
```

---

### Question 4. Best Performing Zone for Green Taxis (2020)

Using the `fct_monthly_zone_revenue` table, find the pickup zone with the **highest total revenue** (`revenue_monthly_total_amount`) for **Green** taxi trips in 2020.

Which zone had the highest revenue?

- **East Harlem North**
- Morningside Heights
- East Harlem South
- Washington Heights South

#### explanation

```python
import ibis
ibis.options.interactive = True
con = ibis.duckdb.connect("taxi_rides_ny/taxi_rides_ny.duckdb")
con.sql(
    """
    SELECT pickup_zone, revenue_month, revenue_monthly_total_amount
    FROM prod.fct_monthly_zone_revenue
    WHERE service_type = 'Green' and year(revenue_month) = '2020'
    ORDER BY revenue_monthly_total_amount DESC
    """
)
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ pickup_zone       ┃ revenue_month ┃ revenue_monthly_total_amount ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ string            │ date          │ decimal(38, 3)               │
├───────────────────┼───────────────┼──────────────────────────────┤
│ East Harlem North │ 2020-01-01    │                   434597.360 │
└───────────────────┴───────────────┴──────────────────────────────┘
```

---

### Question 5. Green Taxi Trip Counts (October 2019)

Using the `fct_monthly_zone_revenue` table, what is the **total number of trips** (`total_monthly_trips`) for Green taxis in October 2019?

- 500,234
- 350,891
- **384,624**
- 421,509

#### explanation

```python
import ibis
ibis.options.interactive = True
con = ibis.duckdb.connect("taxi_rides_ny/taxi_rides_ny.duckdb")
con.sql(
    """
    SELECT sum(total_monthly_trips) as total_trips
    FROM prod.fct_monthly_zone_revenue
    WHERE service_type = 'Green' 
        AND year(revenue_month) = '2019' 
        AND month(revenue_month) = '10'
    """
)
┏━━━━━━━━━━━━━━━━┓
┃ total_trips    ┃
┡━━━━━━━━━━━━━━━━┩
│ decimal(38, 0) │
├────────────────┤
│         384624 │
└────────────────┘
```

---

### Question 6. Build a Staging Model for FHV Data

Create a staging model for the **For-Hire Vehicle (FHV)** trip data for 2019.

1. Load the [FHV trip data for 2019](https://github.com/DataTalksClub/nyc-tlc-data/releases/tag/fhv) into your data warehouse
2. Create a staging model `stg_fhv_tripdata` with these requirements:
   - Filter out records where `dispatching_base_num IS NULL`
   - Rename fields to match your project's naming conventions (e.g., `PUlocationID` → `pickup_location_id`)

What is the count of records in `stg_fhv_tripdata`?

- 42,084,899
- **43,244,693**
- 22,998,722
- 44,112,187

#### explanation

```python
import ibis
ibis.options.interactive = True
fhv = con.table("stg_fhv_tripdata", database="prod")
fhv.count()
┌──────────┐
│ 43244693 │
└──────────┘
```

---

## Submitting the solutions

- Form for submitting: <https://courses.datatalks.club/de-zoomcamp-2026/homework/hw4>

=======

## Learning in Public

We encourage everyone to share what they learned. This is called "learning in public".

Read more about the benefits [here](https://alexeyondata.substack.com/p/benefits-of-learning-in-public-and).

### Example post for LinkedIn

```
🚀 Week 4 of Data Engineering Zoomcamp by @DataTalksClub complete!

Just finished Module 4 - Analytics Engineering with dbt. Learned how to:

✅ Build transformation models with dbt
✅ Create staging, intermediate, and fact tables
✅ Write tests to ensure data quality
✅ Understand lineage and model dependencies
✅ Analyze revenue patterns across NYC zones

Transforming raw data into analytics-ready models - the T in ELT!

Here's my homework solution: <LINK>

Following along with this amazing free course - who else is learning data engineering?

You can sign up here: https://github.com/DataTalksClub/data-engineering-zoomcamp/
```

### Example post for Twitter/X

```
📈 Module 4 of Data Engineering Zoomcamp done!

- Analytics Engineering with dbt
- Transformation models & tests
- Data lineage & dependencies
- NYC taxi revenue analysis

My solution: <LINK>

Free course by @DataTalksClub: https://github.com/DataTalksClub/data-engineering-zoomcamp/
```
