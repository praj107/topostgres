import re
from typing import List
from .type_map import TYPE_MAP, get_serial_type


def translate_schema(tables: dict[str, str]) -> dict[str, str]:
    return {x: _translate_table(tables[x]) for x in tables.keys()}


def _translate_table(mysql_sql: str) -> str:
    mysql_sql = mysql_sql.strip().rstrip(";")

    match = re.match(r"CREATE TABLE `?(\w+)`?\s*\((.*)\)\s*(.*)", mysql_sql, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError("Invalid CREATE TABLE syntax.")

    table_name, body, suffix = match.groups()
    lines = _split_sql_lines(body)

    pg_lines = []
    for line in lines:
        line = line.strip().rstrip(",")
        if not line:
            continue

        # Skip generated columns completely
        if "GENERATED ALWAYS AS" in line.upper():
            continue

        if any(line.upper().startswith(x) for x in ("KEY ", "UNIQUE KEY ", "FULLTEXT KEY", "SPATIAL KEY", "PRIMARY KEY")):
            constraint = _translate_constraint(line)
            if constraint:
                pg_lines.append(constraint)
            continue

        if _is_column_definition(line):
            pg_lines.append(_translate_column(line))
            continue

    pg_sql = f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(pg_lines) + "\n);"
    return pg_sql


def _split_sql_lines(block: str) -> List[str]:
    lines = []
    current = ""
    parens = 0
    for char in block:
        if char == "(":
            parens += 1
        elif char == ")":
            parens -= 1
        if char == "," and parens == 0:
            lines.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        lines.append(current)
    return lines


def _is_column_definition(line: str) -> bool:
    return bool(re.match(r"^\s*`?\w+`?\s+\w+", line.strip()))


def _translate_column(line: str) -> str:
    original = line.strip().rstrip(",")
    if not original:
        return ""

    col_match = re.match(
        r"^\s*`?(?P<col>\w+)`?\s+(?P<type>\w+)(?P<length>\([^)]+\))?(?P<extras>.*)$",
        original,
        flags=re.IGNORECASE
    )

    if not col_match:
        return original  # fallback

    col = col_match.group("col")
    mysql_type = col_match.group("type").lower()
    length = col_match.group("length") or ""
    extras = col_match.group("extras") or ""

    if "enum(" in original.lower():
        return _convert_enum_full(col=original.split()[0], rest=original)

    if "set(" in original.lower():
        return _convert_set_full(col=original.split()[0], rest=original)

    if "auto_increment" in extras.lower():
        pg_type = get_serial_type(mysql_type)
        if "primary key" in extras.lower():
            extras = re.sub(r"\bPRIMARY KEY\b", "", extras, flags=re.IGNORECASE)
            return f"{col} {pg_type} PRIMARY KEY".strip()
        extras = re.sub(r"\bAUTO_INCREMENT\b", "", extras, flags=re.IGNORECASE)
        return f"{col} {pg_type} {extras.strip()}"

    extras = _clean_extras(extras)

    if mysql_type in ("tinyint", "smallint", "mediumint", "int", "integer", "bigint"):
        pg_type = TYPE_MAP.get(mysql_type, "INTEGER")
        return f"{col} {pg_type} {extras}".strip()

    if mysql_type in ("decimal", "numeric"):
        pg_type = "NUMERIC" + length
        return f"{col} {pg_type} {extras}".strip()

    if mysql_type in ("float", "double", "double precision"):
        pg_type = TYPE_MAP.get(mysql_type, "DOUBLE PRECISION")
        return f"{col} {pg_type} {extras}".strip()

    if mysql_type == "bit":
        pg_type = "BIT" + length if length else "BIT"
        return f"{col} {pg_type} {extras}".strip()

    if mysql_type in ("char", "varchar"):
        pg_type = mysql_type.upper() + length
        return f"{col} {pg_type} {extras}".strip()

    if mysql_type in ("text", "tinytext", "mediumtext", "longtext"):
        return f"{col} TEXT {extras}".strip()

    if mysql_type in ("binary", "varbinary", "blob", "tinyblob", "mediumblob", "longblob"):
        return f"{col} BYTEA {extras}".strip()

    if mysql_type == "json":
        return f"{col} JSONB {extras}".strip()

    if mysql_type in ("date", "time", "datetime", "timestamp", "year"):
        pg_type = TYPE_MAP.get(mysql_type, "TIMESTAMP WITHOUT TIME ZONE")
        return f"{col} {pg_type} {extras}".strip()

    if mysql_type in (
        "geometry", "point", "linestring", "polygon",
        "multipoint", "multilinestring", "multipolygon", "geometrycollection"
    ):
        return f"{col} BYTEA {extras}".strip()

    return f"{col} TEXT {extras}".strip()


def _clean_extras(extras: str) -> str:
    extras = extras.strip()
    extras = re.sub(r"CHARACTER SET\s+\w+", '', extras, flags=re.IGNORECASE)
    extras = re.sub(r"COLLATE\s+\w+", '', extras, flags=re.IGNORECASE)
    extras = re.sub(r"ON UPDATE CURRENT_TIMESTAMP", '', extras, flags=re.IGNORECASE)
    extras = re.sub(r"_utf8mb4'([^']*)'", r"'\1'", extras, flags=re.IGNORECASE)
    extras = extras.replace("\n", " ")
    extras = re.sub(r"\s{2,}", ' ', extras)
    return extras.strip()


def _translate_constraint(line: str) -> str:
    line = re.sub(r"`", "", line)

    if any(x in line.upper() for x in ("FULLTEXT", "SPATIAL")):
        return ""

    match = re.match(r"UNIQUE KEY \w+ \((.+)\)", line, re.IGNORECASE)
    if match:
        return f"UNIQUE ({match.group(1)})"

    if "UNIQUE" in line.upper():
        return re.sub(r"UNIQUE KEY", "UNIQUE", line, flags=re.IGNORECASE)

    return line


def _convert_enum_full(col: str, rest: str):
    values = re.findall(r"\(([^)]+)\)", rest)
    clean_rest = re.sub(r"ENUM\s*\([^)]+\)", "", rest, flags=re.IGNORECASE)
    clean_rest = re.sub(r"COLLATE\s+\w+", "", clean_rest, flags=re.IGNORECASE)
    clean_rest = re.sub(r"CHARACTER SET\s+\w+", "", clean_rest, flags=re.IGNORECASE)
    clean_rest = re.sub(rf"^{col}\s+", "", clean_rest).strip()

    if values:
        return f"{col} TEXT {clean_rest} CHECK ({col} IN ({values[0]}))".strip()
    return f"{col} TEXT {clean_rest}".strip()


def _convert_set_full(col: str, rest: str):
    values_match = re.search(r"\(([^)]+)\)", rest)
    values = values_match.group(1).replace(" ", "") if values_match else ""

    clean_rest = re.sub(r"SET\s*\([^)]+\)", "", rest, flags=re.IGNORECASE)
    clean_rest = re.sub(r"COLLATE\s+\w+", "", clean_rest, flags=re.IGNORECASE)
    clean_rest = re.sub(r"CHARACTER SET\s+\w+", "", clean_rest, flags=re.IGNORECASE)
    clean_rest = re.sub(rf"^{col}\s+", "", clean_rest).strip()

    check_clause = f"CHECK ({col} <@ ARRAY[{values}])" if values else ""
    return f"{col} TEXT[] {clean_rest} {check_clause}".strip()
