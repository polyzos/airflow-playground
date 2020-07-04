import json
import pathlib

import airflow
import requests
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

dag = DAG(
    dag_id="launchlib_aggregator",
    start_date=airflow.utils.dates.days_ago(5),     # The date at which the DAG should first start running
    schedule_interval='@daily'
)

fetch_data = BashOperator(
    task_id='fetch_data',
    bash_command="curl -o /opt/airflow/launches.json 'https://launchlibrary.net/1.4/launch?next=5&mode=verbose'",
    dag=dag,
)


def _get_pictures():
    # Ensure directory exists
    pathlib.Path("/opt/airflow/images").mkdir(parents=True, exist_ok=True)

    # download all images in launches.json
    with open('/opt/airflow/launches.json') as f:
        launches = json.load(f)
        image_urls = [launch['rocket']['imageURL'] for launch in launches['launches']]
        for image_url in image_urls:
            response = requests.get(image_url)
            image_filename = image_url.split('/')[-1]
            target_file = f'/opt/airflow/images/{image_filename}'
            with open(target_file, "wb") as f:
                f.write(response.content)
            print(f"Downloaded {image_url} to {target_file}")


get_pictures = PythonOperator(
    task_id='get_pictures',
    python_callable=_get_pictures,
    dag=dag,
)

notify = BashOperator(
    task_id='notify',
    bash_command='echo "There are now $(ls /opt/airflow/images/ | wc -l) images."',
    dag=dag,
)

fetch_data >> get_pictures >> notify