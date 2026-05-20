import keyring
from getpass import getpass
import consts

def get_or_save_api_key(provider_name: str) -> str:
    api_key = keyring.get_password(consts.APP_NAME, provider_name)

    if api_key:
        return api_key

    api_key = getpass(f"Enter your {provider_name} API key: ").strip()

    if not api_key:
        raise ValueError("No API key entered.")

    keyring.set_password(consts.APP_NAME, provider_name, api_key)

    return api_key