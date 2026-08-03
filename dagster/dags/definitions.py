import dagster as dg
from dagster_docker import execute_docker_container


DOCKER_NETWORK = "dagster-vs-airflow-network"


# --------------------------------------------------
# Existing raw.customer table
# --------------------------------------------------

raw_customer = dg.AssetSpec(
    key=dg.AssetKey(
        [
            "raw",
            "customer",
        ]
    ),
    group_name="raw",
    description="Existing raw customer table in PostgreSQL.",
    metadata={
        "database": "source",
        "schema": "raw",
        "table": "customer",
    },
)


# --------------------------------------------------
# Silver customer asset
# --------------------------------------------------

@dg.asset(
    key=dg.AssetKey(
        [
            "silver",
            "silver_customer",
        ]
    ),

    # Creates the lineage:
    # raw.customer -> silver.silver_customer
    deps=[
        raw_customer,
    ],

    group_name="silver",

    description=(
        "Customer table cleaned by Spark "
        "using the silver_job Docker image."
    ),

    metadata={
        "database": "source",
        "schema": "silver",
        "table": "silver_customer",
        "docker_image": "silver_job:latest",
        "processing_engine": "Apache Spark",
    },
)
def silver_customer(
    context: dg.AssetExecutionContext,
) -> dg.MaterializeResult:

    context.log.info(
        "Starting silver_job:latest Docker container..."
    )

    execute_docker_container(
        context=context.op_execution_context,
        image="silver_job:latest",
        networks=[
            DOCKER_NETWORK,
        ],
    )

    context.log.info(
        "Spark cleansing container completed successfully."
    )

    return dg.MaterializeResult(
        metadata={
            "source_table": "raw.customer",
            "target_table": "silver.silver_customer",
            "docker_image": "silver_job:latest",
            "processing_engine": "Apache Spark",
            "status": "completed",
        }
    )


# --------------------------------------------------
# Raw-to-silver job
# --------------------------------------------------

raw_to_silver_job = dg.define_asset_job(
    name="raw_to_silver_job",

    # Only silver is executed.
    # raw_customer appears as its upstream lineage.
    selection=dg.AssetSelection.assets(
        silver_customer,
    ),
)


# --------------------------------------------------
# Register everything with Dagster
# --------------------------------------------------

defs = dg.Definitions(
    assets=[
        raw_customer,
        silver_customer,
    ],

    jobs=[
        raw_to_silver_job,
    ],
)