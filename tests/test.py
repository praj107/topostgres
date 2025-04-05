import unittest
from config.config import MYSQL, POSTGRES
from schema.extractor import get_mysql_tables
from schema.translator import _translate_table
from data.exporter import export_table_data
from data.importer import import_table_data
import mysql.connector
import psycopg2


class TestMigration(unittest.TestCase):
    # Test Parameters:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None  # Show full diff on failure


    def test_mysql_connection(self):
        try:
            conn = mysql.connector.connect(**MYSQL)
            self.assertTrue(conn.is_connected())
            conn.close()
        except Exception as e:
            self.fail(f"MySQL connection failed: {e}")

    def test_postgres_connection(self):
        try:
            conn = psycopg2.connect(**POSTGRES)
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
        self.assertEqual(actual_sql_out, sql_out, f"MySQL to PostgreSQL table translation failed.")
        
    # def test_get_mysql_tables(self):
    #     tables = get_mysql_tables(MYSQL)
    #     self.assertIsInstance(tables, list)
    #     self.assertGreater(len(tables), 0, "No tables found in MySQL")

    # def test_export_import_cycle(self):
    #     table = get_mysql_tables(MYSQL)[0]
    #     rows = export_table_data(table, MYSQL)
    #     self.assertIsInstance(rows, list)
    #     import_table_data(table, rows, POSTGRES)
    #     self.assertTrue(True, "Import successful (no exceptions)")


if __name__ == "__main__":
    unittest.main()
