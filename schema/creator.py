import psycopg2

from config.config import DatabaseConfig
from utils.logger import log

def create_pg_tables(schema_def: dict[str, str], config:DatabaseConfig):
    conn = psycopg2.connect(**config.unpack_postgres())
    cur = conn.cursor()
    for table_def in schema_def.values():
        try:
            cur.execute(table_def)
        except psycopg2.errors.DuplicateTable:
            log(f"Table already exists, skipping: {table_def}", level="warn")
            conn.rollback()
    conn.commit()
    cur.close()
    conn.close()
