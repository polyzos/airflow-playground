from urllib import request

import airflow
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.postgres_operator import PostgresOperator

def _get_data(output_path, **context):
    year, month, day, hour, *_ = context["execution_date"].timetuple()
    url = (
        "https://dumps.wikimedia.org/other/pageviews/"
        f"{year}/{year}-{month:02}/pageviews-{year}{month:02}{day:02}-{hour:02}0000.gz"
    )
    print(output_path)
    request.urlretrieve(url, output_path)


def _fetch_pageviews(pagenames, execution_date, **_):
    result = dict.fromkeys(pagenames, 0)
    with open("/usr/local/airflow/data_dir/wikipageviews", "r") as f:
        for line in f:
            domain_code, page_title, view_counts, _ = line.split(" ")
            if domain_code == "en" and page_title in pagenames:
                result[page_title] = view_counts

    with open("/usr/local/airflow/data_dir/pg_insert.sql", "w") as f:
        for pagename, pageviewcount in result.items():
            f.write(
                f"INSERT INTO page_view_counts VALUES ('{pagename}', {pageviewcount}, '{execution_date}');\n"
            )


with DAG(dag_id="stocksense",
         start_date=airflow.utils.dates.days_ago(1),
         schedule_interval='@hourly',
         #template_searchpath=['/usr/local/airflow/data_dir']
         ) as dag:
    get_data = PythonOperator(
        task_id="get_data",
        python_callable=_get_data,
        provide_context=True,
        op_args= {
            "output_path": "/usr/local/airflow/data_dir/wikipageviews.gz"
        },
    )

    extract_gz = BashOperator(
        task_id="extract_gz",
        bash_command="gunzip --force /usr/local/airflow/data_dir/wikipageviews.gz",
    )

    fetch_pageviews = PythonOperator(
        task_id="fetch_pageviews",
        python_callable=_fetch_pageviews,
        op_kwargs={
            "pagenames": {
                "Google", "Amazon", "Apple", "Microsoft", "Facebook"
            },
            "execution_date": "{{execution_date}}"
        },
    )

    create_pg_table = PostgresOperator(
        task_id="create_pg_table",
        postgres_conn_id="pg_conn",
        sql="create_table.sql",
    )

    write_to_postgres = PostgresOperator(
        task_id="write_to_postgres",
        postgres_conn_id="pg_conn",
        sql="data_dir/pg_insert.sql",
    )

    get_data >> fetch_pageviews >> create_pg_table >> write_to_postgres