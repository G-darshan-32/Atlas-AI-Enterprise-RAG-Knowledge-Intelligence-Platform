"""Unit tests for chunking, extraction, and citation logic."""
import pytest
from app.ai.pipeline.chunker import chunk_text, _clean_text
from app.ai.pipeline.extractor import _extract_txt, _extract_markdown, _extract_csv, extract_text
from app.ai.agents.citation_agent import extract_source_refs


class TestCleaner:
    def test_removes_triple_newlines(self):
        assert "\n\n\n" not in _clean_text("a\n\n\n\nb")

    def test_normalises_spaces(self):
        assert "  " not in _clean_text("a    b")

    def test_removes_null_bytes(self):
        assert "\x00" not in _clean_text("a\x00b")

    def test_strips_leading_trailing(self):
        assert _clean_text("  hello  ") == "hello"


class TestChunker:
    """200+ word text so chunker has something to work with."""

    LONG_TEXT = " ".join(f"word{i}" for i in range(600))
    PARA_TEXT = "\n\n".join(f"Paragraph {i}. " + "sentence " * 40 for i in range(20))
    MD_TEXT = "\n\n".join(f"# Section {i}\n\n" + "content " * 60 for i in range(8))

    def test_returns_list(self):
        assert isinstance(chunk_text(self.LONG_TEXT, "txt"), list)

    def test_empty_returns_empty(self):
        assert chunk_text("", "txt") == []

    def test_whitespace_only_empty(self):
        assert chunk_text("   \n\t  ", "txt") == []

    def test_too_short_filtered(self):
        assert chunk_text("Hi", "txt") == []

    def test_has_content_key(self):
        for c in chunk_text(self.LONG_TEXT, "txt"):
            assert "content" in c and len(c["content"]) > 0

    def test_has_chunk_index(self):
        for c in chunk_text(self.LONG_TEXT, "txt"):
            assert "chunk_index" in c

    def test_has_token_count(self):
        for c in chunk_text(self.LONG_TEXT, "txt"):
            assert c["token_count"] > 0

    def test_indices_start_at_zero(self):
        chunks = chunk_text(self.PARA_TEXT, "txt")
        assert chunks[0]["chunk_index"] == 0

    def test_indices_are_sequential(self):
        chunks = chunk_text(self.PARA_TEXT, "txt")
        for i, c in enumerate(chunks):
            assert c["chunk_index"] == i

    def test_large_text_multiple_chunks(self):
        # Use distinct paragraphs so the chunker has boundaries to split on
        text = "\n\n".join(f"Paragraph {i}: " + "sentence content " * 40 for i in range(30))
        assert len(chunk_text(text, "txt")) > 1

    def test_markdown_mode(self):
        chunks = chunk_text(self.MD_TEXT, "markdown")
        assert len(chunks) > 0
        assert all(len(c["content"]) > 0 for c in chunks)

    def test_csv_mode_preserves_header(self):
        csv = "name,score\n" + "\n".join(f"user{i},{i}" for i in range(100))
        chunks = chunk_text(csv, "csv")
        assert len(chunks) > 0
        assert "name" in chunks[0]["content"]

    def test_pptx_mode_falls_through_to_paragraph(self):
        # pptx falls back to paragraph chunker
        chunks = chunk_text(self.PARA_TEXT, "pptx")
        assert len(chunks) > 0


class TestExtractor:
    def test_txt_basic(self):
        text, meta = _extract_txt(b"Hello world document.", "f.txt")
        assert "Hello" in text
        assert "encoding" in meta

    def test_txt_utf8(self):
        text, _ = _extract_txt("café résumé naïve".encode("utf-8"), "f.txt")
        assert "café" in text

    def test_txt_empty(self):
        text, _ = _extract_txt(b"", "f.txt")
        assert text == ""

    def test_markdown_basic(self):
        text, meta = _extract_markdown(b"# Title\n\nParagraph.", "f.md")
        assert "Title" in text
        assert meta["word_count"] >= 2

    def test_markdown_word_count(self):
        _, meta = _extract_markdown(("word " * 100).encode(), "f.md")
        assert meta["word_count"] >= 100

    def test_csv_rows(self):
        csv = b"a,b\n1,2\n3,4\n5,6"
        text, meta = _extract_csv(csv, "f.csv")
        assert "1" in text
        assert meta["row_count"] >= 3

    def test_dispatcher_txt(self):
        text, _ = extract_text(b"plain content", "txt", "f.txt")
        assert "plain" in text

    def test_dispatcher_markdown(self):
        text, _ = extract_text(b"# Head\n\nbody", "markdown", "f.md")
        assert "Head" in text

    def test_dispatcher_unknown_falls_back(self):
        text, _ = extract_text(b"fallback content", "unknown", "f.xyz")
        assert "fallback" in text


class TestCitationExtractor:
    def test_single(self):
        assert 1 in extract_source_refs("See [Source 1] for details.")

    def test_multiple(self):
        refs = extract_source_refs("[Source 1] and [Source 3] and [Source 2]")
        assert set(refs) == {1, 2, 3}

    def test_empty(self):
        assert extract_source_refs("No citations.") == []

    def test_dedup(self):
        refs = extract_source_refs("[Source 1] again [Source 1]")
        assert refs.count(1) == 1

    def test_large_numbers(self):
        refs = extract_source_refs("[Source 99]")
        assert 99 in refs

    def test_lowercase_not_matched(self):
        assert extract_source_refs("[source 1]") == []

    def test_no_number_not_matched(self):
        assert extract_source_refs("[Source] no number") == []

    def test_empty_string(self):
        assert extract_source_refs("") == []
