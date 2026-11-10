"""RAG accuracy audit: measure a retriever on a question set and find the chunks that hurt it."""

from .chunks import Chunk, load_chunks, paragraph_chunks, save_chunks
from .retrievers import BM25Retriever, load_retriever
from .audit import audit, find_bad_chunks
from .fix import fix_chunks

__all__ = [
    "Chunk",
    "load_chunks",
    "save_chunks",
    "paragraph_chunks",
    "BM25Retriever",
    "load_retriever",
    "audit",
    "find_bad_chunks",
    "fix_chunks",
]
