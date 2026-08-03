FROM spark:4.1.2-scala2.13-java17-python3-ubuntu

USER root

WORKDIR /opt/spark-app

COPY . /opt/spark-app/

ADD https://jdbc.postgresql.org/download/postgresql-42.7.7.jar \
    /opt/spark/jars/postgresql-42.7.7.jar

RUN chown -R spark:spark /opt/spark-app \
    && chown spark:spark /opt/spark/jars/postgresql-42.7.7.jar

USER spark

CMD ["/opt/spark/bin/spark-submit", \
     "--master", "spark://spark-master:7077", \
     "--deploy-mode", "client", \
     "--name", "silver-customer-cleansing", \
     "--jars", "/opt/spark/jars/postgresql-42.7.7.jar", \
     "--driver-memory", "2g", \
     "--executor-cores", "4", \
     "--executor-memory", "3g", \
     "--total-executor-cores", "4", \
     "--conf", "spark.sql.shuffle.partitions=16", \
     "--conf", "spark.sql.adaptive.enabled=true", \
     "--conf", "spark.sql.adaptive.coalescePartitions.enabled=true", \
     "/opt/spark-app/main.py"]