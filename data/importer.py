import psycopg2
from psycopg2 import sql

from config.config import DatabaseConfig
from utils.logger import log
import time

def import_table_data(table, rows:list[dict], config: DatabaseConfig):
    """
    Imports data into a PostgreSQL table.

    Args:
        table (str): The name of the table to import data into.
        rows (list[dict]): List of rows to be inserted into the table, each row is a dictionary with column names as keys._
        config (DatabaseConfig): Database configuration object containing connection details.
    """
    if not rows:
        return

    conn = psycopg2.connect(**config.unpack_postgres())
    cur = conn.cursor()
    placeholders = ", ".join(["%s"] * len(rows[0]))
    insert_query = sql.SQL(f"INSERT INTO {table} VALUES ({placeholders})")
    
    for row in rows:
        try:
            cur.execute(insert_query, row)
        except Exception as e:
            log(f"Error inserting row {row} into table {table}: {e}", level="error")
            time.sleep(1)
    conn.commit()
    cur.close()
    conn.close()
