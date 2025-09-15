import h_vault_extractor_xethhung12 as project
from j_vault_http_client_xethhung12 import client
import os
import argparse
import sys

def main():
    client.load_to_env()
    
    """
    Parses command-line arguments and uses the VaultExtractor library
    to retrieve secrets from HashiCorp Vault.
    """
    # Create the parser object with a helpful description
    parser = argparse.ArgumentParser(
        description="""
        A command-line tool to extract secrets from HashiCorp Vault using AppRole credentials.
        
        Example usage:
        python vault_extractor_cli.py --vault-addr http://localhost:8200 --role-id <your_role_id> --secret-id <your_secret_id> --path "my/app/secret" --keys "db_user" "db_password"
        """,
        formatter_class=argparse.RawTextHelpFormatter # Keeps the description formatting
    )

    # Add arguments for each required parameter
    parser.add_argument(
        "--vault-addr",
        required=True,
        help="The address of the HashiCorp Vault server (e.g., http://localhost:8200)."
    )
    
    parser.add_argument(
        "--role-id",
        required=True,
        help="The Role ID for AppRole authentication."
    )

    parser.add_argument(
        "--secret-id",
        required=True,
        help="The Secret ID for AppRole authentication."
    )

    parser.add_argument(
        "--path",
        required=True,
        help="The full path to the secret in Vault (e.g., my/app/secret)."
    )

    parser.add_argument(
        "--mount-point",
        default="secret",
        help="The mount point of the secret engine (defaults to 'secret')."
    )

    # For a list of keys, use nargs="+"
    parser.add_argument(
        "--keys",
        nargs="+",
        required=True,
        help="A space-separated list of keys to retrieve from the secret data."
    )

    # Parse the arguments from the command line
    args = parser.parse_args()
    
    d = project.GetSecrets(
        vault_addr=args.vault_addr, 
        role_id=args.role_id, 
        secret_id=args.secret_id, 
        mount_point=args.mount_point, secret_path=args.path,
        keys_to_extract=args.keys
    )
    for var1 in d:
        print(var1, d[var1])