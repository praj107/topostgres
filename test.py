import unittest
from config.config import MYSQL, POSTGRES
from schema.extractor import get_mysql_tables, _get_mysql_tables_raw
from schema.translator import _translate_table, translate_schema
from data.exporter import export_table_data
from data.importer import import_table_data
import mysql.connector
import psycopg2

# Normalize SQL function to remove leading/trailing spaces on each line and strip overall
def _normalize_sql(sql: str) -> str:
    # Remove leading/trailing spaces on each line and strip overall
    lines = [line.strip() for line in sql.strip().splitlines()]
    return "\n".join(lines)

class TestMigration(unittest.TestCase):
    # Test Parameters:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None  # Show full diff on failure


    def test_mysql_connection(self):
        try:
            conn = mysql.connector.connect(**MYSQL.unpack_mysql())
            self.assertTrue(conn.is_connected())
            conn.close()
        except Exception as e:
            self.fail(f"MySQL connection failed: {e}")

    def test_mysql_constraint_conversion(self):
        # Test the SQL to SQL conversion for a specific table, starting with the MySQL 8 table as input
        with open("tests\\test_mysql_table_constraint_0.sql", "r") as f:
            sql_in = f.read()
        
        # Get the expected Postgres to compare against:
        with open("tests\\test_postgres_table_constraint_0.sql", "r") as f:
            sql_out = f.read()
        
        # Translate the MySQL table to PostgreSQL:
        actual_sql_out = _translate_table(sql_in)
        # Compare the actual output with the expected output:
        # print(f"Actual SQL:\n[{_normalize_sql(actual_sql_out)}]")
        self.assertEqual(_normalize_sql(actual_sql_out), _normalize_sql(sql_out), f"MySQL to PostgreSQL table translation failed.")

    def test_postgres_connection(self):
        try:
            conn = psycopg2.connect(**POSTGRES.unpack_postgres())
            conn.close()
        except Exception as e:
            self.fail(f"PostgreSQL connection failed: {e}")

        

    def test_mysql_to_postgres_table_1_strict(self):
        # Test the SQL to SQL conversion for a specific table, starting with the MySQL 8 table as input
        with open("tests\\test_mysql_table_0.sql", "r") as f:
            sql_in = f.read()
        
        # Get the expected Postgres to compare against:
        with open("tests\\test_postgres_table_0_strict.sql", "r") as f:
            sql_out = f.read()

        # Translate the MySQL table to PostgreSQL:
        actual_sql_out = _translate_table(sql_in)
        # Compare the actual output with the expected output:
        self.assertEqual(_normalize_sql(actual_sql_out), _normalize_sql(sql_out), f"MySQL to PostgreSQL table translation failed.")

    def test_mysql_unique_fk_test_1(self):
        # Test the SQL to SQL conversion for a specific table, starting with the MySQL 8 table as input
        with open("tests\\test_mysql_table_fk_0.sql", "r") as f:
            sql_in = f.read()
        
        # Get the expected Postgres to compare against:
        with open("tests\\test_postgres_table_fk_0.sql", "r") as f:
            sql_out = f.read()
        
        # Translate the MySQL table to PostgreSQL:
        tables_dict = translate_schema(_get_mysql_tables_raw(sql_in))
        actual_sql_out = "\n".join(tables_dict.values())
        # Compare the actual output with the expected output:
        # print(f"Actual SQL:\n[{_normalize_sql(actual_sql_out)}]")
        self.assertEqual(_normalize_sql(actual_sql_out), _normalize_sql(sql_out), f"Foriegn keys must have references to solely unique keys. Composite Unique or Primary keys refrenced do not count.")
if __name__ == "__main__":
    unittest.main()
