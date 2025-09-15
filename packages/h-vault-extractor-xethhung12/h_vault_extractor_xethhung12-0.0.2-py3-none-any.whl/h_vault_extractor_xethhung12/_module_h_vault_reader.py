import hvac
import os
from typing import List, Tuple, Any

def GetSecrets(vault_addr: str, role_id: str, secret_id: str, mount_point: str, secret_path: str, keys_to_extract: List[str]) -> dict:
    # 1. Basic input validation
    if not all([vault_addr, role_id, secret_id, secret_path]):
        raise Exception("Error: All required arguments (vault_addr, role_id, secret_id, secret_path) must be provided.")
    try:
        # 2. Authenticate with Vault
        client = hvac.Client(url=vault_addr)
        client.auth.approle.login(role_id=role_id, secret_id=secret_id)

        if not client.is_authenticated():
            raise Exception("AppRole login failed. Please check your credentials.")

        # 3. Read the entire secret from the specified path
        read_response = client.secrets.kv.read_secret_version(
            path=secret_path,
            mount_point=mount_point
        )

        if not read_response or 'data' not in read_response:
            raise Exception("Failed to read secret. Check the path and your permissions.")

        # 4. Extract the full data and return a subset if requested
        secret_data = read_response['data']['data']

        d={}
        for key in keys_to_extract:
            if key in secret_data:
                d[key] = secret_data.get(key)
        # extracted_values = tuple(secret_data.get(key) for key in keys_to_extract)
        return d

    except hvac.exceptions.InvalidRequest as e:
        raise Excepton(f"Authentication error: Invalid request - {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")


def LoadSecretsIntoEnv(
    vault_addr: str, role_id: str, secret_id: str, 
    mount_point: str, secret_path: str, keys_to_extract: List[dict]
):
    d = GetSecrets(validation, role_id, secret_id, mount_point, secret_path, keys_to_extract)
    for key in keys_to_extract:
        if key['VAULT_VALUE'] in d:
            print(f"Set env: {key['ENV_NAME']}")
            os.environ[key['ENV_NAME']] = d[key['VAULT_VALUE']]


def Pair(env_name:str, vault_vault: str):
    return {'VAULT_VALUE':vault_vault, "ENV_NAME": env_name}