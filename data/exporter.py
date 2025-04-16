import mysql.connector

from utils.logger import log

def export_table_data(table, config):
    conn = mysql.connector.connect(**config.unpack_mysql())
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    if not rows:
        log(f"No data found in table {table}.", level="warn")
        log(f"Query: SELECT * FROM {table}", level="info")
    return rows
