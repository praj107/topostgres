import re
from typing import List
from .type_map import TYPE_MAP, get_serial_type

def extract_foreign_keys(pg_sql: str) -> List[dict[str, str]]:
    """
    Extracts foreign key constraints from PostgreSQL SQL statements.


    Args:
        pg_sql (str): The PostgreSQL SQL statement to extract foreign keys from.

    Returns:
        List[dict[str, str]]: A list of dictionaries, each containing the local columns, foreign table name, and foreign columns. 
    """
    # General regex for FOREIGN KEY constraints
    pattern = re.compile(
        r'''
        FOREIGN\s+KEY\s*\(
            (?P<local_cols>[^)]+)        # Capture local columns
        \)
        \s*REFERENCES\s+
            (?P<foreign_table>\w+)       # Capture foreign table name
        \s*\(
            (?P<foreign_cols>[^)]+)      # Capture foreign columns
        \)
        ''',
        re.IGNORECASE | re.VERBOSE | re.MULTILINE
    )

    foreign_keys = []

    for match in pattern.finditer(pg_sql):
        local_columns = [col.strip() for col in match.group('local_cols').split(',')]
        foreign_table = match.group('foreign_table').strip()
        foreign_columns = [col.strip() for col in match.group('foreign_cols').split(',')]
        
        foreign_keys.append({
            'local_columns': local_columns,
            'foreign_table': foreign_table,
            'foreign_columns': foreign_columns
        })

    return foreign_keys

def extract_single_column_uniques_and_pks(pg_sql: str) -> List[str]:
    # Match UNIQUE (...) and PRIMARY KEY (...) — with or without CONSTRAINT keyword
    unique_matches = re.findall(r'^\s*(?:CONSTRAINT\s+\w+\s+)?UNIQUE\s*\(([^)]+)\)', pg_sql, re.MULTILINE)
    primary_matches = re.findall(r'^\s*(?:CONSTRAINT\s+\w+\s+)?PRIMARY KEY\s*\(([^)]+)\)', pg_sql, re.MULTILINE)

    # Filter only those constraints that cover exactly one column
    unique_keys = [col.strip() for cols in unique_matches if len(cols.split(',')) == 1 for col in cols.split(',')]
    primary_keys = [col.strip() for cols in primary_matches if len(cols.split(',')) == 1 for col in cols.split(',')]

    return unique_keys, primary_keys


def translate_schema(tables: dict[str, str]) -> dict[str, str]:
    initial_postgres_sql = {x: _translate_table(tables[x]) for x in tables.keys()}
    sole_unique_and_primary_keys_columns = {} # {table_name: column_name (if individually unique or primary key)}]}
    first_stage_processed_postgres_sql = {}
    # Now we need to check, and remove, invalid foreign keys, the ones which do not point to a solely unique or primary key column.:
    for table_name, pg_sql in initial_postgres_sql.items():
        # Get individually unique and primary keys in the table
        unique, primary = extract_single_column_uniques_and_pks(pg_sql)
        # Update the dictionary with the unique and primary keys
        for col in unique + primary:
            sole_unique_and_primary_keys_columns[table_name] = col
        print(f"Table: {table_name}.\nUnique keys: {unique}\nPrimary keys: {primary}")
        # Get the list of foreign keys in the table:
        foreign_keys = extract_foreign_keys(pg_sql)
        print(f"Foreign keys: {foreign_keys}")
        for d in foreign_keys:
            foreign_table, foreign_cols = d['foreign_table'], d['foreign_columns']
            for foreign_col in foreign_cols:
                # Check if the referenced column is NOT solely unique/primary
                if foreign_col not in sole_unique_and_primary_keys_columns.get(foreign_table, []):
                    print(f"Foreign key {d} in table {table_name} is invalid, removing it.")
                    # Make a basic pattern to find the reference
                    reference_pattern = rf'REFERENCES\s+{foreign_table}\s*\(\s*{foreign_col}\s*\)'
                    # Remove any line containing that reference
                    pg_sql = "\n".join(
                        line for line in pg_sql.splitlines()
                        if not re.search(reference_pattern, line, flags=re.IGNORECASE)
                    ).replace(",\n);", "\n);")  # Remove the comma before the closing parenthesis if it exists
                    
        first_stage_processed_postgres_sql[table_name] = pg_sql


    return first_stage_processed_postgres_sql


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

        if any(line.upper().startswith(x) for x in ("KEY ", "UNIQUE KEY ", "FULLTEXT KEY", "SPATIAL KEY", "PRIMARY KEY")):
            constraint = _translate_constraint(line)
            if constraint:
                pg_lines.append(constraint)
            continue

        if _is_column_definition(line):
            if "GENERATED ALWAYS AS" in line.upper():
                line = _strip_generated_column(line)  # ✅ Preserve column, strip generated logic
            pg_lines.append(_translate_column(line))
            continue

    pg_sql = f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(pg_lines) + "\n);\n"

    return pg_sql


