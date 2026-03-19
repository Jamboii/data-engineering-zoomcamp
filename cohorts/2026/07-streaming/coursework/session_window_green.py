from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import EnvironmentSettings, StreamTableEnvironment


def create_events_aggregated_sink(t_env):
    """Sink schema:

    CREATE TABLE processed_events_sessions (
        window_start TIMESTAMP(3),
        window_end TIMESTAMP(3),
        PULocationID INT,
        num_trips BIGINT,
        PRIMARY KEY (window_start, window_end, PULocationID)
    );
    """
    table_name = "processed_events_sessions"
    sink_ddl = f"""
        CREATE TABLE {table_name} (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            PULocationID INT,
            num_trips BIGINT,
            PRIMARY KEY (window_start, window_end, PULocationID) NOT ENFORCED
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://postgres:5432/postgres',
            'table-name' = '{table_name}',
            'username' = 'postgres',
            'password' = 'postgres',
            'driver' = 'org.postgresql.Driver'
        );
        """
    t_env.execute_sql(sink_ddl)
    return table_name


def create_events_source_kafka(t_env):
    """
    Green Trips source schema:

    lpep_pickup_datetime: str # in format 'yyyy-MM-dd HH:mm:ss'
    lpep_dropoff_datetime: str # in format 'yyyy-MM-dd HH:mm:ss'
    PULocationID: int
    DOLocationID: int
    passenger_count: int
    trip_distance: float
    tip_amount: float
    total_amount: float
    """
    table_name = "events"
    source_ddl = f"""
        CREATE TABLE {table_name} (
            lpep_pickup_datetime VARCHAR,
            lpep_dropoff_datetime VARCHAR,
            PULocationID INTEGER,
            DOLocationID INTEGER,
            passenger_count INTEGER,
            trip_distance DOUBLE,
            tip_amount DOUBLE,
            total_amount DOUBLE,
            event_timestamp AS TO_TIMESTAMP(lpep_pickup_datetime, 'yyyy-MM-dd HH:mm:ss'),
            WATERMARK for event_timestamp as event_timestamp - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'properties.bootstrap.servers' = 'redpanda:29092',
            'topic' = 'green-trips',
            'scan.startup.mode' = 'latest-offset',
            'properties.auto.offset.reset' = 'latest',
            'format' = 'json'
        );
        """
    t_env.execute_sql(source_ddl)
    return table_name


def log_aggregation():
    # Set up the execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(10 * 1000)
    env.set_parallelism(1)  # green trips has 1 partition

    # Set up the table environment
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    try:
        # Create Kafka table
        source_table = create_events_source_kafka(t_env)
        aggregated_table = create_events_aggregated_sink(t_env)

        t_env.execute_sql(f"""
        INSERT INTO {aggregated_table}
        SELECT
            window_start,
            window_end,
            PULocationID,
            COUNT(*) AS num_trips
        FROM TABLE(
            SESSION(
                TABLE {source_table},
                DESCRIPTOR(event_timestamp),
                INTERVAL '5' MINUTE
            )
        )
        GROUP BY window_start, window_end, PULocationID;
        """).wait()

        # t_env.execute_sql(f"""
        # INSERT INTO {aggregated_table}
        # SELECT
        #     SESSION_START(event_timestamp, INTERVAL '5' MINUTES) AS window_start,
        #     SESSION_ROWTIME(event_timestamp, INTERVAL '5' MINUTES) AS window_end,
        #     PULocationID,
        #     COUNT(*) AS num_trips
        # FROM {source_table}
        # GROUP BY PULocationID, SESSION(event_timestamp, INTERVAL '5' MINUTES);
        # """).wait()

    except Exception as e:
        print("Writing records from Kafka to JDBC failed:", str(e))


if __name__ == "__main__":
    log_aggregation()
