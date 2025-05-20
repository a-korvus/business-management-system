"""Test PasswordHasher from 'app_auth' app."""

from faker import Faker

from project.app_auth.application.interfaces import PasswordHasher
from project.app_auth.infrastructure.security import (
    CryptographyPasswordHasher,
    get_password_hasher,
    password_hasher,
)
from project.core.log_config import get_logger

logger = get_logger(__name__)


def test_encrypt_objects() -> None:
    """Test encryption-related objects mapping."""
    single_hasher = get_password_hasher()

    assert issubclass(CryptographyPasswordHasher, PasswordHasher)
    assert isinstance(password_hasher, CryptographyPasswordHasher)
    assert isinstance(single_hasher, CryptographyPasswordHasher)


def test_encrypt_password(fake_instance: Faker) -> None:
    """Test the password encryption toolkit."""
    plain_password: str = fake_instance.password()

    assert isinstance(plain_password, str)

    hasher = CryptographyPasswordHasher()
    hashed_password = hasher.hash_password(plain_password)
    password_mapping = hasher.verify_password(plain_password, hashed_password)

    assert plain_password != hashed_password
    assert password_mapping is True