def _strip_generated_column(line: str) -> str:
    """
    Removes the GENERATED ALWAYS AS (...) clause while keeping the column definition.
    """
    # If it’s just the generated clause, preserve the column and type
    match = re.match(
        r"^\s*`?(?P<col>\w+)`?\s+(?P<type>\w+(?:\([^)]+\))?)\s+GENERATED\s+ALWAYS\s+AS\s*\(\(.*?\)\)\s*(STORED|VIRTUAL)?",
        line,
        flags=re.IGNORECASE | re.DOTALL
    )
    if match:
        return f"{match.group('col')} {match.group('type')}"

    # Otherwise strip normally
    return re.sub(
        r"GENERATED\s+ALWAYS\s+AS\s*\(\(.*?\)\)\s*(STORED|VIRTUAL)?",
        "",
        line,
        flags=re.IGNORECASE | re.DOTALL
    ).strip()


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

    # Normalize spacing and remove length from column names like bio(255)
    def strip_lengths(columns: str) -> str:
        return ", ".join(re.sub(r"\(\d+\)", "", col.strip()) for col in columns.split(","))

    # FOREIGN KEY with optional CONSTRAINT name
    fk_match = re.match(
        r"(CONSTRAINT\s+(\w+)\s+)?FOREIGN\s+KEY\s*\(([^)]+)\)\s+REFERENCES\s+(\w+)\s*\(([^)]+)\)",
        line,
        re.IGNORECASE
    )
    if fk_match:
        constraint_name = fk_match.group(2)
        cols = strip_lengths(fk_match.group(3))
        ref_table = fk_match.group(4)
        ref_cols = strip_lengths(fk_match.group(5))
        if constraint_name:
            return f"CONSTRAINT {constraint_name} FOREIGN KEY ({cols}) REFERENCES {ref_table} ({ref_cols})"
        return f"FOREIGN KEY ({cols}) REFERENCES {ref_table} ({ref_cols})"

    # UNIQUE KEY or unnamed UNIQUE constraint
    if match := re.match(r"(UNIQUE\s+KEY\s+\w+\s*)?\((.+)\)", line, flags=re.IGNORECASE):
        cols = strip_lengths(match.group(2))
        return f"UNIQUE ({cols})"

    if match := re.match(r"UNIQUE KEY \w+ \((.+)\)", line, re.IGNORECASE):
        cols = strip_lengths(match.group(1))
        return f"UNIQUE ({cols})"

    # Skip KEY or INDEX — create separately after table
    if match := re.match(r"(KEY|INDEX)\s+\w+\s*\((.+)\)", line, re.IGNORECASE):
        return ""

    # PRIMARY KEY is valid in CREATE TABLE
    if match := re.match(r"(PRIMARY\s+KEY)\s*\((.+)\)", line, re.IGNORECASE):
        cols = strip_lengths(match.group(2))
        return f"{match.group(1).upper()} ({cols})"

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
