import os
import logging
import pickle
import base64
import hashlib
import getpass
import platform
from cryptography.fernet import Fernet
from trino.dbapi import connect
from trino.auth import BasicAuthentication
import psutil

# --- CONFIG ---
DEFAULT_PICKLE = "trino_creds.pkl"
# Change these if you want different network gating
REQUIRED_INTERFACE = "Ethernet 3"
REQUIRED_IPV4 = "192.168.1.52"


class MaskedCreds(dict):
    def __getitem__(self, key):
        # allow access to real secrets by code; repr masks sensitive keys
        return super().__getitem__(key)

    def __repr__(self):
        masked = {k: ("***masked***" if k in ["TRINO_USER", "TRINO_PASSWORD"] else v)
                  for k, v in self.items()}
        return str(masked)


def email_to_fernet_key(email: str) -> bytes:
    """
    Derive a valid Fernet key from an email (deterministic).
    Fernet requires a urlsafe_base64-encoded 32-byte key -> we use SHA256(email) and base64.urlsafe_b64encode.
    """
    if not isinstance(email, str) or not email:
        raise ValueError("Email must be a non-empty string")
    digest = hashlib.sha256(email.strip().lower().encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)  # produces a valid 44-char base64 key usable by Fernet
    return key


def load_credentials_from_pickle(pickle_file: str, email_for_key: str):
    """
    Load and decrypt credentials from pickle_file using a key derived from email_for_key.
    Returns MaskedCreds (dict-like).
    """
    if not os.path.exists(pickle_file):
        raise FileNotFoundError(f"{pickle_file} not found")

    fernet_key = email_to_fernet_key(email_for_key)
    fernet = Fernet(fernet_key)

    with open(pickle_file, "rb") as f:
        encrypted_data = f.read()

    try:
        decrypted = fernet.decrypt(encrypted_data)
    except Exception as e:
        raise ValueError("Decryption failed — maybe wrong email/key or corrupted file") from e

    creds = pickle.loads(decrypted)
    if not isinstance(creds, dict):
        raise ValueError("Pickle did not contain a dict of credentials")

    if "JUPYTERHUB_USER" not in creds or not creds["JUPYTERHUB_USER"]:
        raise ValueError("User email (JUPYTERHUB_USER) must be present in pickle file")

    return MaskedCreds(creds)


def has_required_interface_ip(interface_name: str, ipv4_addr: str) -> bool:
    """
    Check if `interface_name` exists and has the given IPv4 address.
    """
    try:
        if_addrs = psutil.net_if_addrs()
    except Exception:
        return False
    addrs = if_addrs.get(interface_name)
    if not addrs:
        return False
    for a in addrs:
        if a.family.name == "AF_INET" or getattr(a.family, "name", "") == "AF_INET":
            # compare IPv4
            if a.address == ipv4_addr:
                return True
    return False


def fetch_trino_data(query: str, pickle_file: str = DEFAULT_PICKLE, entered_email: str = None):
    """
    Main entry:
      - ask for entered_email if not supplied
      - derive key, decrypt creds
      - check machine network interface gating
      - run query after injecting identifying comment
    """
    if entered_email is None:
        entered_email = input("Enter the email to derive the encryption key (used to decrypt creds): ").strip()

    if not entered_email:
        print("No email entered. Aborting.")
        return None

    # --- gate by network interface/IP ---
    if not has_required_interface_ip(REQUIRED_INTERFACE, REQUIRED_IPV4):
        print(f"Network check failed: required interface/IP not present. "
              f"Need {REQUIRED_INTERFACE} -> {REQUIRED_IPV4}. Aborting.")
        return None

    # --- load credentials ---
    try:
        creds = load_credentials_from_pickle(pickle_file, entered_email)
    except Exception as e:
        logging.error(f"Failed to load credentials: {e}")
        print(f"Failed to load credentials: {e}")
        return None

    # extract trino connection parameters
    try:
        user_name = creds["TRINO_USER"]
        password = creds["TRINO_PASSWORD"]
        host = creds["TRINO_HOST"]
        port = int(creds.get("TRINO_PORT", 443))
        http_scheme = creds.get("TRINO_HTTP_SCHEME", "https")
        jupyter_user_email = creds["JUPYTERHUB_USER"]
    except KeyError as ke:
        logging.error(f"Missing required Trino credential key: {ke}")
        print(f"Missing required Trino credential key: {ke}")
        return None

    # logged-in user and PC
    logged_user = getpass.getuser()
    pc_name = platform.node()

    # inject identifying comment — include both entered_email and JUPYTERHUB_USER and logged user and pc name
    comment = f"/*entered_email:{entered_email}, jupyter_user:{jupyter_user_email}, " \
              f"logged_user:{logged_user}, pc_name:{pc_name}*/ "
    modified_query = comment + query

    # connect to Trino and execute
    try:
        print(f"Connecting to Trino at {host}:{port} as {user_name} (jupyter_user={jupyter_user_email})")
        conn = connect(
            host=host,
            port=port,
            user=user_name,
            auth=BasicAuthentication(user_name, password),
            http_scheme=http_scheme,
        )
        cur = conn.cursor()
        cur.execute(modified_query)
        results = cur.fetchall()
        # If you prefer a DataFrame, return DataFrame (pandas optional)
        try:
            import pandas as pd
            columns = [desc[0] for desc in cur.description]
            df = pd.DataFrame(results, columns=columns)
            cur.close()
            conn.close()
            print("Query executed successfully.")
            return df
        except Exception:
            # fallback to raw results
            cur.close()
            conn.close()
            return results

    except Exception as e:
        logging.error(f"Error executing query: {e}")
        print(f"Error executing query: {e}")
        return None
