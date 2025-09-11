import os
import logging
import pandas as pd
from dotenv import load_dotenv
from trino.dbapi import connect
from trino.auth import BasicAuthentication

# Automatically load .env
load_dotenv()

def fetch_trino_data(query, user_name=None, password=None):
    """
    Execute a Trino query securely and return a pandas DataFrame.
    
    Credentials can be provided in two ways:
    1. Passed directly as function arguments
    2. Set in a .env file as TRINO_USER and TRINO_PASSWORD

    Parameters:
        query (str): SQL query to execute
        user_name (str, optional): Trino username
        password (str, optional): Trino password
    
    Returns:
        pd.DataFrame: Query results
    """

    # Priority: function arguments > .env
    user_name = user_name or os.getenv("TRINO_USER")
    password = password or os.getenv("TRINO_PASSWORD")
    
    if not user_name or not password:
        raise ValueError(
            "Trino username and password must be provided either as arguments "
            "or in a .env file with TRINO_USER and TRINO_PASSWORD."
        )

    # Optional: track JupyterHub user
    user_email = os.getenv('JUPYTERHUB_USER', 'default.user@example.com')
    modified_query = f'/*user:{user_email}*/ {query}'

    print(f"Connected to Trino as: {user_name}")

    try:
        conn = connect(
            host=os.getenv("TRINO_HOST", "kdbc.dbc.co"),
            port=int(os.getenv("TRINO_PORT", 443)),
            user=user_name,
            auth=BasicAuthentication(user_name, password),
            http_scheme=os.getenv("TRINO_HTTP_SCHEME", "https")
        )
        cur = conn.cursor()
        cur.execute(modified_query)
        results = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(results, columns=columns)
        cur.close()
        conn.close()
        print("Execution successful")
        return df

    except Exception as e:
        logging.error(f"Error executing query: {str(e)}")
        return None
