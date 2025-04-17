import mysql.connector
import re
from typing import Dict, List
from config.config import DatabaseConfig

def get_mysql_tables(config: DatabaseConfig) -> list[str]:
    """
    Get all tables from a MySQL database.
    This function connects to a MySQL database using the provided configuration and retrieves a list of all tables in the database,
    in the form of a list of strings representing their respective creation SQL statements.

    Args:
        config (DatabaseConfig): Config object for the database connection.

    Returns:
        list[str]: The list of tables in the database, each represented by its creation SQL statement.
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


def _get_mysql_tables_raw(sql: str) -> dict[str, str]:
    """
    Extracts all table creation SQL statements from a MySQL script.

    Args:
        sql (str): The full SQL script.

    Returns:
        dict[str, str]: Mapping of table names to their CREATE TABLE SQL statements.
    """
    tables = {}

    # Regex to match CREATE TABLE statements properly
    pattern = re.compile(
        r'(CREATE\s+TABLE\s+`?(\w+)`?\s*\(.*?)(?=(?:CREATE\s+TABLE|$))',
        re.IGNORECASE | re.DOTALL
    )

    for match in pattern.finditer(sql):
        full_statement = match.group(1).strip()
        table_name = match.group(2)
        tables[table_name] = full_statement

    return tables

