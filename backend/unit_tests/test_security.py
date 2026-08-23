"""Unit tests for core security utilities."""
import pytest
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    hash_token, decode_access_token,
    generate_verification_token, generate_api_key,
)
from jose import JWTError


class TestPasswordHashing:
    def test_hash_is_argon2(self):
        h = hash_password("Pass@word1")
        assert h.startswith("$argon2")

    def test_hash_is_not_plaintext(self):
        h = hash_password("Pass@word1")
        assert h != "Pass@word1"

    def test_verify_correct(self):
        h = hash_password("Correct@1")
        assert verify_password("Correct@1", h) is True

    def test_verify_wrong(self):
        h = hash_password("Correct@1")
        assert verify_password("Wrong@1", h) is False

    def test_verify_empty(self):
        h = hash_password("Nonempty@1")
        assert verify_password("", h) is False

    def test_same_input_different_hash(self):
        h1, h2 = hash_password("Same@1"), hash_password("Same@1")
        assert h1 != h2  # argon2 salts differ
        assert verify_password("Same@1", h1) and verify_password("Same@1", h2)


class TestJWT:
    def test_round_trip(self):
        token = create_access_token("user-42")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-42"

    def test_type_claim(self):
        payload = decode_access_token(create_access_token("u"))
        assert payload["type"] == "access"

    def test_exp_and_iat_present(self):
        payload = decode_access_token(create_access_token("u"))
        assert "exp" in payload and "iat" in payload

    def test_extra_claims(self):
        token = create_access_token("u", extra_claims={"wid": "ws-1"})
        assert decode_access_token(token)["wid"] == "ws-1"

    def test_tampered_raises(self):
        token = create_access_token("u")
        with pytest.raises(JWTError):
            decode_access_token(token[:-4] + "XXXX")

    def test_garbage_raises(self):
        with pytest.raises(JWTError):
            decode_access_token("not.a.token")


class TestRefreshToken:
    def test_returns_two_distinct_strings(self):
        raw, hashed = create_refresh_token("u")
        assert isinstance(raw, str) and isinstance(hashed, str)
        assert raw != hashed

    def test_raw_token_long_enough(self):
        raw, _ = create_refresh_token("u")
        assert len(raw) >= 40

    def test_hash_is_deterministic(self):
        assert hash_token("xyz") == hash_token("xyz")

    def test_hash_differs_for_different_inputs(self):
        assert hash_token("a") != hash_token("b")

    def test_hash_is_sha256_hex_length(self):
        assert len(hash_token("anything")) == 64

    def test_bulk_uniqueness(self):
        tokens = {create_refresh_token("u")[0] for _ in range(50)}
        assert len(tokens) == 50


class TestHelpers:
    def test_verification_token_is_string(self):
        assert isinstance(generate_verification_token(), str)

    def test_verification_token_min_length(self):
        assert len(generate_verification_token()) >= 32

    def test_verification_tokens_unique(self):
        assert len({generate_verification_token() for _ in range(100)}) == 100

    def test_api_key_starts_with_atl(self):
        raw, _, _ = generate_api_key()
        assert raw.startswith("atl_")

    def test_api_key_prefix_matches(self):
        raw, prefix, _ = generate_api_key()
        assert raw.startswith(prefix)

    def test_api_key_hash_is_hex64(self):
        _, _, hashed = generate_api_key()
        assert len(hashed) == 64
        int(hashed, 16)  # valid hex
