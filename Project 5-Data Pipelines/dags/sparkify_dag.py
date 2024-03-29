from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators import (StageToRedshiftOperator, LoadFactOperator,
                                DataQualityOperator,LoadDimensionOperator)
from helpers import SqlQueries

# AWS_KEY = os.environ.get('AWS_KEY')
# AWS_SECRET = os.environ.get('AWS_SECRET')

start_date = datetime.utcnow()

#Define deafult parameters to configure DAG
default_args = {
    'owner': 'udacity',
    'start_date': start_date,
    'end_date' : datetime(2023, 5, 1),
    'depends_on_past' : False,
    'retries' : 3,
    'retry_delay' : timedelta(minutes=5),
    'catchup' : False,
    'email_on_retry' : False
}

#dag configuration 
dag_name = 'sparkify_dag'
dag = DAG(dag_name,
          default_args=default_args,
          description='Load and transform data in Redshift with Airflow',
          schedule_interval='0 * * * *',
          max_active_runs=1
        )

#Define Start Operator
start_operator = DummyOperator(task_id='Begin_execution',dag=dag)
   
#Load Log data from S3 to staging table(staging_events) in Redshift
stage_events_to_redshift = StageToRedshiftOperator(
    task_id='Stage_events',
    dag=dag,
    provide_context=True,
    table="staging_events",
    redshift_conn_id="Redshift",
    aws_credentials_id="aws_credentials",
    s3_bucket="udacity_dend",
    s3_key="song_data/A/A/A",
    region="us-west-2",
    file_format="JSON",
    
)

#Load Song data from S3 to staging table(staging_songs) in Redshift
stage_songs_to_redshift = StageToRedshiftOperator(
    task_id='Stage_songs',
    dag=dag,
    provide_context=True,
    table="staging_songs",
    redshift_conn_id="Redshift",
    aws_credentials_id="aws_credentials",
    s3_bucket="udacity_dend",
    s3_key="song_data",
    region="us-west-2",
    file_format="JSON",
)

#Load the fact table - songplays from the staging tables
load_songplays_table = LoadFactOperator(
    task_id='Load_songplays_fact_table',
    dag=dag,
    provide_contecxt=True,
    aws_credentials_id="aws_credentials",
    redshift_conn_id="Redshift",
    sql_query=SqlQueries.songplay_table_insert
)

#Load dimension table - users from staging tables(staging_events)
load_user_dimension_table = LoadDimensionOperator(
    task_id='Load_user_dim_table',
    dag=dag,
    provide_context=True,
    redshift_conn_id="Redshift",
    sql_query=SqlQueries.user_table_insert,
    table="users",
    truncate=True
)

#Load dimension table - Songs from staging tables(staging songs)
load_song_dimension_table = LoadDimensionOperator(
    task_id='Load_song_dim_table',
    dag=dag,
    provide_context=True,
    redshift_conn_id="Redshift",
    sql_query=SqlQueries.song_table_insert,
    table="songs",
    truncate=True
    
)

#Load dimension table - Artists from staging tables(staging_songs)
load_artist_dimension_table = LoadDimensionOperator(
    task_id='Load_artist_dim_table',
    dag=dag,
    provide_context=True,
    redshift_conn_id="Redshift",
    sql_query=SqlQueries.artist_table_insert,
    table="artists",
    truncate=True
)

#Load dimension table - Time from songplays
load_time_dimension_table = LoadDimensionOperator(
    task_id='Load_time_dim_table',
    dag=dag,
    provide_context=True,
    redshift_conn_id="Redshift",
    sql_query=SqlQueries.time_table_insert,
    table="time",
    truncate=True
)

#Run checks on the data
run_quality_checks = DataQualityOperator(
    task_id='Run_data_quality_checks',
    redshift_conn_id='redshift',
    test_query='select count(*) from songs where songid is null;',
    expected_result=0,
    dag=dag
)

#Define end operator
end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)

# Setting tasks dependencies
start_operator >> [stage_events_to_redshift,stage_songs_to_redshift]
[stage_events_to_redshift,stage_songs_to_redshift] >> load_songplays_table
load_songplays_table >> [load_user_dimension_table,load_song_dimension_table,load_artist_dimension_table,load_time_dimension_table]
[load_user_dimension_table,load_song_dimension_table,load_artist_dimension_table,load_time_dimension_table] >> run_quality_checks
run_quality_checks >> end_operator

