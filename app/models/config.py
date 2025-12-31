from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Ollama Configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama2")
    
    # Embedding Model
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # RAG Configuration
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    top_k: int = int(os.getenv("TOP_K", "5"))
    rerank_enabled: bool = os.getenv("RERANK_ENABLED", "false").lower() == "true"
    
    # Application
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    data_path: str = os.getenv("DATA_PATH", "/app/data")
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "/app/chroma_db")
    
    # Guardrails
    enable_guardrails: bool = os.getenv("ENABLE_GUARDRAILS", "true").lower() == "true"
    max_query_length: int = int(os.getenv("MAX_QUERY_LENGTH", "500"))
    
    # Cost estimation (for Llama2 local model, cost is 0)
    prompt_token_cost: float = 0.0
    completion_token_cost: float = 0.0
    
    class Config:
        case_sensitive = False


settings = Settings()
