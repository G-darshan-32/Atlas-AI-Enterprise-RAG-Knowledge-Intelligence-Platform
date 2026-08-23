"""Unit tests for security utilities."""
import pytest
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, hash_token, decode_access_token,
    generate_verification_token, generate_api_key
)
from jose import JWTError
import time


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("MySecret@1")
        assert hashed != "MySecret@1"

    def test_verify_correct_password(self):
        hashed = hash_password("MySecret@1")
        assert verify_password("MySecret@1", hashed) is True

    def test_reject_wrong_password(self):
        hashed = hash_password("MySecret@1")
        assert verify_password("WrongPassword", hashed) is False

    def test_different_hashes_same_input(self):
        # bcrypt uses salt so same input produces different hashes
        h1 = hash_password("Same@Pass1")
        h2 = hash_password("Same@Pass1")
        assert h1 != h2
        assert verify_password("Same@Pass1", h1)
        assert verify_password("Same@Pass1", h2)


class TestJWT:
    def test_create_and_decode_access_token(self):
        token = create_access_token(subject="user-123")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_token_has_expiry(self):
        token = create_access_token(subject="user-456")
        payload = decode_access_token(token)
        assert "exp" in payload

    def test_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_access_token("not.a.valid.jwt")

    def test_extra_claims(self):
        token = create_access_token(subject="user-789", extra_claims={"workspace_id": "ws-1"})
        payload = decode_access_token(token)
        assert payload["workspace_id"] == "ws-1"


class TestRefreshToken:
    def test_create_refresh_token_returns_tuple(self):
        raw, hashed = create_refresh_token(subject="user-1")
        assert isinstance(raw, str)
        assert isinstance(hashed, str)
        assert raw != hashed
        assert len(raw) > 40

    def test_hash_token_is_deterministic(self):
        token = "some_secret_token"
        h1 = hash_token(token)
        h2 = hash_token(token)
        assert h1 == h2

    def test_hash_token_different_for_different_tokens(self):
        h1 = hash_token("token_a")
        h2 = hash_token("token_b")
        assert h1 != h2


class TestHelpers:
    def test_generate_verification_token_is_string(self):
        token = generate_verification_token()
        assert isinstance(token, str)
        assert len(token) > 20

    def test_generate_verification_tokens_are_unique(self):
        tokens = {generate_verification_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_generate_api_key_format(self):
        raw, prefix, hashed = generate_api_key()
        assert raw.startswith("atl_")
        assert raw[:len(prefix)] == prefix
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA-256 hex
