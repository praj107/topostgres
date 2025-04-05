import psycopg2

from config.config import DatabaseConfig

def create_pg_tables(schema_def: dict[str, str], config:DatabaseConfig):
    conn = psycopg2.connect(**config.unpack_postgres())
    cur = conn.cursor()
    for table_def in schema_def.values():
        cur.execute(table_def)
    conn.commit()
    cur.close()
    conn.close()
