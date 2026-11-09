"""Two ways to split documents into chunks.

fixed_chunks:   cut text every N characters (the common default).
heading_chunks: split by markdown headings and keep the heading path
                at the top of each chunk, so every chunk knows what it is about.
"""

import re
from dataclasses import dataclass, field

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    heading: str = ""
    meta: dict = field(default_factory=dict)


def fixed_chunks(text: str, source: str, size: int = 500, overlap: int = 50) -> list[Chunk]:
    if size <= overlap:
        raise ValueError("size must be larger than overlap")
    chunks = []
    start = 0
    i = 0
    while start < len(text):
        piece = text[start:start + size].strip()
        if piece:
            chunks.append(Chunk(id=f"{source}#fixed-{i}", text=piece, source=source))
            i += 1
        start += size - overlap
    return chunks


def _split_long(body: str, max_chars: int) -> list[str]:
    """Split a long section by paragraphs, keeping each part under max_chars when possible."""
    parts, current = [], ""
    for para in [p.strip() for p in body.split("\n\n") if p.strip()]:
        if current and len(current) + len(para) + 2 > max_chars:
            parts.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        parts.append(current)
    return parts


def heading_chunks(text: str, source: str, max_chars: int = 1200) -> list[Chunk]:
    stack: list[tuple[int, str]] = []
    sections: list[tuple[str, list[str]]] = []
    body: list[str] = []

    def flush():
        content = "\n".join(body).strip()
        if content:
            path = " > ".join(title for _, title in stack)
            sections.append((path, [content]))

    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            flush()
            body = []
            level, title = len(m.group(1)), m.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
        else:
            body.append(line)
    flush()

    chunks = []
    for path, (content,) in sections:
        for j, part in enumerate(_split_long(content, max_chars)):
            chunks.append(Chunk(
                id=f"{source}#{len(chunks)}",
                text=f"{path}\n\n{part}" if path else part,
                source=source,
                heading=path,
                meta={"part": j},
            ))
    return chunks
