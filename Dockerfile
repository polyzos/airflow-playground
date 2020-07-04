FROM apache/airflow:1.10.10.1-alpha2-python3.7

COPY dags $AIRFLOW_HOME/dags