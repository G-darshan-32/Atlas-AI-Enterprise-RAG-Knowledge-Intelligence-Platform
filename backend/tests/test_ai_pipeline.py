"""Unit tests for the AI pipeline (no external services needed)."""
import pytest
from app.ai.pipeline.chunker import chunk_text, _clean_text
from app.ai.pipeline.extractor import _extract_txt, _extract_markdown, _extract_csv
from app.ai.agents.citation_agent import extract_source_refs


class TestChunker:
    def test_basic_chunking(self):
        text = " ".join(["word"] * 1000)
        chunks = chunk_text(text, "txt")
        assert len(chunks) > 0
        assert all("content" in c for c in chunks)
        assert all(c["token_count"] > 0 for c in chunks)

    def test_empty_text_returns_empty(self):
        chunks = chunk_text("", "txt")
        assert chunks == []

    def test_whitespace_only_returns_empty(self):
        chunks = chunk_text("   \n\n   ", "txt")
        assert chunks == []

    def test_chunk_indices_sequential(self):
        text = "\n\n".join([f"Paragraph {i}. " + "word " * 50 for i in range(20)])
        chunks = chunk_text(text, "txt")
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_markdown_chunking_respects_headers(self):
        text = "# Section 1\n\nContent one.\n\n## Section 2\n\nContent two.\n\n### Section 3\n\nContent three."
        chunks = chunk_text(text, "markdown")
        assert len(chunks) >= 1

    def test_short_chunks_are_filtered(self):
        # Very short content should be filtered out
        text = "Hi"
        chunks = chunk_text(text, "txt")
        assert len(chunks) == 0

    def test_clean_text_removes_extra_newlines(self):
        raw = "Hello\n\n\n\nWorld"
        cleaned = _clean_text(raw)
        assert "\n\n\n" not in cleaned

    def test_clean_text_normalizes_spaces(self):
        raw = "Hello    World\t\tFoo"
        cleaned = _clean_text(raw)
        assert "  " not in cleaned


class TestExtractor:
    def test_extract_txt(self):
        content = b"Hello World, this is a test document."
        text, meta = _extract_txt(content, "test.txt")
        assert "Hello World" in text
        assert "encoding" in meta

    def test_extract_txt_utf8(self):
        content = "Héllo Wörld".encode("utf-8")
        text, meta = _extract_txt(content, "test.txt")
        assert "Héllo" in text

    def test_extract_markdown(self):
        content = b"# Title\n\nSome **bold** text.\n\n## Section\n\nMore content."
        text, meta = _extract_markdown(content, "doc.md")
        assert "Title" in text
        assert "bold" in text

    def test_extract_csv(self):
        content = b"name,age,city\nAlice,30,NYC\nBob,25,LA"
        text, meta = _extract_csv(content, "data.csv")
        assert "Alice" in text
        assert "Bob" in text
        assert "row_count" in meta


class TestCitationAgent:
    def test_extract_source_refs_single(self):
        text = "According to the policy [Source 1], employees must..."
        refs = extract_source_refs(text)
        assert refs == [1]

    def test_extract_source_refs_multiple(self):
        text = "See [Source 1] and [Source 3] for more details. Also [Source 2]."
        refs = extract_source_refs(text)
        assert set(refs) == {1, 2, 3}

    def test_extract_source_refs_none(self):
        text = "No citations in this text."
        refs = extract_source_refs(text)
        assert refs == []

    def test_extract_source_refs_deduplicates(self):
        text = "[Source 1] first mention. [Source 1] second mention."
        refs = extract_source_refs(text)
        assert refs.count(1) == 1
