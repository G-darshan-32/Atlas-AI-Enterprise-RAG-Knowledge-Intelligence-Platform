"""Smart semantic chunking with configurable strategy."""
import re
from typing import List


CHUNK_SIZE = 512        # target tokens per chunk
CHUNK_OVERLAP = 64      # token overlap between chunks
CHARS_PER_TOKEN = 4     # rough approximation


def chunk_text(text: str, file_type: str = "txt", chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[dict]:
    """
    Split text into overlapping chunks with semantic boundary awareness.
    Returns list of dicts: {content, chunk_index, token_count, page_hint}
    """
    # Clean the text first
    text = _clean_text(text)

    if not text.strip():
        return []

    # Use different strategies based on file type
    if file_type in ("markdown", "ipynb"):
        raw_chunks = _chunk_by_markdown_headers(text, chunk_size, overlap)
    elif file_type == "pdf":
        raw_chunks = _chunk_by_paragraphs(text, chunk_size, overlap)
    elif file_type in ("csv", "xlsx"):
        raw_chunks = _chunk_rows(text, chunk_size)
    else:
        raw_chunks = _chunk_by_paragraphs(text, chunk_size, overlap)

    # Tag with index and token count
    result = []
    for i, chunk in enumerate(raw_chunks):
        content = chunk.get("content", "").strip()
        if len(content) < 50:  # skip tiny chunks
            continue
        result.append({
            "content": content,
            "chunk_index": i,
            "token_count": len(content) // CHARS_PER_TOKEN,
            "page_hint": chunk.get("page_hint"),
        })

    return result


def _clean_text(text: str) -> str:
    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    # Remove null bytes
    text = text.replace("\x00", "")
    return text.strip()


def _chunk_by_paragraphs(text: str, chunk_size: int, overlap: int) -> List[dict]:
    """Split on paragraph boundaries, merge small paragraphs, split large ones."""
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks = []
    current = []
    current_tokens = 0
    target_chars = chunk_size * CHARS_PER_TOKEN
    overlap_chars = overlap * CHARS_PER_TOKEN

    for para in paragraphs:
        para_tokens = len(para) // CHARS_PER_TOKEN

        # If single paragraph exceeds chunk size, split by sentences
        if para_tokens > chunk_size:
            if current:
                chunks.append({"content": "\n\n".join(current)})
                current = []
                current_tokens = 0
            sentence_chunks = _split_by_sentences(para, chunk_size, overlap)
            chunks.extend(sentence_chunks)
            continue

        # If adding this para exceeds limit, flush current
        if current_tokens + para_tokens > chunk_size and current:
            chunk_content = "\n\n".join(current)
            chunks.append({"content": chunk_content})

            # Overlap: keep last portion
            overlap_text = chunk_content[-overlap_chars:]
            current = [overlap_text] if overlap_text.strip() else []
            current_tokens = len(overlap_text) // CHARS_PER_TOKEN

        current.append(para)
        current_tokens += para_tokens

    if current:
        chunks.append({"content": "\n\n".join(current)})

    return chunks


def _split_by_sentences(text: str, chunk_size: int, overlap: int) -> List[dict]:
    """Split large block by sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = []
    current_len = 0
    target = chunk_size * CHARS_PER_TOKEN

    for sent in sentences:
        if current_len + len(sent) > target and current:
            chunks.append({"content": " ".join(current)})
            # overlap
            overlap_sents = current[-2:] if len(current) >= 2 else current
            current = overlap_sents[:]
            current_len = sum(len(s) for s in current)
        current.append(sent)
        current_len += len(sent)

    if current:
        chunks.append({"content": " ".join(current)})

    return chunks


def _chunk_by_markdown_headers(text: str, chunk_size: int, overlap: int) -> List[dict]:
    """Split markdown on header boundaries."""
    sections = re.split(r"\n(?=#{1,4} )", text)
    chunks = []
    target_chars = chunk_size * CHARS_PER_TOKEN

    for section in sections:
        if len(section) <= target_chars:
            if section.strip():
                chunks.append({"content": section.strip()})
        else:
            # Large section: further split by paragraphs
            sub_chunks = _chunk_by_paragraphs(section, chunk_size, overlap)
            chunks.extend(sub_chunks)

    return chunks


def _chunk_rows(text: str, chunk_size: int) -> List[dict]:
    """For tabular data, group rows into chunks."""
    lines = text.split("\n")
    chunks = []
    target_chars = chunk_size * CHARS_PER_TOKEN
    current_lines = []
    current_len = 0

    header = lines[0] if lines else ""

    for line in lines[1:]:  # skip header for chunking but include in each chunk
        if current_len + len(line) > target_chars and current_lines:
            content = header + "\n" + "\n".join(current_lines)
            chunks.append({"content": content})
            current_lines = []
            current_len = 0
        current_lines.append(line)
        current_len += len(line)

    if current_lines:
        chunks.append({"content": header + "\n" + "\n".join(current_lines)})

    return chunks
