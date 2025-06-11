import os
import unittest

from sqlalchemy.engine import URL

from config.config import MYSQL, POSTGRES
from schema.translator import translate_schema

import mysql.connector
import psycopg2


def _normalize_sql(sql: str) -> str:
    lines = [line.strip() for line in sql.strip().splitlines()]
    return "\n".join(lines)


class TestMigration(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_mysql_connection(self):
        try:
            conn = mysql.connector.connect(**MYSQL.unpack_mysql())
            self.assertTrue(conn.is_connected())
            conn.close()
        except Exception as e:
            self.fail(f"MySQL connection failed: {e}")

    def test_postgres_connection(self):
        try:
            conn = psycopg2.connect(**POSTGRES.unpack_postgres())
            conn.close()
        except Exception as e:
            self.fail(f"PostgreSQL connection failed: {e}")

    def test_schema_translation_complex_table(self):
        url = URL.create(
            "mysql+mysqlconnector",
            username=MYSQL.user,
            password=MYSQL.password,
            host=MYSQL.host,
            port=MYSQL.port,
            database=MYSQL.database,
        )
        translated = translate_schema(str(url))
        with open(os.path.join("tests", "test_postgres_table_0_strict.sql")) as f:
            expected = f.read()
        self.assertIn("complex_table", translated)
        self.assertEqual(
            _normalize_sql(translated["complex_table"]),
            _normalize_sql(expected),
        )


if __name__ == "__main__":
    unittest.main()
