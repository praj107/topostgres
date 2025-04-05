import psycopg2
from psycopg2 import sql

from config.config import DatabaseConfig
from utils.logger import log
import time


def import_table_data(table: str, rows: list[tuple], config: DatabaseConfig):
    """
    Imports data into a PostgreSQL table.

    Args:
        table (str): The name of the table to import data into.
        rows (list[tuple]): List of rows to be inserted into the table, each row is a tuple of values.
        config (DatabaseConfig): Database configuration object containing connection details.
    """
    if not rows:
        log(f"No data to import for table {table}.", level="warn")
        return

    conn = psycopg2.connect(**config.unpack_postgres())
    cur = conn.cursor()

    # Infer column count from first row
    column_count = len(rows[0])
    placeholders = sql.SQL(', ').join(sql.Placeholder() for _ in range(column_count))

    insert_query = sql.SQL("INSERT INTO {table} VALUES ({values})").format(
        table=sql.Identifier(table),
        values=placeholders
    )

    failures = 0
    successes = 0
    total_rows = len(rows)
    start_time = time.time()

    for idx, row in enumerate(rows, 1):
        try:
            cur.execute(insert_query, row)
            successes += 1
        except Exception as e:
            log(f"[{table}] Failed row {idx}/{total_rows}: {e}", level="error")
            failures += 1

        if idx % 500 == 0:
            conn.commit()
            log(f"[{table}] Inserted {idx}/{total_rows} rows...", level="info")

    conn.commit()
    cur.close()
    conn.close()

    elapsed = round(time.time() - start_time, 2)
    log(f"[{table}] ✅ Imported {successes}/{total_rows} rows in {elapsed}s (Failures: {failures})", level="success" if failures == 0 else "warn")
