import dagster as dg
from dagster_docker import docker_container_op


run_data_init = docker_container_op.configured(
    {
        "image": "data_init:latest",

        # Connect the worker container to the same network as PostgreSQL.
        "networks": [
            "dagster-vs-airflow-network",
        ],

        "env_vars": [
            "DB_USER=source_postgres",
            "DB_PASSWORD=sourcepostgres",
            "DB_HOST=source",
            "DB_PORT=5432",
            "DB_NAME=source",
        ],
    },
    name="run_data_init",
)


@dg.job(
    name="dagster_data_generate",
    description="Generate source customer data using the data_init container",
)
def dagster_data_generate():
    run_data_init()


defs = dg.Definitions(
    jobs=[
        dagster_data_generate,
    ],
)