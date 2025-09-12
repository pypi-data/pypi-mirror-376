import base64
import hashlib
import json
import platform
import socket
import uuid
from getpass import getpass

from cryptography.fernet import Fernet


def key32_from_string_sha256(user_key: str) -> bytes:
    raw32 = hashlib.sha256(user_key.encode("utf-8")).digest()
    return raw32


def fernet_key_from_string_sha256(user_key: str) -> bytes:
    raw32 = key32_from_string_sha256(user_key)
    return base64.urlsafe_b64encode(raw32)


def generate_key(user_key: str = None, from_system: bool = True) -> bytes:
    """
    Generate a Fernet-compatible encryption key.

    Args:
        user_key (str): Optional user-provided key for personalization.
        from_system (bool): If True, bind key to system info.

    Returns:
        bytes: A Fernet-compatible key.
    """
    if user_key is None:
        user_key = ""

    if from_system:
        system_name = platform.system()
        hostname = socket.gethostname()
        architecture = platform.machine()
        mac_address = str(uuid.getnode())
        system_info = f"{user_key}{system_name}{hostname}{mac_address}{architecture}"
        hashed_info = hashlib.sha256(system_info.encode()).digest()
        key = base64.urlsafe_b64encode(hashed_info[:32])
    else:
        key = fernet_key_from_string_sha256(user_key)

    return key


def pass_account() -> dict:
    """
    Prompt user for username and password via terminal.

    Returns:
        dict: Dictionary with 'username' and 'password' keys.
    """
    username = input("Username: ")
    password = getpass()
    return {"username": username, "password": password}


def encrypt(content: str | bytes | dict, key: str | bytes = None, **kwargs) -> bytes:
    """
    Encrypt the given content using a Fernet key.

    Args:
        content (str | bytes | dict): The content to encrypt.
        key (str | bytes): Encryption key (if None, auto-generated).

    Returns:
        bytes: The encrypted content.
    """
    if content is None:
        content = {}
    if isinstance(content, dict):
        content = json.dumps(content)
    if isinstance(content, str):
        content = content.encode()
    if key is None:
        key = generate_key(**kwargs)
    cipher = Fernet(key)
    return cipher.encrypt(content)


def decrypt(content: str | bytes, key: str | bytes = None, to_dict: bool = False, **kwargs) -> bytes | dict:
    """
    Decrypt encrypted content using a Fernet key.

    Args:
        content (str | bytes): Encrypted content.
        key (str | bytes): Encryption key (if None, auto-generated).
        to_dict (bool): Whether to parse decrypted content as JSON.

    Returns:
        bytes | dict: Decrypted raw bytes or dict.
    """
    if isinstance(content, str):
        content = content.encode()
    if key is None:
        key = generate_key(**kwargs)
    cipher = Fernet(key)
    decrypted_content = cipher.decrypt(content)
    if to_dict:
        decrypted_content = json.loads(decrypted_content)
    return decrypted_content


def save(content: str | bytes | dict, file: str = None, key: str | bytes = None, **kwargs) -> bytes:
    """
    Encrypt and save content to a file.

    Args:
        content (str | bytes | dict): The content to encrypt and save.
        file (str): File path.
        key (str | bytes): Optional encryption key.

    Returns:
        bytes: Encrypted content.
    """
    if file is None:
        file = "./account.key"
    encrypted_content = encrypt(content=content, key=key, **kwargs)
    with open(file, "wb") as f:
        f.write(encrypted_content)
    return encrypted_content


def load(file: str = None, key: str | bytes = None, to_dict: dict = True, **kwargs) -> bytes | dict:
    """
    Load and decrypt content from a file.

    Args:
        file (str): File path to read from.
        key (str | bytes): Optional decryption key.
        to_dict (bool): Whether to decode JSON.

    Returns:
        bytes | dict: Decrypted content.
    """
    if file is None:
        file = "./account.key"
    with open(file, "rb") as f:
        content = f.read()
    decrypted_content = decrypt(content, key=key, to_dict=to_dict, **kwargs)
    return decrypted_content
