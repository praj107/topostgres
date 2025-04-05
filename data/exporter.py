import mysql.connector

def export_table_data(table, config):
    conn = mysql.connector.connect(**config.unpack_mysql())
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
