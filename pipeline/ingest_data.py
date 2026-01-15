import pandas as pd
from sqlalchemy import create_engine
from tqdm import tqdm
import click

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
@click.option("--pg-user", default="root", help="PostgreSQL username")
@click.option("--pg-pass", default="root", help="PostgreSQL password")
@click.option("--pg-host", default="localhost", help="PostgreSQL host")
@click.option("--pg-port", default="5432", help="PostgreSQL port")
@click.option("--pg-db", default="ny_taxi", help="PostgreSQL database name")
@click.option(
    "--target-table", default="yellow_taxi_data", help="Table name to insert into"
)
@click.option("--year", default=2021, help="Year of data")
@click.option("--month", default=1, help="Month of data")
@click.option("--chunksize", default=100000, help="Chunk size for ingestion")
def main(
    pg_user, pg_pass, pg_host, pg_port, pg_db, target_table, year, month, chunksize
):
    url = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_{year:04d}-{month:02d}.csv.gz"

    print(f"Downloading: {url}")

    engine = create_engine(
        f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    )

    df_iter = pd.read_csv(
        url, dtype=dtype, parse_dates=parse_dates, iterator=True, chunksize=chunksize
    )

    first_chunk = next(df_iter)

    # create table
    first_chunk.head(0).to_sql(name=target_table, con=engine, if_exists="replace")
    print(f"Table {target_table} created.")

    # insert first chunk
    first_chunk.to_sql(name=target_table, con=engine, if_exists="append")
    print(f"Inserted first chunk: {len(first_chunk)} rows")

    for chunk in tqdm(df_iter, desc="Ingesting"):
        chunk.to_sql(name=target_table, con=engine, if_exists="append")
        print(f"Inserted chunk: {len(chunk)} rows")

    print(f"Done. Data ingested into table {target_table}")


if __name__ == "__main__":
    main()
