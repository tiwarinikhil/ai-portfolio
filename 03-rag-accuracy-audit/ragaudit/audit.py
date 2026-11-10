"""Score a retriever on a question set and flag the chunks that hurt it."""

import re
from collections import Counter, defaultdict

from .chunks import Chunk
from .retrievers import tokenize

TINY_CHARS = 40          # shorter than this is almost always a heading or a stray line
DUP_SIMILARITY = 0.8     # word overlap (Jaccard) that counts as a near-duplicate
BOILERPLATE_DOCS = 3     # the same text in this many documents is boilerplate
STALE_HEADING_SHARE = 0.5


def is_tiny(chunk: Chunk) -> bool:
    """Very short, or only heading lines: no real content to retrieve."""
    lines = [l for l in chunk.text.splitlines() if l.strip()]
    return len(chunk.text) < TINY_CHARS or all(l.lstrip().startswith("#") for l in lines)


def is_hit(chunk: Chunk, answer: str) -> bool:
    return answer.lower() in chunk.text.lower()


def jaccard(a: str, b: str) -> float:
    """Word overlap, ignoring numbers, so '14 days' vs '30 days' still counts as the same sentence."""
    sa = {t for t in tokenize(a) if not t.isdigit()}
    sb = {t for t in tokenize(b) if not t.isdigit()}
    return len(sa & sb) / len(sa | sb) if sa | sb else 0.0


def _headings(chunks: list[Chunk]) -> set[str]:
    return {c.text.lstrip("#").strip().lower() for c in chunks if c.text.startswith("#")}


def find_stale_docs(chunks: list[Chunk]) -> dict[str, str]:
    """Docs that look like an older copy of another doc (same headings, older date).

    Returns {old_doc: newer_doc}.
    """
    by_doc = defaultdict(list)
    for c in chunks:
        by_doc[c.doc].append(c)
    stale = {}
    docs = list(by_doc)
    for a in docs:
        for b in docs:
            if a == b:
                continue
            ha, hb = _headings(by_doc[a]), _headings(by_doc[b])
            if not ha:
                continue
            share = len(ha & hb) / len(ha)
            ua, ub = by_doc[a][0].updated, by_doc[b][0].updated
            if share >= STALE_HEADING_SHARE and ua and ub and ua < ub:
                stale[a] = b
    return stale


def find_bad_chunks(chunks: list[Chunk]) -> dict[str, list[str]]:
    """Return {chunk_id: [issue, ...]} using only the chunks (no questions needed)."""
    issues = defaultdict(list)
    for c in chunks:
        if is_tiny(c):
            issues[c.id].append("tiny")

    # near-duplicate groups
    groups = []
    seen = set()
    for i, a in enumerate(chunks):
        if a.id in seen or is_tiny(a):
            continue
        group = [a]
        for b in chunks[i + 1:]:
            if b.id not in seen and not is_tiny(b) and jaccard(a.text, b.text) >= DUP_SIMILARITY:
                group.append(b)
                seen.add(b.id)
        if len(group) > 1:
            seen.add(a.id)
            groups.append(group)
    for g in groups:
        docs = {c.doc for c in g}
        nums = {tuple(re.findall(r"\d+", c.text)) for c in g}
        label = "boilerplate" if len(docs) >= BOILERPLATE_DOCS else "duplicate"
        if len(nums) > 1:
            label = "conflict"  # nearly the same text, different numbers
        for c in g:
            issues[c.id].append(label)

    for old, new in find_stale_docs(chunks).items():
        for c in chunks:
            if c.doc == old:
                issues[c.id].append(f"stale (newer: {new})")
    return dict(issues)


def audit(chunks: list[Chunk], retriever, questions: list[dict], k: int = 5) -> dict:
    by_id = {c.id: c for c in chunks}
    bad = find_bad_chunks(chunks)
    rows = []
    wrong_top1 = Counter()
    in_topk = Counter()
    for q in questions:
        ids = retriever.search(q["question"], k)
        rank = next((r + 1 for r, cid in enumerate(ids) if is_hit(by_id[cid], q["answer"])), None)
        for cid in ids:
            in_topk[cid] += 1
        top = ids[0] if ids else None
        if top and rank != 1:
            wrong_top1[top] += 1
        rows.append({"question": q["question"], "answer": q["answer"], "rank": rank, "top": top,
                     "top_issues": bad.get(top, []) if top else []})

    n = len(rows)
    metrics = {
        "questions": n,
        "chunks": len(chunks),
        "hit@1": sum(r["rank"] == 1 for r in rows) / n,
        "hit@3": sum(r["rank"] is not None and r["rank"] <= 3 for r in rows) / n,
        f"hit@{k}": sum(r["rank"] is not None for r in rows) / n,
        "mrr": sum(1 / r["rank"] for r in rows if r["rank"]) / n,
    }
    # chunks that push the right answer down: they win top-1 for questions they cannot answer
    crowders = [
        {"id": cid, "wrong_top1": cnt, "issues": bad.get(cid, []), "text": by_id[cid].text[:80]}
        for cid, cnt in wrong_top1.most_common()
    ]
    flagged = sum(1 for c in chunks if c.id in bad)
    return {"metrics": metrics, "rows": rows, "crowders": crowders, "bad": bad,
            "flagged_chunks": flagged, "never_retrieved": [c.id for c in chunks if c.id not in in_topk]}
