from airflow import DAG
from datetime import datetime, timedelta

from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.postgres_operator import PostgresOperator

from helper import preprocess_data

default_args = {
    'owner': 'Airflow',
    'start_date': datetime(2020, 4, 17),
    'retries': 1,
    'retry_delay': timedelta(seconds=5)
}

dag = DAG(
    'store_dag',
    default_args=default_args,
    schedule_interval='@daily',
    template_searchpath=['/usr/local/airflow/data_dir'],
    catchup=False
)

task1 = BashOperator(
    task_id='check_file_exists',
    bash_command='shasum ~/data_dir/raw_store_transactions.csv',
    retries=2,
    retry_delay=timedelta(seconds=15),
    dag=dag
)

task2 = PythonOperator(
    task_id="preprocess_raw_transactions",
    python_callable=preprocess_data,
    dag=dag
)

task3 = PostgresOperator(
    task_id="create_pg_tables",
    postgres_conn_id="pg_conn",
    sql="create_tables.sql",
    dag=dag
)

task4 = PostgresOperator(
    task_id="store_data_in_pg",
    postgres_conn_id="pg_conn",
    sql="insert.sql",
    dag=dag
)
task1 >> task2 >> task3 >> task4