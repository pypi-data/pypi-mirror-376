import os
import pytest

from aneSettings.Encryption import Encryption


@pytest.fixture
def encryption_instance():
    """Fixture for creating an Encryption instance."""
    return Encryption(key=Encryption.generate_fernet_key())


def test_initialization_with_bytes_key():
    """Test initialization with a byte key."""
    key = b"test_key_value"
    encryption = Encryption(key=key)
    assert encryption.key == key


def test_initialization_with_string_key():
    """Test initialization with a string key."""
    key = "test_key_value"
    encryption = Encryption(key=key)
    assert encryption.key == key.encode()


def test_generate_fernet_key():
    """Test generating a Fernet key."""
    key = Encryption.generate_fernet_key()
    assert isinstance(key, bytes)


def test_generate_salt_and_key_with_salt():
    """Test generating salt and key with a provided salt."""
    password = "test_password"
    salt = os.urandom(16)
    salt_encoded, key_encoded = Encryption.generate_salt_and_key(password, salt=salt)
    assert isinstance(salt_encoded, str)
    assert isinstance(key_encoded, str)


def test_generate_salt_and_key_without_salt():
    """Test generating salt and key without a provided salt."""
    password = "test_password"
    salt_encoded, key_encoded = Encryption.generate_salt_and_key(password)
    assert isinstance(salt_encoded, str)
    assert isinstance(key_encoded, str)


def test_encrypt(encryption_instance):
    """Test encryption of plaintext."""
    plaintext = "test_plaintext"
    ciphertext = encryption_instance.encrypt(plaintext)
    assert isinstance(ciphertext, bytes)


def test_decrypt(encryption_instance):
    """Test decryption of ciphertext."""
    plaintext = "test_plaintext"
    ciphertext = encryption_instance.encrypt(plaintext)
    decrypted_text = encryption_instance.decrypt(ciphertext)
    assert decrypted_text == plaintext


def test_decrypt_invalid_token(encryption_instance):
    """Test decryption with invalid token."""
    invalid_ciphertext = b"invalid_ciphertext"
    decrypted_text = encryption_instance.decrypt(invalid_ciphertext)
    assert decrypted_text == "InvalidToken"


def test_base64_encode():
    """Test Base64 encoding of data."""
    data = "test_data"
    encoded_data = Encryption.base64_encode(data)
    assert isinstance(encoded_data, str)


def test_base64_decode():
    """Test Base64 decoding of data."""
    data = "test_data"
    encoded_data = Encryption.base64_encode(data)
    decoded_data = Encryption.base64_decode(encoded_data)
    assert decoded_data == data


def test_is_base64_encoded_valid_base64():
    """Test is_base64_encoded returns True for valid Base64 strings."""
    valid_base64 = "U29tZSByYW5kb20gdmFsaWQgZGF0YQ=="
    assert Encryption.is_base64_encoded(valid_base64) is True


def test_is_base64_encoded_invalid_base64():
    """Test is_base64_encoded returns False for invalid Base64 strings."""
    invalid_base64 = "Invalid base64 data###"
    assert Encryption.is_base64_encoded(invalid_base64) is False


def test_is_base64_encoded_empty_string():
    """Test is_base64_encoded returns False for empty string."""
    empty_string = ""
    assert Encryption.is_base64_encoded(empty_string) is False


def test_is_base64_encoded_whitespace_string():
    """Test is_base64_encoded returns False for string with only whitespace."""
    whitespace_string = "    "
    assert Encryption.is_base64_encoded(whitespace_string) is False


def test_is_base64_encoded_non_string_input():
    """Test is_base64_encoded returns False for non-string input."""
    non_string_input = 12345  # Example with an integer
    assert Encryption.is_base64_encoded(non_string_input) is False
