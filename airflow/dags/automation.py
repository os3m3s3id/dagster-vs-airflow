from datetime import datetime

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator


with DAG(
    dag_id="data_pipeline_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    run_data_init = DockerOperator(
        task_id="run_data_init",
        image="data_init:latest",
        docker_url="unix://var/run/docker.sock",

        # Must match the network name in docker-compose.yml
        network_mode="dagster-vs-airflow-network",

        auto_remove="success",
        mount_tmp_dir=False,

        environment={
            "DB_USER": "source_postgres",
            "DB_PASSWORD": "sourcepostgres",
            "DB_HOST": "source",
            "DB_PORT": "5432",
            "DB_NAME": "source",
        },
    )