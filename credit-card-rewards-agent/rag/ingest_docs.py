"""
Layer 1: Data Ingestion
Reads card documents (.txt or .pdf) from data/raw_docs/, cleans + chunks the
text, attaches metadata (card_name, issuer, document_type, page_number,
effective_date), embeds each chunk with OpenAI embeddings, and stores the
result in a persistent Chroma collection (this project's stand-in for
PostgreSQL + pgvector -- same role, zero external infra to stand up for a
capstone demo running in VS Code).
"""

import os
import re
import glob
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_openai import OpenAIEmbeddings
import chromadb

from rag.chunk_documents import split_text

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_store")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
COLLECTION_NAME = "card_document_chunks"

RAW_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw_docs")


def _read_txt(path: str) -> list[tuple[str, int]]:
    """Returns list of (text, page_number). Plain text files are treated as a
    single 'page'."""
    with open(path, "r", encoding="utf-8") as f:
        return [(f.read(), 1)]


def _read_pdf(path: str) -> list[tuple[str, int]]:
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((text, i))
    return pages


def _extract_metadata(full_text: str, fallback_name: str) -> dict:
    """Pulls simple 'KEY: value' header fields out of the document text."""
    def find(field, default=""):
        m = re.search(rf"{field}\s*:\s*(.+)", full_text, re.IGNORECASE)
        return m.group(1).strip() if m else default

    return {
        "card_name": find("CARD NAME", fallback_name),
        "issuer": find("ISSUER", "Unknown"),
        "document_type": find("DOCUMENT TYPE", "Reward Program Terms"),
        "effective_date": find("EFFECTIVE DATE", "Unknown"),
    }


def get_chroma_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def ingest_all(raw_docs_dir: str = RAW_DOCS_DIR, reset: bool = False):
    """Ingests every .txt / .pdf file in raw_docs_dir into the Chroma collection."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    files = glob.glob(os.path.join(raw_docs_dir, "*.txt")) + \
        glob.glob(os.path.join(raw_docs_dir, "*.pdf"))

    total_chunks = 0
    for path in files:
        fname = os.path.basename(path)
        fallback_name = os.path.splitext(fname)[0].replace("_", " ").title()

        if path.endswith(".pdf"):
            pages = _read_pdf(path)
        else:
            pages = _read_txt(path)

        full_text = "\n".join(p[0] for p in pages)
        meta = _extract_metadata(full_text, fallback_name)

        ids, docs, metadatas = [], [], []
        chunk_idx = 0
        for page_text, page_number in pages:
            for chunk in split_text(page_text):
                if not chunk.strip():
                    continue
                chunk_idx += 1
                chunk_id = f"{fname}::{chunk_idx}"
                ids.append(chunk_id)
                docs.append(chunk)
                metadatas.append({
                    "card_name": meta["card_name"],
                    "issuer": meta["issuer"],
                    "document_type": meta["document_type"],
                    "effective_date": meta["effective_date"],
                    "page_number": page_number,
                    "source_file": fname,
                })

        if not docs:
            continue

        vectors = embeddings.embed_documents(docs)
        collection.upsert(ids=ids, documents=docs, metadatas=metadatas, embeddings=vectors)
        total_chunks += len(docs)
        print(f"Ingested {len(docs)} chunks from {fname} (card: {meta['card_name']})")

    print(f"Done. Total chunks in collection: {total_chunks}")


if __name__ == "__main__":
    ingest_all(reset=True)
