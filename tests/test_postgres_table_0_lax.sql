-- ========================================
-- Complex Table Setup Script (PostGIS-Aware Fallback)
-- Fallbacks to BYTEA if PostGIS is unavailable
-- ========================================

DO $$
DECLARE
    postgis_available BOOLEAN := TRUE;
BEGIN
    BEGIN
        -- Try to enable PostGIS
        IF NOT EXISTS (
            SELECT 1 FROM pg_extension WHERE extname = 'postgis'
        ) THEN
            CREATE EXTENSION postgis;
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            -- PostGIS not installed
            postgis_available := FALSE;
            RAISE NOTICE 'PostGIS not available, using BYTEA as fallback for spatial types.';
    END;

    -- Begin transaction block
    BEGIN
        -- Drop table if already exists for clean testing
        DROP TABLE IF EXISTS complex_table;

        -- Conditionally create the table based on PostGIS availability
        IF postgis_available THEN
            EXECUTE $postgis$
            CREATE TABLE complex_table (
                id SERIAL PRIMARY KEY,

                tiny_int_col SMALLINT NOT NULL,
                small_int_col SMALLINT NOT NULL,
                medium_int_col INTEGER NOT NULL,
                int_col INTEGER NOT NULL,
                big_int_col BIGINT NOT NULL,

                decimal_col NUMERIC(10, 2) NOT NULL,
                float_col REAL NOT NULL,
                double_col DOUBLE PRECISION NOT NULL,

                bit_col BIT(8) NOT NULL,

                char_col CHAR(10) NOT NULL,
                varchar_col VARCHAR(255) NOT NULL,

                binary_col BYTEA NOT NULL,
                varbinary_col BYTEA NOT NULL,

                tinytext_col TEXT NOT NULL,
                text_col TEXT NOT NULL,
                mediumtext_col TEXT NOT NULL,
                longtext_col TEXT NOT NULL,

                tinyblob_col BYTEA NOT NULL,
                blob_col BYTEA NOT NULL,
                mediumblob_col BYTEA NOT NULL,
                longblob_col BYTEA NOT NULL,

                enum_col TEXT NOT NULL CHECK (enum_col IN ('value1', 'value2', 'value3')),
                set_col TEXT[] NOT NULL CHECK (set_col <@ ARRAY['value1','value2','value3']),

                date_col DATE NOT NULL,
                datetime_col TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                timestamp_col TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                time_col TIME WITHOUT TIME ZONE NOT NULL,
                year_col SMALLINT NOT NULL CHECK (year_col BETWEEN 1901 AND 2155),

                json_col JSONB NOT NULL,

                geometry_col geometry NOT NULL,
                point_col geometry(Point) NOT NULL,
                linestring_col geometry(LineString) NOT NULL,
                polygon_col geometry(Polygon) NOT NULL,
                multipoint_col geometry(MultiPoint) NOT NULL,
                multilinestring_col geometry(MultiLineString) NOT NULL,
                multipolygon_col geometry(MultiPolygon) NOT NULL,
                geometrycollection_col geometry(GeometryCollection) NOT NULL,

                fulltext_col TEXT NOT NULL,
                spatial_index_col geometry(Point) NOT NULL,

                UNIQUE (varchar_col)
            );
            $postgis$;

            -- Full-text index (always OK)
            CREATE INDEX IF NOT EXISTS fulltext_index
              ON complex_table USING GIN (to_tsvector('english', fulltext_col));

            -- Spatial index (only if PostGIS available)
            CREATE INDEX IF NOT EXISTS spatial_index
              ON complex_table USING GIST (spatial_index_col);

        ELSE
            EXECUTE $fallback$
            CREATE TABLE complex_table (
                id SERIAL PRIMARY KEY,

                tiny_int_col SMALLINT NOT NULL,
                small_int_col SMALLINT NOT NULL,
                medium_int_col INTEGER NOT NULL,
                int_col INTEGER NOT NULL,
                big_int_col BIGINT NOT NULL,

                decimal_col NUMERIC(10, 2) NOT NULL,
                float_col REAL NOT NULL,
                double_col DOUBLE PRECISION NOT NULL,

                bit_col BIT(8) NOT NULL,

                char_col CHAR(10) NOT NULL,
                varchar_col VARCHAR(255) NOT NULL,

                binary_col BYTEA NOT NULL,
                varbinary_col BYTEA NOT NULL,

                tinytext_col TEXT NOT NULL,
                text_col TEXT NOT NULL,
                mediumtext_col TEXT NOT NULL,
                longtext_col TEXT NOT NULL,

                tinyblob_col BYTEA NOT NULL,
                blob_col BYTEA NOT NULL,
                mediumblob_col BYTEA NOT NULL,
                longblob_col BYTEA NOT NULL,

                enum_col TEXT NOT NULL CHECK (enum_col IN ('value1', 'value2', 'value3')),
                set_col TEXT[] NOT NULL CHECK (set_col <@ ARRAY['value1','value2','value3']),

                date_col DATE NOT NULL,
                datetime_col TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                timestamp_col TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                time_col TIME WITHOUT TIME ZONE NOT NULL,
                year_col SMALLINT NOT NULL CHECK (year_col BETWEEN 1901 AND 2155),

                json_col JSONB NOT NULL,

                geometry_col BYTEA NOT NULL,
                point_col BYTEA NOT NULL,
                linestring_col BYTEA NOT NULL,
                polygon_col BYTEA NOT NULL,
                multipoint_col BYTEA NOT NULL,
                multilinestring_col BYTEA NOT NULL,
                multipolygon_col BYTEA NOT NULL,
                geometrycollection_col BYTEA NOT NULL,

                fulltext_col TEXT NOT NULL,
                spatial_index_col BYTEA NOT NULL,

                UNIQUE (varchar_col)
            );
            $fallback$;

            -- Full-text index still valid
            CREATE INDEX IF NOT EXISTS fulltext_index
              ON complex_table USING GIN (to_tsvector('english', fulltext_col));
        END IF;

        COMMIT;
    END;
END$$;