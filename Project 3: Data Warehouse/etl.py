import configparser
import psycopg2
from sql_queries import copy_table_queries, insert_table_queries


def load_staging_tables(cur, conn):
    '''
    Load data from S3 to staging tables on Redshift and load data queries in copy_table_queries.
    '''
    for query in copy_table_queries:
        cur.execute(query)
        conn.commit()


def insert_tables(cur, conn):
    '''
    Insert data into fact and dimesion tables from the staging tables on Redshift using queries in
    insert_table_queries
    '''
    for query in insert_table_queries:
        cur.execute(query)
        conn.commit()


def main():
    """
    - reads dwh.cfg file 
    
    - Establishes connection with the redshift database using the cluster details defined in dwh.cfg       and assign a cursor to it.  
    
    - Load data from S3 to staging tables on Redshift.  
    
    - Creates all tables needed. 
    
    - Finally, closes the connection. 
    """
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))
    cur = conn.cursor()
    
    load_staging_tables(cur, conn)
    insert_tables(cur, conn)

    conn.close()


if __name__ == "__main__":
    main()