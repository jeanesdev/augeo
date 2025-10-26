"""Unit tests for password hashing and verification.

Tests the password hashing utilities:
- Password hashing with bcrypt
- Password verification
- Hash strength (12+ rounds)
- Invalid password handling
"""

import pytest

from app.core.security import hash_password, verify_password


class TestPasswordHashing:
    """Unit tests for password hashing utilities."""

    def test_hash_password_creates_bcrypt_hash(self) -> None:
        """Test password is hashed using bcrypt algorithm.

        Verifies:
        - Hash starts with $2b$ (bcrypt identifier)
        - Hash is not equal to plaintext password
        """
        password = "SecurePass123"
        hashed = hash_password(password)

        # Bcrypt hashes start with $2b$ or $2a$
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        # Hash should not be the plaintext
        assert hashed != password

    def test_hash_password_is_deterministically_different(self) -> None:
        """Test same password generates different hashes (due to salt).

        Verifies:
        - Same password hashed twice produces different results
        - This is due to bcrypt's random salt
        """
        password = "SecurePass123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to salt
        assert hash1 != hash2

    def test_verify_password_correct_password(self) -> None:
        """Test correct password verification succeeds.

        Verifies:
        - Correct password returns True
        """
        password = "SecurePass123"
        hashed = hash_password(password)

        # Verification should succeed
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self) -> None:
        """Test incorrect password verification fails.

        Verifies:
        - Incorrect password returns False
        """
        password = "SecurePass123"
        wrong_password = "WrongPass456"
        hashed = hash_password(password)

        # Verification should fail
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(self) -> None:
        """Test password verification is case-sensitive.

        Verifies:
        - Password with different case fails verification
        """
        password = "SecurePass123"
        wrong_case = "securepass123"
        hashed = hash_password(password)

        # Verification should fail with different case
        assert verify_password(wrong_case, hashed) is False

    def test_hash_empty_password(self) -> None:
        """Test empty password can be hashed (validation should happen elsewhere).

        Verifies:
        - Empty string can be hashed (business logic should prevent this)
        """
        password = ""
        hashed = hash_password(password)

        # Should still create a valid bcrypt hash
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        # Verification should work
        assert verify_password(password, hashed) is True

    def test_hash_long_password(self) -> None:
        """Test very long passwords can be hashed.

        Verifies:
        - Passwords up to reasonable length can be hashed
        """
        password = "A" * 200  # Very long password
        hashed = hash_password(password)

        # Should still work
        assert verify_password(password, hashed) is True

    def test_hash_special_characters(self) -> None:
        """Test passwords with special characters are handled correctly.

        Verifies:
        - Special characters don't break hashing
        """
        passwords = [
            "P@ssw0rd!",
            "Test#123$%^",
            "emoji😀pass",
            "unicode→←↑↓",
            "quotes'\"pass",
        ]

        for password in passwords:
            hashed = hash_password(password)
            assert verify_password(password, hashed) is True

    def test_verify_invalid_hash_format(self) -> None:
        """Test verification with invalid hash format raises error.

        Verifies:
        - Invalid hash format is handled appropriately
        """
        password = "SecurePass123"
        invalid_hashes = [
            "not_a_hash",
            "",
            "short",
            "$2b$12$",  # Incomplete bcrypt hash
        ]

        for invalid_hash in invalid_hashes:
            # Should raise ValueError or return False
            with pytest.raises((ValueError, Exception)):
                verify_password(password, invalid_hash)

    def test_bcrypt_work_factor(self) -> None:
        """Test bcrypt uses appropriate work factor (rounds).

        Verifies:
        - Hash uses at least 12 rounds (recommended minimum)
        """
        password = "SecurePass123"
        hashed = hash_password(password)

        # Extract rounds from bcrypt hash
        # Format: $2b$12$... where 12 is the rounds
        parts = hashed.split("$")
        rounds = int(parts[2])

        # Should use at least 12 rounds
        assert rounds >= 12

    def test_hash_preserves_utf8(self) -> None:
        """Test UTF-8 passwords are handled correctly.

        Verifies:
        - UTF-8 encoded passwords work correctly
        """
        utf8_passwords = [
            "пароль123",  # Cyrillic
            "密码123",  # Chinese
            "كلمة السر123",  # Arabic
            "パスワード123",  # Japanese
        ]

        for password in utf8_passwords:
            hashed = hash_password(password)
            assert verify_password(password, hashed) is True

    def test_timing_attack_resistance(self) -> None:
        """Test password verification takes consistent time.

        Verifies:
        - Verification time doesn't vary significantly (timing attack resistance)

        Note: This is a basic test. Bcrypt is designed to be timing-attack resistant,
        but comprehensive timing analysis requires more sophisticated testing.
        """
        import time

        password = "SecurePass123"
        hashed = hash_password(password)

        # Time correct password verification
        start = time.time()
        verify_password(password, hashed)
        correct_time = time.time() - start

        # Time incorrect password verification
        start = time.time()
        verify_password("WrongPass456", hashed)
        incorrect_time = time.time() - start

        # Times should be similar (within 50% variance)
        # This is a rough check; bcrypt is designed for constant-time comparison
        ratio = max(correct_time, incorrect_time) / min(correct_time, incorrect_time)
        assert ratio < 1.5  # Should be similar timing
