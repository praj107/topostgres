from schema.extractor import get_mysql_tables
from schema.translator import translate_schema
from schema.creator import create_pg_tables
from data.exporter import export_table_data
from data.importer import import_table_data
from utils.logger import log
from config.config import MYSQL, POSTGRES

# TESTING COMMAND(S)
# python -m unittest tests/test.py


def migrate_schema():
    log("Extracting schema from MySQL...", "info")
    tables = get_mysql_tables(MYSQL)
    log(f"Fetched {len(tables)} tables from MySQL.", "info")
    [print(f"===[MYSQL 8 version {x} ]===\n{tables[x]}\n===[ ------- ]===") for x in tables.keys()]
    log("Translating schema to PostgreSQL...", "info")
    translated = translate_schema(tables)
    [print(f"===[POSTGRES version {x} ]===\n{translated[x]}\n===[ ------- ]===") for x in translated.keys()]
    log(f"Translated {len(translated)} tables to PostgreSQL.", "info")
    log("Creating PostgreSQL tables...", "info")
    create_pg_tables(translated, POSTGRES)
    log("✅ Schema migration complete.", "success")

def migrate_data():
    tables = get_mysql_tables(MYSQL)
    for table in tables:
        log(f"Migrating data: {table}", "info")
        rows = export_table_data(table, MYSQL)
        import_table_data(table, rows, POSTGRES)

def main():
    # migrate_schema()
    migrate_data()

if __name__ == "__main__":
    main()
