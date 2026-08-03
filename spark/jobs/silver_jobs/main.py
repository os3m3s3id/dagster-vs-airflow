import os

from pyspark.sql import SparkSession

from silver_customer import run_customer_silver


spark = (
    SparkSession.builder
    .appName("raw-to-silver-pipeline")
    .master(os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077"))
    .getOrCreate()
)


try:
    run_customer_silver(spark)

finally:
    spark.stop()