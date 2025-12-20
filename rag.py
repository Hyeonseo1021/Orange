# -*- coding: utf-8 -*-
"""
RAG (Retrieval-Augmented Generation) Module
- Embedding: intfloat/multilingual-e5-small (HuggingFace)
- Vector DB: ChromaDB
- PDF/OCR support
"""

import os
import io
from typing import List, Optional, BinaryIO
from pathlib import Path

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# PDF & OCR imports
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# Settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "documents")


class RAGSystem:
    """RAG System with ChromaDB and e5-small-v2 embeddings."""

    def __init__(
        self,
        embedding_model: str = EMBEDDING_MODEL,
        persist_directory: str = CHROMA_PERSIST_DIR,
        collection_name: str = CHROMA_COLLECTION_NAME,
    ):
        self.embedding_model = embedding_model
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": "cpu"},  # Use "cuda" for GPU
            encode_kwargs={"normalize_embeddings": True},
        )

        # Initialize or load ChromaDB
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
        )

        # Text splitter for document chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )

    def add_documents(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> List[str]:
        """Add documents to the vector store.

        Args:
            texts: List of text content to add
            metadatas: Optional list of metadata dicts for each text

        Returns:
            List of document IDs
        """
        documents = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            chunks = self.text_splitter.split_text(text)
            for chunk in chunks:
                documents.append(Document(page_content=chunk, metadata=metadata))

        if documents:
            ids = self.vectorstore.add_documents(documents)
            return ids
        return []

    def add_document(self, text: str, metadata: Optional[dict] = None) -> List[str]:
        """Add a single document to the vector store."""
        return self.add_documents([text], [metadata] if metadata else None)

    def extract_text_from_pdf(self, pdf_file: BinaryIO, use_ocr: bool = True) -> str:
        """Extract text from PDF file.

        Args:
            pdf_file: PDF file object (binary)
            use_ocr: Whether to use OCR for image-based pages

        Returns:
            Extracted text content
        """
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        all_text = []

        for page_num, page in enumerate(doc):
            # Try to extract text directly first
            text = page.get_text().strip()

            # If no text found and OCR is enabled, try OCR
            if not text and use_ocr:
                # Render page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))

                # OCR - try Korean+English first, fallback to English only
                try:
                    text = pytesseract.image_to_string(img, lang="kor+eng")
                except pytesseract.TesseractError:
                    text = pytesseract.image_to_string(img)

            if text:
                all_text.append(f"[페이지 {page_num + 1}]\n{text}")

        doc.close()
        return "\n\n".join(all_text)

    def extract_text_from_image(self, image_file: BinaryIO) -> str:
        """Extract text from image using OCR.

        Args:
            image_file: Image file object (binary)

        Returns:
            Extracted text content
        """
        img = Image.open(image_file)
        # Try Korean+English first, fallback to English only
        try:
            text = pytesseract.image_to_string(img, lang="kor+eng")
        except pytesseract.TesseractError:
            text = pytesseract.image_to_string(img)
        return text.strip()

    def add_pdf(self, pdf_file: BinaryIO, filename: str, use_ocr: bool = True) -> List[str]:
        """Add PDF document to the vector store.

        Args:
            pdf_file: PDF file object (binary)
            filename: Original filename for metadata
            use_ocr: Whether to use OCR for image-based pages

        Returns:
            List of document IDs
        """
        text = self.extract_text_from_pdf(pdf_file, use_ocr=use_ocr)
        if text:
            return self.add_document(text, metadata={"source": filename, "type": "pdf"})
        return []

    def add_image(self, image_file: BinaryIO, filename: str) -> List[str]:
        """Add image (via OCR) to the vector store.

        Args:
            image_file: Image file object (binary)
            filename: Original filename for metadata

        Returns:
            List of document IDs
        """
        text = self.extract_text_from_image(image_file)
        if text:
            return self.add_document(text, metadata={"source": filename, "type": "image"})
        return []

    def search(self, query: str, k: int = 3) -> List[Document]:
        """Search for similar documents.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of similar documents
        """
        # e5 models require "query: " prefix for queries
        formatted_query = f"query: {query}"
        results = self.vectorstore.similarity_search(formatted_query, k=k)
        return results

    def search_with_score(self, query: str, k: int = 3) -> List[tuple]:
        """Search with relevance scores.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of (Document, score) tuples
        """
        formatted_query = f"query: {query}"
        results = self.vectorstore.similarity_search_with_score(formatted_query, k=k)
        return results

    def get_retriever(self, k: int = 3):
        """Get a retriever for use in chains."""
        return self.vectorstore.as_retriever(search_kwargs={"k": k})

    def get_context(self, query: str, k: int = 3) -> str:
        """Get formatted context string for RAG.

        Args:
            query: User query
            k: Number of documents to retrieve

        Returns:
            Formatted context string
        """
        docs = self.search(query, k=k)
        if not docs:
            return ""

        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"[{i}] (출처: {source})\n{doc.page_content}")

        return "\n\n".join(context_parts)

    def clear(self):
        """Clear all documents from the collection."""
        self.vectorstore.delete_collection()
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

    def get_collection_stats(self) -> dict:
        """Get statistics about the collection."""
        collection = self.vectorstore._collection
        return {
            "name": self.collection_name,
            "count": collection.count(),
        }

    def get_sources(self) -> list:
        """Get unique source names from the collection."""
        collection = self.vectorstore._collection
        if collection.count() == 0:
            return []

        # Get all metadata
        result = collection.get(include=["metadatas"])
        metadatas = result.get("metadatas", [])

        # Extract unique sources
        sources = set()
        for meta in metadatas:
            if meta and "source" in meta:
                sources.add(meta["source"])

        return sorted(list(sources))


# Singleton instance
_rag_instance: Optional[RAGSystem] = None


def get_rag_system() -> RAGSystem:
    """Get or create the RAG system singleton."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGSystem()
    return _rag_instance


if __name__ == "__main__":
    # Test the RAG system
    rag = get_rag_system()

    # Add sample documents
    sample_texts = [
        "Python은 간결하고 읽기 쉬운 문법을 가진 프로그래밍 언어입니다.",
        "FastAPI는 Python으로 API를 빠르게 만들 수 있는 웹 프레임워크입니다.",
        "LangChain은 LLM 애플리케이션 개발을 위한 프레임워크입니다.",
    ]
    sample_metadatas = [
        {"source": "python_guide"},
        {"source": "fastapi_docs"},
        {"source": "langchain_docs"},
    ]

    print("Adding documents...")
    rag.add_documents(sample_texts, sample_metadatas)

    print(f"Collection stats: {rag.get_collection_stats()}")

    # Test search
    query = "웹 API를 만들려면 어떻게 해야 하나요?"
    print(f"\nQuery: {query}")
    results = rag.search(query, k=2)
    for i, doc in enumerate(results, 1):
        print(f"\n[{i}] {doc.page_content}")
        print(f"    Source: {doc.metadata.get('source', 'N/A')}")
