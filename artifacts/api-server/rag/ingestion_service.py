import os
import hashlib
import logging
from typing import List, Optional
from pypdf import PdfReader

from rag.embedding_service import OpenAIEmbeddingService
from rag.chroma_service import ChromaService

logger = logging.getLogger(__name__)


class RecursiveCharacterTextSplitter:
    """A clean, pure-Python implementation of RecursiveCharacterTextSplitter."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        return self._split(text, self.separators)

    def _split(self, text: str, separators: List[str]) -> List[str]:
        """Recursive splitting implementation."""
        if not separators:
            # Base case: split by characters
            return [
                text[i : i + self.chunk_size]
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap)
            ]

        separator = separators[0]
        next_separators = separators[1:]

        # If separator is empty string, split into characters directly
        if separator == "":
            return [
                text[i : i + self.chunk_size]
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap)
            ]

        splits = text.split(separator)

        chunks = []
        current_chunk: List[str] = []
        current_len = 0

        for split in splits:
            split_len = len(split)
            if split_len > self.chunk_size:
                # If a single split is larger than chunk_size, process the current buffer
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_len = 0

                # Recursively split the oversized split
                sub_splits = self._split(split, next_separators)
                chunks.extend(sub_splits)
            else:
                # Accumulate split into current chunk
                if (
                    current_len + split_len + (len(separator) if current_chunk else 0)
                    <= self.chunk_size
                ):
                    current_chunk.append(split)
                    current_len += split_len + (
                        len(separator) if len(current_chunk) > 1 else 0
                    )
                else:
                    if current_chunk:
                        chunks.append(separator.join(current_chunk))
                    # Retain some elements for overlap
                    overlap_size = 0
                    overlap_chunk: List[str] = []
                    for item in reversed(current_chunk):
                        if overlap_size + len(item) <= self.chunk_overlap:
                            overlap_chunk.insert(0, item)
                            overlap_size += len(item) + len(separator)
                        else:
                            break
                    current_chunk = overlap_chunk + [split]
                    current_len = sum(len(x) for x in current_chunk) + len(
                        separator
                    ) * (len(current_chunk) - 1)

        if current_chunk:
            chunks.append(separator.join(current_chunk))

        return chunks


class IngestionService:
    def __init__(
        self, chroma_service: ChromaService, embedding_service: OpenAIEmbeddingService
    ):
        self.chroma = chroma_service
        self.embedding = embedding_service
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract all pages text from a PDF file using pypdf."""
        try:
            reader = PdfReader(file_path)
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise

    def ingest_file(self, file_path: str) -> int:
        """Ingest a file (PDF or TXT) into ChromaDB."""
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return 0

        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        try:
            if ext == ".pdf":
                text = self.extract_text_from_pdf(file_path)
            elif ext in [".txt", ".md"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            else:
                logger.warning(f"Unsupported file format: {ext}")
                return 0

            if not text.strip():
                logger.warning(f"No text extracted from file: {filename}")
                return 0

            chunks = self.splitter.split_text(text)
            if not chunks:
                return 0

            logger.info(f"Split {filename} into {len(chunks)} chunks.")

            ids = []
            embeddings = []
            metadatas = []
            documents = []

            # Generate embeddings in batch
            embeddings_list = self.embedding.get_embeddings(chunks)

            for i, chunk in enumerate(chunks):
                chunk_id = f"{filename}_chunk_{i}"
                ids.append(chunk_id)
                embeddings.append(embeddings_list[i])
                documents.append(chunk)
                metadatas.append(
                    {
                        "source": filename,
                        "chunk_index": i,
                        "hash": hashlib.md5(chunk.encode("utf-8")).hexdigest(),
                    }
                )

            self.chroma.add_documents(ids, documents, embeddings, metadatas)
            return len(chunks)

        except Exception as e:
            logger.error(f"Failed to ingest file {file_path}: {e}")
            raise
