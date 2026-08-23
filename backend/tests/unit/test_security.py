"""Unit tests for security utilities — no DB, no HTTP required."""
import sys
import os

# Patch env before any app imports so Settings() doesn't fail
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DATABASE_SYNC_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum!!")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-real")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_ACCESS_KEY", "test")
os.environ.setdefault("S3_SECRET_KEY", "test")
os.environ.setdefault("S3_BUCKET_NAME", "test")

import pytest
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    hash_token, decode_access_token,
    generate_verification_token, generate_api_key,
)
from jose import JWTError


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("MySecret@1")
        assert hashed != "MySecret@1"
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        hashed = hash_password("MySecret@1")
        assert verify_password("MySecret@1", hashed) is True

    def test_reject_wrong_password(self):
        hashed = hash_password("MySecret@1")
        assert verify_password("WrongPassword", hashed) is False

    def test_different_hashes_same_input(self):
        h1 = hash_password("Same@Pass1")
        h2 = hash_password("Same@Pass1")
        assert h1 != h2          # bcrypt salts differ
        assert verify_password("Same@Pass1", h1)
        assert verify_password("Same@Pass1", h2)

    def test_empty_password_does_not_match_hash(self):
        hashed = hash_password("Secure@Pass1")
        assert verify_password("", hashed) is False


class TestJWT:
    def test_create_and_decode_access_token(self):
        token = create_access_token(subject="user-123")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_extra_claims_preserved(self):
        token = create_access_token(subject="user-789", extra_claims={"role": "admin"})
        payload = decode_access_token(token)
        assert payload["role"] == "admin"

    def test_tampered_token_raises(self):
        token = create_access_token(subject="user-1")
        bad = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_access_token(bad)

    def test_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_access_token("not.a.valid.jwt")

    def test_empty_token_raises(self):
        with pytest.raises(JWTError):
            decode_access_token("")


class TestRefreshToken:
    def test_returns_raw_and_hash(self):
        raw, hashed = create_refresh_token(subject="u1")
        assert isinstance(raw, str)
        assert isinstance(hashed, str)
        assert raw != hashed
        assert len(raw) > 40

    def test_hash_is_deterministic(self):
        assert hash_token("abc") == hash_token("abc")

    def test_hash_differs_for_different_inputs(self):
        assert hash_token("a") != hash_token("b")

    def test_hash_length_is_64(self):
        # SHA-256 hex = 64 chars
        assert len(hash_token("any_token")) == 64

    def test_tokens_are_unique(self):
        tokens = {create_refresh_token(subject="u")[0] for _ in range(50)}
        assert len(tokens) == 50


class TestHelpers:
    def test_verification_token_is_urlsafe_string(self):
        t = generate_verification_token()
        assert isinstance(t, str)
        assert len(t) >= 32
        # urlsafe base64 — no +, /
        assert "+" not in t
        assert "/" not in t

    def test_verification_tokens_are_unique(self):
        tokens = {generate_verification_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_api_key_format(self):
        raw, prefix, hashed = generate_api_key()
        assert raw.startswith("atl_")
        assert raw[:len(prefix)] == prefix
        assert len(hashed) == 64

    def test_api_key_prefix_is_first_12_chars(self):
        raw, prefix, _ = generate_api_key()
        assert prefix == raw[:12]
