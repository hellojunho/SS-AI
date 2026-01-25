from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import faiss
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

SUPPORTED_EXTENSIONS = {".txt", ".csv", ".pdf", ".md"}
WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class DocumentChunk:
    text: str
    source: str


@dataclass
class IndexArtifacts:
    index: faiss.Index
    chunks: list[DocumentChunk]
    model_name: str


def _clean_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_csv(path: Path) -> str:
    df = pd.read_csv(path)
    lines = []
    for _, row in df.iterrows():
        parts = [f"{col}: {row[col]}" for col in df.columns]
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def _read_pdf(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return pages


def _read_web(url: str) -> str:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for script in soup(["script", "style", "noscript"]):
        script.decompose()
    text = soup.get_text(separator=" ")
    return text


def load_documents(paths: Iterable[Path], urls: Iterable[str]) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for path in paths:
        if path.is_dir():
            for file_path in path.rglob("*"):
                if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    chunks.extend(load_documents([file_path], []))
            continue
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue
        if suffix == ".txt":
            text = _read_txt(path)
            chunks.append(DocumentChunk(text=text, source=str(path)))
        elif suffix == ".md":
            text = _read_md(path)
            chunks.append(DocumentChunk(text=text, source=str(path)))
        elif suffix == ".csv":
            text = _read_csv(path)
            chunks.append(DocumentChunk(text=text, source=str(path)))
        elif suffix == ".pdf":
            pages = _read_pdf(path)
            for page_index, page_text in enumerate(pages, start=1):
                source = f"{path}#page={page_index}"
                chunks.append(DocumentChunk(text=page_text, source=source))

    for url in urls:
        text = _read_web(url)
        chunks.append(DocumentChunk(text=text, source=url))

    cleaned: list[DocumentChunk] = []
    for chunk in chunks:
        cleaned_text = _clean_text(chunk.text)
        if cleaned_text:
            cleaned.append(DocumentChunk(text=cleaned_text, source=chunk.source))
    return cleaned


def chunk_text(text: str, max_chars: int = 1000, overlap: int = 200) -> list[str]:
    if max_chars <= 0:
        return [text]
    if overlap >= max_chars:
        overlap = max_chars // 4
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == length:
            break
        start = end - overlap
    return chunks


def _is_e5_model(model_name: str) -> bool:
    return "e5" in model_name.lower()


def embed_texts(model: SentenceTransformer, texts: list[str], *, is_query: bool) -> np.ndarray:
    if _is_e5_model(model.name_or_path):
        prefix = "query: " if is_query else "passage: "
        texts = [prefix + text for text in texts]
    embeddings = model.encode(texts, normalize_embeddings=True)
    return np.asarray(embeddings, dtype="float32")


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return index


def build_index(
    documents: list[DocumentChunk],
    *,
    model_name: str = "intfloat/multilingual-e5-small",
    max_chars: int = 1000,
    overlap: int = 200,
) -> IndexArtifacts:
    model = SentenceTransformer(model_name)
    chunked_docs: list[DocumentChunk] = []
    for doc in documents:
        for chunk in chunk_text(doc.text, max_chars=max_chars, overlap=overlap):
            chunked_docs.append(DocumentChunk(text=chunk, source=doc.source))
    texts = [doc.text for doc in chunked_docs]
    embeddings = embed_texts(model, texts, is_query=False)
    index = build_faiss_index(embeddings)
    return IndexArtifacts(index=index, chunks=chunked_docs, model_name=model_name)


def save_index(artifacts: IndexArtifacts, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "index.faiss"
    faiss.write_index(artifacts.index, str(index_path))
    metadata = {
        "model_name": artifacts.model_name,
        "chunks": [
            {"text": chunk.text, "source": chunk.source}
            for chunk in artifacts.chunks
        ],
    }
    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def load_index(index_dir: Path) -> IndexArtifacts:
    index_path = index_dir / "index.faiss"
    metadata_path = index_dir / "metadata.json"
    index = faiss.read_index(str(index_path))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    chunks = [DocumentChunk(**chunk) for chunk in metadata["chunks"]]
    return IndexArtifacts(index=index, chunks=chunks, model_name=metadata["model_name"])


def search(
    artifacts: IndexArtifacts,
    query: str,
    *,
    top_k: int = 4,
) -> list[DocumentChunk]:
    model = SentenceTransformer(artifacts.model_name)
    query_embedding = embed_texts(model, [query], is_query=True)
    scores, indices = artifacts.index.search(query_embedding, top_k)
    results = []
    for idx in indices[0]:
        if idx < 0 or idx >= len(artifacts.chunks):
            continue
        results.append(artifacts.chunks[idx])
    return results
