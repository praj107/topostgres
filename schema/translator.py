from __future__ import annotations

from typing import Dict, List, Tuple

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    CheckConstraint,
    UniqueConstraint,
    ForeignKeyConstraint,
    Integer,
    SmallInteger,
    BigInteger,
    Numeric,
    Float,
    REAL,
    Date,
    Text,
    LargeBinary,
    CHAR,
    VARCHAR,
)
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.schema import CreateTable
from sqlalchemy import create_engine

from .type_map import TYPE_MAP, get_serial_type

# Mapping from PostgreSQL type names used in TYPE_MAP to SQLAlchemy types
_PG_TYPE_MAP = {
    "SMALLINT": SmallInteger,
    "INTEGER": Integer,
    "BIGINT": BigInteger,
    "REAL": REAL,
    "DOUBLE PRECISION": postgresql.DOUBLE_PRECISION,
    "NUMERIC": Numeric,
    "DATE": Date,
    "TIMESTAMP WITHOUT TIME ZONE": postgresql.TIMESTAMP,
    "TIME WITHOUT TIME ZONE": postgresql.TIME,
    "JSONB": postgresql.JSONB,
    "BYTEA": LargeBinary,
    "CHAR": CHAR,
    "VARCHAR": VARCHAR,
    "TEXT": Text,
    "BIT": postgresql.BIT,
}


def _map_mysql_type(col: Column) -> Tuple[Column, List[CheckConstraint]]:
    """Convert a reflected MySQL column to a PostgreSQL SQLAlchemy Column."""
    constraints: List[CheckConstraint] = []
    mysql_type = col.type
    name = col.name

    # ENUM
    if isinstance(mysql_type, mysql.ENUM):
        values = ", ".join(f"'{v}'" for v in mysql_type.enums)
        pg_col = Column(name, Text, nullable=col.nullable, primary_key=col.primary_key)
        constraints.append(CheckConstraint(f"{name} IN ({values})"))
        return pg_col, constraints

    # SET
    if isinstance(mysql_type, mysql.SET):
        values = ",".join(f"'{v}'" for v in mysql_type.values)
        pg_col = Column(name, postgresql.ARRAY(Text), nullable=col.nullable, primary_key=col.primary_key)
        constraints.append(CheckConstraint(f"{name} <@ ARRAY[{values}]"))
        return pg_col, constraints

    base = mysql_type.__class__.__name__.lower()
    mapped_name = TYPE_MAP.get(base, "TEXT")
    pg_type_cls = _PG_TYPE_MAP.get(mapped_name, Text)

    if mapped_name in ("CHAR", "VARCHAR"):
        length = getattr(mysql_type, "length", None)
        pg_type = pg_type_cls(length)
    elif mapped_name == "BIT":
        length = getattr(mysql_type, "length", None)
        pg_type = pg_type_cls(length)
    elif mapped_name == "NUMERIC":
        precision = getattr(mysql_type, "precision", None)
        scale = getattr(mysql_type, "scale", None)
        if precision is not None:
            pg_type = pg_type_cls(precision, scale)
        else:
            pg_type = pg_type_cls()
    else:
        pg_type = pg_type_cls()

    autoinc = getattr(col, "autoincrement", False)
    if autoinc and base in (
        "tinyint",
        "smallint",
        "mediumint",
        "int",
        "integer",
        "bigint",
    ):
        serial_name = get_serial_type(base)
        serial_cls = getattr(postgresql, serial_name)
        pg_col = Column(name, serial_cls, primary_key=col.primary_key)
    else:
        pg_col = Column(name, pg_type, nullable=col.nullable, primary_key=col.primary_key)

    default = getattr(col, "default", None) or getattr(col, "server_default", None)
    if default is not None:
        pg_col.server_default = default

    return pg_col, constraints


def translate_schema(mysql_url: str) -> Dict[str, str]:
    """Reflect tables from a MySQL database and generate PostgreSQL DDL."""
    engine = create_engine(mysql_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    compiled: Dict[str, str] = {}

    for table in metadata.sorted_tables:
        pg_meta = MetaData()
        pg_columns: List[Column] = []
        pg_constraints = []

        for col in table.columns:
            new_col, extra = _map_mysql_type(col)
            pg_columns.append(new_col)
            pg_constraints.extend(extra)

        for cons in table.constraints:
            if isinstance(cons, UniqueConstraint):
                pg_constraints.append(UniqueConstraint(*[c.name for c in cons.columns]))
            elif isinstance(cons, ForeignKeyConstraint):
                local_cols = [elem.parent.name for elem in cons.elements]
                remote_cols = [f"{elem.column.table.name}.{elem.column.name}" for elem in cons.elements]
                pg_constraints.append(ForeignKeyConstraint(local_cols, remote_cols))

        for idx in table.indexes:
            if idx.unique:
                pg_constraints.append(UniqueConstraint(*[c.name for c in idx.columns]))

        pg_table = Table(table.name, pg_meta, *pg_columns, *pg_constraints)
        ddl = str(CreateTable(pg_table).compile(dialect=postgresql.dialect()))
        compiled[table.name] = ddl

    engine.dispose()
    return compiled
