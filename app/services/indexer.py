import os
import time
from typing import List, Dict
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import structlog

logger = structlog.get_logger()


class DocumentIndexer:
    """Serviço responsável pela ingestão e indexação de documentos"""
    
    def __init__(
        self,
        data_path: str,
        chroma_db_path: str,
        embedding_model_name: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        self.data_path = Path(data_path)
        self.chroma_db_path = chroma_db_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Inicializar modelo de embeddings
        logger.info("Loading embedding model", model=embedding_model_name)
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # Inicializar ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Collection name
        self.collection_name = "documents"
        
    def _extract_text_from_pdf(self, pdf_path: Path) -> List[Dict[str, str]]:
        """Extrai texto de um PDF página por página"""
        logger.info("Extracting text from PDF", file=pdf_path.name)
        
        reader = PdfReader(str(pdf_path))
        pages = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text.strip():
                pages.append({
                    "text": text,
                    "page": page_num,
                    "source": pdf_path.name
                })
        
        logger.info("PDF extraction complete", file=pdf_path.name, pages=len(pages))
        return pages
    
    def _chunk_documents(self, pages: List[Dict[str, str]]) -> List[Dict[str, any]]:
        """Divide documentos em chunks com overlap"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = []
        for page_data in pages:
            page_chunks = text_splitter.split_text(page_data["text"])
            
            for i, chunk_text in enumerate(page_chunks):
                chunks.append({
                    "text": chunk_text,
                    "source": page_data["source"],
                    "page": page_data["page"],
                    "chunk_id": f"{page_data['source']}_p{page_data['page']}_c{i}"
                })
        
        return chunks
    
    def _create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para os textos"""
        logger.info("Generating embeddings", count=len(texts))
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()
    
    def index_documents(self) -> int:
        """Indexa todos os documentos PDF da pasta data"""
        start_time = time.time()
        
        # Listar PDFs
        pdf_files = list(self.data_path.glob("*.pdf"))
        if not pdf_files:
            logger.warning("No PDF files found", path=str(self.data_path))
            return 0
        
        logger.info("Found PDF files", count=len(pdf_files), files=[f.name for f in pdf_files])
        
        # Extrair e processar todos os documentos
        all_chunks = []
        for pdf_file in pdf_files:
            pages = self._extract_text_from_pdf(pdf_file)
            chunks = self._chunk_documents(pages)
            all_chunks.extend(chunks)
        
        logger.info("Total chunks created", count=len(all_chunks))
        
        # Criar ou obter collection
        try:
            self.chroma_client.delete_collection(self.collection_name)
            logger.info("Deleted existing collection")
        except Exception:
            pass
        
        collection = self.chroma_client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Gerar embeddings
        texts = [chunk["text"] for chunk in all_chunks]
        embeddings = self._create_embeddings(texts)
        
        # Preparar metadados
        metadatas = [
            {
                "source": chunk["source"],
                "page": chunk["page"],
                "chunk_id": chunk["chunk_id"]
            }
            for chunk in all_chunks
        ]
        
        ids = [chunk["chunk_id"] for chunk in all_chunks]
        
        # Adicionar à collection
        collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        elapsed_time = time.time() - start_time
        logger.info(
            "Indexing complete",
            chunks=len(all_chunks),
            elapsed_seconds=elapsed_time
        )
        
        return len(all_chunks)
    
    def get_collection(self):
        """Retorna a collection do ChromaDB"""
        try:
            return self.chroma_client.get_collection(self.collection_name)
        except Exception:
            return None
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas da indexação"""
        collection = self.get_collection()
        if collection:
            return {
                "total_chunks": collection.count(),
                "collection_name": self.collection_name
            }
        return {"total_chunks": 0, "collection_name": self.collection_name}
