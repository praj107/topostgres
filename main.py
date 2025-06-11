import re
from sqlalchemy.engine import URL
from schema.extractor import get_mysql_tables
from schema.translator import translate_schema
from schema.creator import create_pg_tables
from data.exporter import export_table_data
from data.importer import import_table_data
from utils.logger import log
from config.config import MYSQL, POSTGRES

# TESTING COMMAND(S)
# python -m unittest tests/test.py

# Utils functions:
TABLE_NAME_SKIPLIST = [

]
def count_columns(create_stmt: str) -> int:
    """
    Counts column definitions based on how many ',\n' or ', [whitespace]\n' occur.
    Assumes standard formatting where each column ends with a comma,
    and the last one does not.
    """
    # Count commas at end of lines (ignores constraints like PRIMARY KEY which may also end in commas)
    match = re.search(r"\((.*)\)", create_stmt, flags=re.DOTALL)
    if not match:
        return 0

    body = match.group(1)
    comma_lines = len(re.findall(r",\s*\n", body))
    return comma_lines + 1  # +1 for the last column

# Migration functions:
def migrate_schema():
    log("Translating schema to PostgreSQL via SQLAlchemy reflection...", "info")
    url = URL.create(
        "mysql+mysqlconnector",
        username=MYSQL.user,
        password=MYSQL.password,
        host=MYSQL.host,
        port=MYSQL.port,
        database=MYSQL.database,
    )
    translated = translate_schema(str(url))
    [print(f"===[POSTGRES version {x} ]===\n{translated[x]}\n===[ ------- ]===") for x in translated.keys()]
    log(
        f"Translated {len(translated)} tables [~{sum([count_columns(x) for x in translated.values()])} columns total] to PostgreSQL.",
        "info",
    )
    log("Creating PostgreSQL tables...", "info")
    create_pg_tables(translated, POSTGRES)

    
    log("✅ Schema migration complete.", "success")

def migrate_data():
    tables = [x for x in get_mysql_tables(MYSQL) if x not in TABLE_NAME_SKIPLIST]
    log(f"Skipping tables: {TABLE_NAME_SKIPLIST}", "info")
    for table in tables:
        log(f"Migrating data: {table}", "info")
        rows = export_table_data(table, MYSQL)
        import_table_data(table, rows, POSTGRES)

def main():
    migrate_schema()
    migrate_data()

if __name__ == "__main__":
    main()
