from datetime import datetime

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator


DOCKER_NETWORK = "dagster-vs-airflow-network"


with DAG(
    dag_id="raw_to_silver_dag",
    description=(
        "Run Spark to clean raw.customer "
        "and create silver.silver_customer."
    ),
    start_date=datetime(2026, 1, 1),

    # Manual execution for now
    schedule=None,

    catchup=False,

    # Prevent two Spark jobs from overwriting
    # the silver table at the same time
    max_active_runs=1,

    tags=[
        "spark",
        "raw",
        "silver",
    ],
) as dag:

    run_silver_job = DockerOperator(
        task_id="run_silver_job",

        # Local Spark cleansing image
        image="silver_job:latest",

        # Connect Airflow to the host Docker engine
        docker_url="unix://var/run/docker.sock",

        # Use the locally built image.
        # Do not pull it from Docker Hub.
        force_pull=False,

        # Connect the temporary container to PostgreSQL
        # and the Spark cluster
        network_mode=DOCKER_NETWORK,

        # Your Dockerfile already contains spark-submit,
        # so no command is needed here.

        mount_tmp_dir=False,

        # Delete the temporary container after success
        auto_remove="success",

        environment={
            "SPARK_MASTER_URL": (
                "spark://spark-master:7077"
            ),
            "SOURCE_JDBC_URL": (
                "jdbc:postgresql://source:5432/source"
            ),
            "SOURCE_TABLE": "raw.customer",
            "SOURCE_DB_USER": "source_postgres",
            "SOURCE_DB_PASSWORD": "sourcepostgres",
            "SOURCE_PARTITION_COLUMN": "customer_id",
            "SOURCE_LOWER_BOUND": "1",
            "SOURCE_UPPER_BOUND": "10000000",
            "SOURCE_NUM_PARTITIONS": "8",
        },
    )