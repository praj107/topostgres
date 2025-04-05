import mysql.connector

from config.config import DatabaseConfig

def get_mysql_tables(config: DatabaseConfig) -> list[str]:
    """
    Get all tables from a MySQL database.
    This function connects to a MySQL database using the provided configuration and retrieves a list of all tables in the database,
    in the form of a list of strings representing their respective creation SQL statements.

    Args:
        config (_type_): _description_

    Returns:
        list[str]: _description_
    """
    # Connect to MySQL database and setup cursor:
    conn = mysql.connector.connect(**config.unpack_mysql())
    cursor = conn.cursor()

    # Get the list of tables in the database:
    cursor.execute("SHOW TABLES;")
    table_names = [row[0] for row in cursor.fetchall()]
    tables = {}
    for name in table_names:
        cursor.execute(f"SHOW CREATE TABLE `{name}`;")
        create_statement = cursor.fetchone()[1]
        tables[name] = create_statement.replace("`", "")  # Remove backticks for compatibility
    # Close the cursor and connection:
    # [print(f"===[ {x} ]===\n{tables[x]}\n===[ ------- ]===") for x in tables.keys()]
    cursor.close()
    conn.close()
    return tables
