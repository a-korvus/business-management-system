"""Implementation of the PasswordHasher interface.

Using 'Argon2id' from the 'cryptography' library.
"""

import base64
import os
from functools import lru_cache

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

from project.app_auth.application.interfaces import PasswordHasher
from project.app_auth.domain.exceptions import InvalidPasswordFormatError
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)


class CryptographyPasswordHasher(PasswordHasher):
    """Implementation password hasher using 'cryptography' and 'Agron2id'.

    Stores salt and hash in one string <base64(salt):base64(hash)>.
    """

    def __init__(
        self,
        time_cost: int = settings.AUTH.ARGON2_TIME_COST,
        memory_cost: int = settings.AUTH.ARGON2_MEMORY_COST,
        parallelism: int = settings.AUTH.ARGON2_PARALLELISM,
        salt_length: int = settings.AUTH.ARGON2_SALT_LENGTH,
        hash_length: int = settings.AUTH.ARGON2_HASH_LENGTH,
    ) -> None:
        """Initialize the password hasher."""
        self.time_cost = time_cost
        self.memory_cost = memory_cost
        self.parallelism = parallelism
        self.salt_length = salt_length
        self.hash_length = hash_length

    def _get_argon2_instance(self, salt: bytes) -> Argon2id:
        """Create an 'Argon2id' instance with current parameters.

        Args:
            salt (bytes): Random value.

        Returns:
            Argon2id: Configured Argon2id object.
        """
        return Argon2id(
            salt=salt,
            length=self.hash_length,
            iterations=self.time_cost,
            lanes=self.parallelism,
            memory_cost=self.memory_cost,
        )

    def hash_password(self, plain_pswrd: str) -> str:
        """Hash the password using Argon2id.

        Args:
            plain_pswrd (str): User input.

        Returns:
            str: 'salt:hash' as base64.
        """
        if not plain_pswrd:
            raise ValueError("Password cannot be empty.")

        salt: bytes = os.urandom(self.salt_length)
        argon2: Argon2id = self._get_argon2_instance(salt)
        hashed_pswrd_b: bytes = argon2.derive(plain_pswrd.encode("utf-8"))

        # кодируем соль и хеш в base64 и объединяем через ':'
        salt_b64 = base64.urlsafe_b64encode(salt).decode("utf-8")
        hash_b64 = base64.urlsafe_b64encode(hashed_pswrd_b).decode("utf-8")

        return f"{salt_b64}:{hash_b64}"

    def verify_password(self, plain_pswrd: str, stored_pswrd: str) -> bool:
        """Check the hash of the entered password is equal to the saved one.

        Args:
            plain_pswrd (str): User input.
            stored_pswrd (str): Stored encrypted password with salt.

        Returns:
            bool: Comparison result.
        """
        if not plain_pswrd or not stored_pswrd:
            return False

        try:
            salt_b64, hash_b64 = stored_pswrd.split(":", 1)

            salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
            stored_hash_b = base64.urlsafe_b64decode(hash_b64.encode("utf-8"))
        except (ValueError, TypeError):
            # строка не парсится или base64 некорректен
            raise InvalidPasswordFormatError(
                msg="Could not parse stored password",
            ) from None

        if len(stored_hash_b) != self.hash_length:
            raise InvalidPasswordFormatError(
                msg="Stored hash has incorrect length",
            )

        argon2 = self._get_argon2_instance(salt)
        try:
            # InvalidKey, если хеши не совпадают
            argon2.verify(plain_pswrd.encode("utf-8"), stored_hash_b)
            return True
        except InvalidKey:
            return False
        except Exception:  # noqa
            logger.exception("Unexpected error during password verification")
            return False


password_hasher = CryptographyPasswordHasher()


@lru_cache(maxsize=1)
def get_password_hasher() -> PasswordHasher:
    """Get the only one password hasher instance."""
    return password_hasher  # singleton
