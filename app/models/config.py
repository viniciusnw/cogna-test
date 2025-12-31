from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Ollama Configuration
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama2"
    
    # Embedding Model
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # RAG Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    rerank_enabled: bool = False
    
    # Application
    log_level: str = "INFO"
    data_path: str = "/app/data"
    chroma_db_path: str = "/app/chroma_db"
    
    # Guardrails
    enable_guardrails: bool = True
    max_query_length: int = 500
    
    # Cost estimation (for Llama2 local model, cost is 0)
    prompt_token_cost: float = 0.0
    completion_token_cost: float = 0.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
