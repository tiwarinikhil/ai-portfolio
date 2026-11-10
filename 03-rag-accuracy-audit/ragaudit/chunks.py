"""Chunk model, loading and a simple paragraph chunker for the demo."""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Chunk:
    id: str
    doc: str
    text: str
    updated: str = ""  # ISO date of the source document, if known


def load_chunks(path: str | Path) -> list[Chunk]:
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    return [Chunk(id=r["id"], doc=r.get("doc", ""), text=r["text"], updated=r.get("updated", "")) for r in rows]


def save_chunks(chunks: list[Chunk], path: str | Path) -> None:
    Path(path).write_text("".join(json.dumps(asdict(c)) + "\n" for c in chunks))


def _front_matter(text: str) -> tuple[dict, str]:
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        text = text[m.end():]
    return meta, text


def paragraph_chunks(text: str, doc: str) -> list[Chunk]:
    """Split on blank lines, the way many quick RAG pipelines do.

    Headings become their own tiny chunks. That is on purpose: it is a common
    real-world mistake, and the audit should catch it.
    """
    meta, body = _front_matter(text)
    parts = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    out = []
    for p in parts:
        lines = p.splitlines()
        if lines[0].startswith("#"):  # heading line becomes its own chunk
            out.append(lines[0].strip())
            lines = lines[1:]
        rest = "\n".join(lines).strip()
        if rest:
            out.append(rest)
    return [Chunk(id=f"{doc}#{i}", doc=doc, text=t, updated=meta.get("updated", "")) for i, t in enumerate(out)]


def chunk_folder(folder: str | Path) -> list[Chunk]:
    chunks = []
    for f in sorted(Path(folder).glob("*.md")):
        chunks += paragraph_chunks(f.read_text(), f.name)
    return chunks
