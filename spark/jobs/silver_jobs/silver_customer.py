from pyspark.sql import functions as F
from pyspark.sql.window import Window


JDBC_URL = "jdbc:postgresql://source:5432/source"
DB_USER = "source_postgres"
DB_PASSWORD = "sourcepostgres"

SOURCE_TABLE = "raw.customer"
TARGET_TABLE = "silver.silver_customer"


def run_customer_silver(spark):

    # Create silver schema
    connection = spark._sc._gateway.jvm.java.sql.DriverManager.getConnection(
        JDBC_URL,
        DB_USER,
        DB_PASSWORD,
    )

    statement = connection.createStatement()
    statement.execute("CREATE SCHEMA IF NOT EXISTS silver")

    statement.close()
    connection.close()

    # Read source table
    source_df = (
        spark.read
        .format("jdbc")
        .option("url", JDBC_URL)
        .option("dbtable", SOURCE_TABLE)
        .option("user", DB_USER)
        .option("password", DB_PASSWORD)
        .option("driver", "org.postgresql.Driver")
        .option("partitionColumn", "customer_id")
        .option("lowerBound", "1")
        .option("upperBound", "10000000")
        .option("numPartitions", "8")
        .option("fetchsize", "10000")
        .load()
    )

    source_df.printSchema()

    selected_df = source_df.select(
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "address",
        "city",
        "country",
        "created_at",
    )

    standardized_df = selected_df.select(
        F.col("customer_id").cast("int").alias("customer_id"),
        F.trim(F.col("first_name")).alias("first_name"),
        F.trim(F.col("last_name")).alias("last_name"),
        F.lower(F.trim(F.col("email"))).alias("email"),
        F.regexp_replace(
            F.trim(F.col("phone")),
            r"[^0-9+]",
            "",
        ).alias("phone"),
        F.trim(F.col("address")).alias("address"),
        F.trim(F.col("city")).alias("city"),
        F.trim(F.col("country")).alias("country"),
        F.to_timestamp(F.col("created_at")).alias("created_at"),
    )

    cleaned_df = standardized_df.dropna(
        subset=[
            "customer_id",
            "created_at",
        ]
    )

    cleaned_df = cleaned_df.fillna(
        {
            "first_name": "Unknown",
            "last_name": "Unknown",
            "city": "Unknown",
            "country": "Unknown",
        }
    )

    customer_window = (
        Window
        .partitionBy("customer_id")
        .orderBy(F.col("created_at").desc())
    )

    cleaned_df = (
        cleaned_df
        .withColumn(
            "row_number",
            F.row_number().over(customer_window),
        )
        .filter(F.col("row_number") == 1)
        .drop("row_number")
    )

    cleaned_df = (
        cleaned_df
        .withColumn(
            "full_name",
            F.concat_ws(
                " ",
                F.col("first_name"),
                F.col("last_name"),
            ),
        )
        .drop(
            "first_name",
            "last_name",
        )
    )

    (
        cleaned_df.write
        .format("jdbc")
        .option("url", JDBC_URL)
        .option("dbtable", TARGET_TABLE)
        .option("user", DB_USER)
        .option("password", DB_PASSWORD)
        .option("driver", "org.postgresql.Driver")
        .option("batchsize", "5000")
        .option("numPartitions", "4")
        .mode("overwrite")
        .save()
    )

    print(f"Cleaned data moved to {TARGET_TABLE} successfully.")