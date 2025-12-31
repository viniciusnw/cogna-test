from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Citation(BaseModel):
    """Citação de fonte do documento"""
    source: str = Field(..., description="Nome do arquivo fonte")
    excerpt: str = Field(..., description="Trecho relevante do documento")
    page: Optional[int] = Field(None, description="Número da página (se aplicável)")
    score: Optional[float] = Field(None, description="Score de relevância")


class Metrics(BaseModel):
    """Métricas de execução da requisição"""
    total_latency_ms: float = Field(..., description="Latência total em milissegundos")
    retrieval_latency_ms: float = Field(..., description="Latência do retrieval em ms")
    llm_latency_ms: float = Field(..., description="Latência da geração LLM em ms")
    prompt_tokens: int = Field(..., description="Número aproximado de tokens no prompt")
    completion_tokens: int = Field(..., description="Número aproximado de tokens na resposta")
    total_tokens: int = Field(..., description="Total de tokens utilizados")
    estimated_cost_usd: float = Field(..., description="Custo estimado em USD")
    top_k_used: int = Field(..., description="Quantidade de documentos recuperados")
    context_size: int = Field(..., description="Tamanho do contexto em caracteres")
    groundedness_score: Optional[float] = Field(None, description="Score de groundedness (0-1)")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class QuestionRequest(BaseModel):
    """Requisição de pergunta"""
    question: str = Field(..., description="Pergunta a ser respondida", min_length=1, max_length=500)
    top_k: Optional[int] = Field(5, description="Número de documentos a recuperar", ge=1, le=10)


class QuestionResponse(BaseModel):
    """Resposta da pergunta"""
    answer: str = Field(..., description="Resposta gerada pelo modelo")
    citations: List[Citation] = Field(..., description="Lista de citações das fontes")
    metrics: Metrics = Field(..., description="Métricas de execução")
    status: str = Field("success", description="Status da resposta")


class GuardrailViolation(BaseModel):
    """Violação de guardrail detectada"""
    blocked: bool = Field(..., description="Se a requisição foi bloqueada")
    reason: str = Field(..., description="Motivo do bloqueio")
    policy: str = Field(..., description="Política violada")
    message: str = Field(..., description="Mensagem para o usuário")


class HealthResponse(BaseModel):
    """Resposta de health check"""
    status: str
    ollama_status: str
    documents_indexed: int
    embedding_model: str
    timestamp: str
