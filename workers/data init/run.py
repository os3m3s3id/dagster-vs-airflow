from sqlalchemy import create_engine, text


# Database connection details
DB_USER = "source_postgres"
DB_PASSWORD = "sourcepostgres"
DB_HOST = "source"
DB_PORT = "5432"
DB_NAME = "source"

TARGET_BYTES = 5 * 1024 * 1024 * 1024  # Exactly 5 GiB = 5,368,709,120 bytes


engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


try:
    with engine.begin() as connection:
        print("Connected successfully", flush=True)

        connection.execute(
            text("CREATE SCHEMA IF NOT EXISTS raw;")
        )

        connection.execute(
            text("""
                DROP TABLE IF EXISTS raw.customer;

                CREATE TABLE raw.customer (
                    customer_id bigint,
                    first_name  text,
                    last_name   text,
                    email       text,
                    phone       text,
                    address     text,
                    city        text,
                    country     text,
                    created_at  timestamp,
                    padding     text
                );

                ALTER TABLE raw.customer
                SET (autovacuum_enabled = false);
            """)
        )

        connection.execute(
            text("""
                DO $$
                DECLARE
                    target_bytes bigint := 5::bigint * 1024 * 1024 * 1024;

                    current_size bigint := 0;
                    next_id      bigint := 1;
                    rows_to_add  integer;
                BEGIN
                    /*
                     * Stage 1:
                     * Add 500,000 rows while more than 512 MiB remains.
                     */
                    LOOP
                        SELECT pg_relation_size('raw.customer')
                        INTO current_size;

                        EXIT WHEN target_bytes - current_size <=
                                  512::bigint * 1024 * 1024;

                        rows_to_add := 500000;

                        INSERT INTO raw.customer (
                            customer_id,
                            first_name,
                            last_name,
                            email,
                            phone,
                            address,
                            city,
                            country,
                            created_at,
                            padding
                        )
                        WITH generated AS (
                            SELECT next_id + gs - 1 AS row_id
                            FROM generate_series(1, rows_to_add) AS gs
                        )
                        SELECT
                            CASE
                                WHEN row_id % 7 = 0 THEN row_id - 1
                                ELSE row_id
                            END,
                            CASE
                                WHEN random() < 0.05 THEN NULL
                                ELSE 'First' || row_id
                            END,
                            CASE
                                WHEN random() < 0.05 THEN NULL
                                ELSE 'Last' || row_id
                            END,
                            CASE
                                WHEN random() < 0.10 THEN NULL
                                ELSE 'user' || row_id || '@example.com'
                            END,
                            CASE
                                WHEN random() < 0.10 THEN NULL
                                ELSE '+1-555-' ||
                                    lpad((row_id % 10000)::text, 4, '0')
                            END,
                            'Address ' || row_id,
                            (
                                ARRAY[
                                    'New York',
                                    'London',
                                    'Berlin',
                                    'Tokyo',
                                    'Paris'
                                ]
                            )[1 + floor(random() * 5)::int],
                            (
                                ARRAY[
                                    'USA',
                                    'UK',
                                    'Germany',
                                    'Japan',
                                    'France'
                                ]
                            )[1 + floor(random() * 5)::int],
                            now() - (random() * interval '3650 days'),
                            md5(random()::text || row_id::text) ||
                            md5(random()::text) ||
                            md5(random()::text)
                        FROM generated;

                        next_id := next_id + rows_to_add;
                    END LOOP;


                    /*
                     * Stage 2:
                     * Add 10,000 rows while more than 16 MiB remains.
                     */
                    LOOP
                        SELECT pg_relation_size('raw.customer')
                        INTO current_size;

                        EXIT WHEN target_bytes - current_size <=
                                  16::bigint * 1024 * 1024;

                        rows_to_add := 10000;

                        INSERT INTO raw.customer
                        WITH generated AS (
                            SELECT next_id + gs - 1 AS row_id
                            FROM generate_series(1, rows_to_add) AS gs
                        )
                        SELECT
                            CASE
                                WHEN row_id % 7 = 0 THEN row_id - 1
                                ELSE row_id
                            END,
                            CASE WHEN random() < 0.05
                                THEN NULL ELSE 'First' || row_id END,
                            CASE WHEN random() < 0.05
                                THEN NULL ELSE 'Last' || row_id END,
                            CASE WHEN random() < 0.10
                                THEN NULL
                                ELSE 'user' || row_id || '@example.com'
                            END,
                            CASE WHEN random() < 0.10
                                THEN NULL
                                ELSE '+1-555-' ||
                                     lpad((row_id % 10000)::text, 4, '0')
                            END,
                            'Address ' || row_id,
                            (
                                ARRAY[
                                    'New York',
                                    'London',
                                    'Berlin',
                                    'Tokyo',
                                    'Paris'
                                ]
                            )[1 + floor(random() * 5)::int],
                            (
                                ARRAY[
                                    'USA',
                                    'UK',
                                    'Germany',
                                    'Japan',
                                    'France'
                                ]
                            )[1 + floor(random() * 5)::int],
                            now() - (random() * interval '3650 days'),
                            md5(random()::text || row_id::text) ||
                            md5(random()::text) ||
                            md5(random()::text)
                        FROM generated;

                        next_id := next_id + rows_to_add;
                    END LOOP;


                    /*
                     * Stage 3:
                     * Add 100 rows while more than 1 MiB remains.
                     */
                    LOOP
                        SELECT pg_relation_size('raw.customer')
                        INTO current_size;

                        EXIT WHEN target_bytes - current_size <=
                                  1::bigint * 1024 * 1024;

                        rows_to_add := 100;

                        INSERT INTO raw.customer
                        WITH generated AS (
                            SELECT next_id + gs - 1 AS row_id
                            FROM generate_series(1, rows_to_add) AS gs
                        )
                        SELECT
                            row_id,
                            'First' || row_id,
                            'Last' || row_id,
                            'user' || row_id || '@example.com',
                            '+1-555-' ||
                                lpad((row_id % 10000)::text, 4, '0'),
                            'Address ' || row_id,
                            'London',
                            'UK',
                            now(),
                            md5(random()::text || row_id::text) ||
                            md5(random()::text) ||
                            md5(random()::text)
                        FROM generated;

                        next_id := next_id + rows_to_add;
                    END LOOP;


                    /*
                     * Stage 4:
                     * Insert one row at a time.
                     *
                     * PostgreSQL extends a table in 8 KiB pages.
                     * Exactly 5 GiB is divisible by 8 KiB, so the table
                     * can stop at precisely the requested byte size.
                     */
                    LOOP
                        SELECT pg_relation_size('raw.customer')
                        INTO current_size;

                        EXIT WHEN current_size = target_bytes;

                        IF current_size > target_bytes THEN
                            RAISE EXCEPTION
                                'Table exceeded target. Current: %, target: %',
                                current_size,
                                target_bytes;
                        END IF;

                        INSERT INTO raw.customer (
                            customer_id,
                            first_name,
                            last_name,
                            email,
                            phone,
                            address,
                            city,
                            country,
                            created_at,
                            padding
                        )
                        VALUES (
                            next_id,
                            'First' || next_id,
                            'Last' || next_id,
                            'user' || next_id || '@example.com',
                            '+1-555-' ||
                                lpad((next_id % 10000)::text, 4, '0'),
                            'Address ' || next_id,
                            'London',
                            'UK',
                            now(),
                            md5(random()::text || next_id::text) ||
                            md5(random()::text) ||
                            md5(random()::text)
                        );

                        next_id := next_id + 1;
                    END LOOP;


                    SELECT pg_relation_size('raw.customer')
                    INTO current_size;

                    IF current_size <> target_bytes THEN
                        RAISE EXCEPTION
                            'Incorrect final size. Current: %, expected: %',
                            current_size,
                            target_bytes;
                    END IF;

                    RAISE NOTICE
                        'Finished: raw.customer is exactly % bytes',
                        current_size;
                END $$;
            """)
        )

        result = connection.execute(
            text("""
                SELECT
                    pg_relation_size('raw.customer') AS table_bytes,
                    pg_size_pretty(
                        pg_relation_size('raw.customer')
                    ) AS table_size,
                    pg_total_relation_size(
                        'raw.customer'
                    ) AS total_relation_bytes,
                    COUNT(*) AS total_rows
                FROM raw.customer;
            """)
        ).mappings().one()

        print("Generation completed", flush=True)
        print(f"Main table bytes: {result['table_bytes']:,}", flush=True)
        print(f"Main table size: {result['table_size']}", flush=True)
        print(f"Total relation bytes: {result['total_relation_bytes']:,}", flush=True)
        print(f"Total rows: {result['total_rows']:,}", flush=True)

        assert result["table_bytes"] == TARGET_BYTES

except Exception as error:
    print("Data generation failed:", flush=True)
    print(error, flush=True)
    raise