"""Safe, automatic fixes for the issues the audit finds.

1. Drop documents that are an older copy of a newer document.
2. Keep one copy of each duplicate or boilerplate group.
3. Merge tiny chunks (usually headings) into the chunk that follows them.

Conflicts (same text, different numbers) inside current documents are only
reported. A person has to decide which number is right.
"""

from .audit import DUP_SIMILARITY, find_bad_chunks, find_stale_docs, is_tiny, jaccard
from .chunks import Chunk


ALL_STEPS = ("stale", "dedupe", "merge")


def fix_chunks(chunks: list[Chunk], steps=ALL_STEPS) -> tuple[list[Chunk], list[str]]:
    log = []
    stale = find_stale_docs(chunks) if "stale" in steps else {}
    for old, new in stale.items():
        log.append(f"dropped stale document {old} (newer copy: {new})")
    chunks = [c for c in chunks if c.doc not in stale]

    bad = find_bad_chunks(chunks)
    kept: list[Chunk] = []
    for c in chunks:
        dup_label = {"duplicate", "boilerplate"} & set(bad.get(c.id, []))
        if "dedupe" in steps and dup_label and any(jaccard(c.text, k.text) >= DUP_SIMILARITY for k in kept):
            log.append(f"dropped {sorted(dup_label)[0]} copy {c.id}")
            continue
        kept.append(c)

    if "merge" not in steps:
        return kept, log

    merged: list[Chunk] = []
    carry = None
    for c in kept:
        if carry and carry.doc == c.doc:
            c = Chunk(id=c.id, doc=c.doc, text=carry.text + "\n" + c.text, updated=c.updated)
            log.append(f"merged tiny chunk {carry.id} into {c.id}")
            carry = None
        elif carry:
            merged.append(carry)
            carry = None
        if is_tiny(c):
            carry = c
            continue
        merged.append(c)
    if carry:
        merged.append(carry)
    return merged, log
