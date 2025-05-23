CREATE TABLE complex_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tiny_int_col TINYINT NOT NULL,
    small_int_col SMALLINT NOT NULL,
    medium_int_col MEDIUMINT NOT NULL,
    int_col INT NOT NULL,
    big_int_col BIGINT NOT NULL,
    decimal_col DECIMAL(10, 2) NOT NULL,
    float_col FLOAT NOT NULL,
    double_col DOUBLE NOT NULL,
    bit_col BIT(8) NOT NULL,
    char_col CHAR(10) NOT NULL,
    varchar_col VARCHAR(255) NOT NULL,
    binary_col BINARY(16) NOT NULL,
    varbinary_col VARBINARY(255) NOT NULL,
    tinytext_col TINYTEXT NOT NULL,
    text_col TEXT NOT NULL,
    mediumtext_col MEDIUMTEXT NOT NULL,
    longtext_col LONGTEXT NOT NULL,
    tinyblob_col TINYBLOB NOT NULL,
    blob_col BLOB NOT NULL,
    mediumblob_col MEDIUMBLOB NOT NULL,
    longblob_col LONGBLOB NOT NULL,
    enum_col ENUM('value1', 'value2', 'value3') NOT NULL,
    set_col SET('value1', 'value2', 'value3') NOT NULL,
    date_col DATE NOT NULL,
    datetime_col DATETIME NOT NULL,
    timestamp_col TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    time_col TIME NOT NULL,
    year_col YEAR NOT NULL,
    json_col JSON NOT NULL,
    geometry_col GEOMETRY NOT NULL,
    point_col POINT NOT NULL,
    linestring_col LINESTRING NOT NULL,
    polygon_col POLYGON NOT NULL,
    multipoint_col MULTIPOINT NOT NULL,
    multilinestring_col MULTILINESTRING NOT NULL,
    multipolygon_col MULTIPOLYGON NOT NULL,
    geometrycollection_col GEOMETRYCOLLECTION NOT NULL,
    fulltext_col TEXT NOT NULL,
    spatial_index_col POINT NOT NULL,
    UNIQUE KEY unique_key (varchar_col),
    FULLTEXT KEY fulltext_index (fulltext_col),
    SPATIAL KEY spatial_index (spatial_index_col)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='A table with all MySQL column types and parameters.';