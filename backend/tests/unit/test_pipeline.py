"""Unit tests for the AI pipeline — no LLM calls, no DB, no HTTP."""
import sys
import os

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
from app.ai.pipeline.chunker import chunk_text, _clean_text
from app.ai.pipeline.extractor import (
    _extract_txt, _extract_markdown, _extract_csv, extract_text
)
from app.ai.agents.citation_agent import extract_source_refs


# ─── Chunker ────────────────────────────────────────────

class TestChunker:
    def test_basic_txt_chunking_returns_list(self):
        text = "This is a sentence. " * 200
        chunks = chunk_text(text, "txt")
        assert isinstance(chunks, list)
        assert len(chunks) > 0

    def test_every_chunk_has_required_keys(self):
        text = "word " * 600
        chunks = chunk_text(text, "txt")
        for c in chunks:
            assert "content" in c
            assert "chunk_index" in c
            assert "token_count" in c

    def test_chunk_content_is_non_empty(self):
        text = "word " * 600
        chunks = chunk_text(text, "txt")
        for c in chunks:
            assert len(c["content"].strip()) > 0

    def test_empty_text_returns_empty_list(self):
        assert chunk_text("", "txt") == []

    def test_whitespace_only_returns_empty(self):
        assert chunk_text("   \n\n\t  ", "txt") == []

    def test_chunk_indices_start_at_zero(self):
        text = "\n\n".join([f"Para {i}. " + "word " * 60 for i in range(15)])
        chunks = chunk_text(text, "txt")
        assert chunks[0]["chunk_index"] == 0

    def test_chunk_indices_are_sequential(self):
        text = "\n\n".join([f"Para {i}. " + "word " * 60 for i in range(20)])
        chunks = chunk_text(text, "txt")
        for i, c in enumerate(chunks):
            assert c["chunk_index"] == i

    def test_very_short_content_filtered_out(self):
        # < 50 chars gets dropped
        chunks = chunk_text("Hi", "txt")
        assert len(chunks) == 0

    def test_token_count_is_positive(self):
        text = "word " * 300
        chunks = chunk_text(text, "txt")
        for c in chunks:
            assert c["token_count"] > 0

    def test_markdown_chunking(self):
        md = "# Section 1\n\nContent here. " * 5 + "\n\n## Section 2\n\nMore content. " * 5
        chunks = chunk_text(md, "markdown")
        assert len(chunks) > 0
        # All content should be non-empty
        assert all(len(c["content"]) > 0 for c in chunks)

    def test_csv_chunking_preserves_header(self):
        rows = "name,age,city\n" + "\n".join(f"Person{i},{i+20},City{i}" for i in range(100))
        chunks = chunk_text(rows, "csv")
        assert len(chunks) > 0
        # Header should appear in first chunk
        assert "name" in chunks[0]["content"]

    def test_large_text_produces_multiple_chunks(self):
        text = "word " * 5000
        chunks = chunk_text(text, "txt")
        assert len(chunks) > 1

    def test_clean_text_removes_triple_newlines(self):
        raw = "Hello\n\n\n\nWorld"
        cleaned = _clean_text(raw)
        assert "\n\n\n" not in cleaned

    def test_clean_text_normalizes_spaces(self):
        raw = "Hello    World\t\tFoo"
        cleaned = _clean_text(raw)
        assert "  " not in cleaned

    def test_clean_text_removes_null_bytes(self):
        raw = "Hello\x00World"
        cleaned = _clean_text(raw)
        assert "\x00" not in cleaned


# ─── Extractor ──────────────────────────────────────────

class TestExtractor:
    def test_extract_txt_basic(self):
        content = b"Hello World, this is a plain text document."
        text, meta = _extract_txt(content, "test.txt")
        assert "Hello World" in text
        assert "encoding" in meta

    def test_extract_txt_utf8_special_chars(self):
        content = "Héllo Wörld résumé café".encode("utf-8")
        text, _ = _extract_txt(content, "test.txt")
        assert "Héllo" in text

    def test_extract_txt_empty_file(self):
        text, meta = _extract_txt(b"", "empty.txt")
        assert isinstance(text, str)

    def test_extract_markdown_returns_text(self):
        content = b"# Title\n\nSome **bold** text.\n\n## Section\n\nMore content here."
        text, meta = _extract_markdown(content, "doc.md")
        assert "Title" in text
        assert "bold" in text
        assert "Section" in text
        assert "word_count" in meta

    def test_extract_markdown_word_count(self):
        content = b"word " * 100
        _, meta = _extract_markdown(content, "doc.md")
        assert meta["word_count"] >= 100

    def test_extract_csv_basic(self):
        content = b"name,age,city\nAlice,30,NYC\nBob,25,LA\nCarol,35,SF"
        text, meta = _extract_csv(content, "data.csv")
        assert "Alice" in text
        assert "Bob" in text
        assert "row_count" in meta

    def test_extract_csv_row_count(self):
        rows = "col1,col2\n" + "\n".join(f"val{i},val{i}" for i in range(50))
        _, meta = _extract_csv(rows.encode(), "data.csv")
        assert meta["row_count"] >= 50

    def test_extract_text_dispatcher_txt(self):
        text, _ = extract_text(b"Hello plain text", "txt", "test.txt")
        assert "Hello" in text

    def test_extract_text_dispatcher_markdown(self):
        text, _ = extract_text(b"# Header\n\nContent", "markdown", "doc.md")
        assert "Header" in text

    def test_extract_text_dispatcher_unknown_type(self):
        # Falls back to txt extractor
        text, _ = extract_text(b"Fallback content", "unknown_type", "file.xyz")
        assert "Fallback" in text


# ─── Citation Agent ─────────────────────────────────────

class TestCitationExtraction:
    def test_single_reference(self):
        refs = extract_source_refs("According to policy [Source 1], employees must...")
        assert 1 in refs

    def test_multiple_references(self):
        refs = extract_source_refs("See [Source 1] and [Source 3]. Also [Source 2].")
        assert set(refs) == {1, 2, 3}

    def test_no_references(self):
        refs = extract_source_refs("No citations here at all.")
        assert refs == []

    def test_deduplicates_repeated_ref(self):
        refs = extract_source_refs("[Source 1] first. [Source 1] second.")
        assert refs.count(1) == 1

    def test_high_source_numbers(self):
        refs = extract_source_refs("[Source 10] and [Source 25]")
        assert 10 in refs
        assert 25 in refs

    def test_case_insensitive_not_matched(self):
        # Our regex matches "Source" with capital S only
        refs = extract_source_refs("[source 1] lowercase")
        assert refs == []

    def test_empty_string(self):
        assert extract_source_refs("") == []

    def test_malformed_not_matched(self):
        refs = extract_source_refs("[Source] no number [Source abc]")
        assert refs == []
