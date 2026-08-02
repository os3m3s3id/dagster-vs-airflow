from sqlalchemy import create_engine, text


# Database connection details
DB_USER = "source_postgres"
DB_PASSWORD = "sourcepostgres"
DB_HOST = "source"
DB_PORT = "5432"
DB_NAME = "source"


# Create database connection
engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# Connect and run SQL
try:
    with engine.begin() as connection:
        print("Connected successfully")

        connection.execute(
            text("CREATE SCHEMA IF NOT EXISTS raw;")
        )


        connection.execute(
            text("""
                DROP TABLE IF EXISTS raw.customer;
                CREATE TABLE IF NOT EXISTS raw.customer (
                    customer_id   bigint,
                    first_name    text,
                    last_name     text,
                    email         text,
                    phone         text,
                    address       text,
                    city          text,
                    country       text,
                    created_at    timestamp,
                    padding       text
                );
            """)
        )


        connection.execute(
            text("""
                DO $$
                DECLARE
                    target_bytes bigint := 10::bigint * 1024 * 1024 * 1024;
                    batch_size   bigint := 500000;
                    batch_num    bigint := 0;
                    current_size bigint := 0;
                BEGIN
                    WHILE current_size < target_bytes LOOP
                        batch_num := batch_num + 1;

                        INSERT INTO raw.customer (customer_id, first_name, last_name, email, phone, address, city, country, created_at, padding)
                        SELECT
                            (CASE WHEN gs % 7 = 0 THEN gs - 1 ELSE gs END) + (batch_num - 1) * batch_size AS customer_id,
                            CASE WHEN random() < 0.05 THEN NULL ELSE 'First' || gs END,
                            CASE WHEN random() < 0.05 THEN NULL ELSE 'Last' || gs END,
                            CASE WHEN random() < 0.10 THEN NULL ELSE 'user' || gs || '@example.com' END,
                            CASE WHEN random() < 0.10 THEN NULL ELSE '+1-555-' || lpad((gs % 10000)::text, 4, '0') END,
                            'Address ' || gs,
                            (ARRAY['New York','London','Berlin','Tokyo','Paris'])[1 + floor(random()*5)::int],
                            (ARRAY['USA','UK','Germany','Japan','France'])[1 + floor(random()*5)::int],
                            now() - (random() * interval '3650 days'),
                            md5(random()::text || gs::text) || md5(random()::text) || md5(random()::text)
                        FROM generate_series(1, batch_size) AS gs;

                        SELECT pg_total_relation_size('raw.customer') INTO current_size;

                        RAISE NOTICE 'Batch %, current size % MB', batch_num, current_size / 1024 / 1024;
                    END LOOP;
                END $$;
            """)
        )

        
except Exception as error:
    print("Database connection failed:")
    print(error)
    raise