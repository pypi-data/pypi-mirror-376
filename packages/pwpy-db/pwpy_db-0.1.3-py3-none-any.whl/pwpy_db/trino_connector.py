import os
import logging
import pandas as pd
import pickle
from cryptography.fernet import Fernet
from trino.dbapi import connect
from trino.auth import BasicAuthentication

KEY_FILE = "secret.key"  # Your encryption key

def load_credentials(pickle_file, key_file=KEY_FILE):
    """
    Load and decrypt Trino credentials from a pickle file using Fernet secret.key.
    """
    if not os.path.exists(key_file):
        raise FileNotFoundError(f"{key_file} not found")
    
    # Read the encryption key
    with open(key_file, "rb") as f:
        key = f.read()
    fernet = Fernet(key)

    if not os.path.exists(pickle_file):
        raise FileNotFoundError(f"{pickle_file} not found")
    
    # Read encrypted pickle file
    with open(pickle_file, "rb") as f:
        encrypted_data = f.read()

    # Decrypt and unpickle
    decrypted_data = fernet.decrypt(encrypted_data)
    creds = pickle.loads(decrypted_data)

    # Ensure email exists
    if "JUPYTERHUB_USER" not in creds or not creds["JUPYTERHUB_USER"]:
        raise ValueError("User email (JUPYTERHUB_USER) must be present in pickle file")

    # Optionally: mask credentials if user tries to print
    class MaskedCreds(dict):
        def __getitem__(self, key):
            if key in ["TRINO_USER", "TRINO_PASSWORD"]:
                return super().__getitem__(key)
            return super().__getitem__(key)
        def __repr__(self):
            masked = {k: ("***masked***" if k in ["TRINO_USER", "TRINO_PASSWORD"] else v)
                      for k, v in self.items()}
            return str(masked)
    return MaskedCreds(creds)

def fetch_trino_data(query, pickle_file=None):
    """
    Execute a Trino query securely using credentials from an encrypted pickle file.
    User email is mandatory.

    Parameters:
        query (str): SQL query
        pickle_file (str): Path to .pkl file (dynamic, e.g., kamlesh.pkl, ayushq.pkl)
                            If None, defaults to trino_creds.pkl
    """
    if pickle_file is None:
        pickle_file = "trino_creds.pkl"

    try:
        creds = load_credentials(pickle_file)
        user_name = creds["TRINO_USER"]
        password = creds["TRINO_PASSWORD"]
        host = creds["TRINO_HOST"]
        port = creds.get("TRINO_PORT", 443)
        http_scheme = creds.get("TRINO_HTTP_SCHEME", "https")
        user_email = creds["JUPYTERHUB_USER"]

        modified_query = f'/*user:{user_email}*/ {query}'
        print(f"Connected to Trino as: {user_name} (email: {user_email})")

        conn = connect(
            host=host,
            port=int(port),
            user=user_name,
            auth=BasicAuthentication(user_name, password),
            http_scheme=http_scheme,
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
