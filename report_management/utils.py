import psycopg2 # For PostgreSQL. Install with: pip install psycopg2-binary
                # If using other databases, you'll need the respective driver and logic.

def verify_database_connection(host, port, dbname, user, password, timeout=5):
    """
    Attempts to connect to a PostgreSQL database with the given credentials.

    Args:
        host (str): The database host.
        port (int): The database port.
        dbname (str): The name of the database.
        user (str): The database username.
        password (str): The database password.
        timeout (int): Connection timeout in seconds.

    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname=dbname, user=user, password=password, connect_timeout=timeout
        )
        conn.close()
        return True
    except psycopg2.Error:  # Catching base psycopg2 error for connection issues
        return False
    except Exception: # Catch any other unexpected errors
        return False

def execute_sql_query(host, port, dbname, user, password, sql_query, timeout=30):
    """
    Connects to a PostgreSQL database, executes a given SQL query, and returns results.

    Args:
        host (str): The database host.
        port (int): The database port.
        dbname (str): The name of the database.
        user (str): The database username.
        password (str): The database password.
        sql_query (str): The SQL query to execute.
        timeout (int): Connection and query execution timeout in seconds.

    Returns:
        tuple: (column_names, data_rows) if successful.
    Raises:
        psycopg2.Error: If any database error occurs.
        Exception: For other unexpected errors.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname=dbname, user=user, password=password, connect_timeout=timeout
        )
        with conn.cursor() as cur:
            cur.execute(sql_query)
            column_names = [desc[0] for desc in cur.description]
            data_rows = cur.fetchall()
            return column_names, data_rows
    finally:
        if conn:
            conn.close()