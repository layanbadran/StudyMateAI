"""Step 2: split page text into overlapping chunks.

Why chunks? An embedding represents the meaning of a piece of text. Whole pages mix many
topics, so small focused pieces give more precise search results.
Why overlap? A sentence cut at a chunk border would lose its context; overlap keeps it
in both neighbouring chunks.
We chunk each page separately so every chunk has exactly one page number for citations.
"""
from dataclasses import dataclass

SENTENCE_ENDINGS = (". ", "? ", "! ", "؟ ", "。")


@dataclass
class Chunk:
    text: str
    page: int
    index: int  # position of the chunk inside the whole document


def split_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = " ".join(text.split())  # collapse newlines and repeated spaces
    if not text:
        return []

    pieces: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)

        if end < length:
            # Prefer to stop at the end of a sentence in the last 40% of the window,
            # otherwise at the last space, so words are not cut in half.
            window_start = start + int(chunk_size * 0.6)
            cut = max(text.rfind(mark, window_start, end) for mark in SENTENCE_ENDINGS)
            if cut != -1:
                end = cut + 1
            else:
                space = text.rfind(" ", window_start, end)
                if space != -1:
                    end = space

        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)

        if end >= length:
            break

        # Step back by `overlap`, always moving forward overall, and begin at a word start.
        start = max(end - overlap, start + 1)
        if start > 0 and text[start - 1] != " ":
            space = text.find(" ", start, end)
            if space != -1:
                start = space + 1

    return pieces


def chunk_pages(pages, chunk_size: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page in pages:
        for piece in split_text(page.text, chunk_size, overlap):
            chunks.append(Chunk(text=piece, page=page.page, index=len(chunks)))
    return chunks
