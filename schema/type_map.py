TYPE_MAP = {
    # Integers
    "tinyint": "SMALLINT",
    "smallint": "SMALLINT",
    "mediumint": "INTEGER",
    "int": "INTEGER",
    "integer": "INTEGER",
    "bigint": "BIGINT",

    # Floating/Decimal
    "float": "REAL",
    "double": "DOUBLE PRECISION",
    "double precision": "DOUBLE PRECISION",
    "decimal": "NUMERIC",
    "numeric": "NUMERIC",

    # Dates
    "date": "DATE",
    "datetime": "TIMESTAMP WITHOUT TIME ZONE",
    "timestamp": "TIMESTAMP WITHOUT TIME ZONE",
    "time": "TIME WITHOUT TIME ZONE",
    "year": "SMALLINT",

    # JSON
    "json": "JSONB",

    # Geometry fallback
    "geometry": "BYTEA",
    "point": "BYTEA",
    "linestring": "BYTEA",
    "polygon": "BYTEA",
    "multipoint": "BYTEA",
    "multilinestring": "BYTEA",
    "multipolygon": "BYTEA",
    "geometrycollection": "BYTEA"
}


def get_serial_type(mysql_type: str) -> str:
    mysql_type = mysql_type.lower()
    if "bigint" in mysql_type:
        return "BIGSERIAL"
    elif "smallint" in mysql_type:
        return "SMALLSERIAL"
    else:
        return "SERIAL"
