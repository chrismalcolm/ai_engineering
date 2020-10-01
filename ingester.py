"""Script for ingesting time series data into the PostgreSQL database."""

import random
import time
from configparser import ConfigParser

import psycopg2


def generate_data(minute_range):
    """
        Randomly generate the time series metric data.

        Parameters:
        > minute_range (int) - the number of minutes the data should range over

        Returns:
        > data (zip object) - contains the iterable data
    """
    current_time = int(time.time())

    entries = zip(
        range(current_time - (60 * minute_range), current_time + 60, 60),
        random.choices([n/1000 for n in range(100000 + 1)], k=minute_range+1),
        random.choices(range(500000 + 1), k=minute_range+1)
    )

    return entries


def ingest(psql_config, data):
    """
        Ingests time series data into the PostgreSQL database.

        Parameters:
        > psql_config (dict) - mapping containing any necessary information for
            connecting to the database; e.g. host, database, username, password
        > data (iterable) - an object that can iterate through time series data;
            each element of the form (timestamp, cpu_load, concurrency)
    """
    try:
        conn = psycopg2.connect(**psql_config)
        cur = conn.cursor()

        print("timestamp | cpu_load | concurrency")
        for (timestamp, cpu_load, concurrency) in data:
            cur.execute(
                'INSERT INTO "metrics" (timestamp, cpu_load, concurrency) '
                'VALUES (%i, %f, %i);' % (timestamp, cpu_load, concurrency)
            )
            print(timestamp, cpu_load, concurrency)

        conn.commit()
        cur.close()

    except psycopg2.DatabaseError as err:
        print(err)

    finally:
        if conn is not None:
            conn.close()


def main(config_file, minute_range):
    """Time series data creation and ingestion."""

    # Get postgresql config
    config = ConfigParser()
    config.read(config_file)
    postgresql_config = dict(config.items("postgresql"))

    # Generate time series data
    time_series_data = generate_data(minute_range)

    # Ingest data into the postgresql database
    ingest(postgresql_config, time_series_data)


if __name__ == "__main__":
    main(config_file="config.ini", minute_range=5)
