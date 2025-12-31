import time
import structlog
import requests
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime

from app.models.config import settings
from app.models.schemas import (
    QuestionRequest,
    QuestionResponse,
    Citation,
    Metrics,
    GuardrailViolation,
    HealthResponse
)
from app.services.indexer import DocumentIndexer
from app.services.rag import RAGService
from app.services.guardrails import GuardrailService
from app.services.metrics import metrics_service
from app.utils.logger import setup_logging

# Configurar logging estruturado com arquivo
logger = setup_logging(log_dir="/app/logs", log_level=settings.log_level)

# Variáveis globais para serviços
indexer: DocumentIndexer = None
rag_service: RAGService = None
guardrail_service: GuardrailService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    global indexer, rag_service, guardrail_service
    
    logger.info("Starting application initialization")
    
    # Inicializar serviços
    indexer = DocumentIndexer(
        data_path=settings.data_path,
        chroma_db_path=settings.chroma_db_path,
        embedding_model_name=settings.embedding_model,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )
    
    # Indexar documentos
    logger.info("Starting document indexation")
    indexed_count = indexer.index_documents()
    logger.info("Document indexation complete", indexed_chunks=indexed_count)
    
    # Inicializar RAG service
    collection = indexer.get_collection()
    if not collection:
        raise Exception("Failed to initialize ChromaDB collection")
    
    rag_service = RAGService(
        collection=collection,
        embedding_model=indexer.embedding_model,
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        top_k=settings.top_k
    )
    
    # Inicializar guardrails
    guardrail_service = GuardrailService(
        max_query_length=settings.max_query_length
    )
    
    logger.info("Application initialization complete")
    
    yield
    
    # Cleanup
    logger.info("Shutting down application")


# Criar aplicação FastAPI
app = FastAPI(
    title="Micro-RAG API",
    description="Microserviço de RAG com Guardrails para responder perguntas baseadas em documentos",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", response_model=dict)
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "service": "Micro-RAG API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ask": "/api/v1/ask",
            "metrics": "/api/v1/metrics"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check do serviço"""
    # Verificar status do Ollama
    ollama_status = "unhealthy"
    try:
        response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_status = "healthy"
    except Exception as e:
        logger.error("Ollama health check failed", error=str(e))
    
    # Obter estatísticas do índice
    stats = indexer.get_stats() if indexer else {"total_chunks": 0}
    
    return HealthResponse(
        status="healthy" if ollama_status == "healthy" else "degraded",
        ollama_status=ollama_status,
        documents_indexed=stats["total_chunks"],
        embedding_model=settings.embedding_model,
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/api/v1/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Endpoint principal para fazer perguntas
    
    - **question**: Pergunta a ser respondida (obrigatório)
    - **top_k**: Número de documentos a recuperar (opcional, padrão: 5)
    """
    start_time = time.time()
    
    logger.info("Received question", question=request.question, top_k=request.top_k)
    
    # 1. Validar com guardrails
    if settings.enable_guardrails:
        is_valid, violation = guardrail_service.validate_query(request.question)
        
        if not is_valid:
            logger.warning("Query blocked by guardrail", violation=violation.policy)
            
            # Registrar métrica de bloqueio
            total_latency = (time.time() - start_time) * 1000
            metrics_service.record_request(
                query=request.question,
                answer="",
                total_latency=total_latency,
                retrieval_latency=0,
                llm_latency=0,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                top_k=request.top_k,
                context_size=0,
                citations_count=0,
                blocked=True,
                blocked_reason=violation.policy
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "query_blocked",
                    "violation": violation.dict()
                }
            )
    
    # 2. Processar pergunta com RAG
    try:
        answer, documents, retrieval_latency, llm_latency, prompt_tokens, completion_tokens = \
            rag_service.answer_question(request.question, request.top_k)
        
        # Validar groundedness (resposta baseada nos documentos)
        groundedness_score = None
        if settings.enable_guardrails and documents:
            is_grounded, groundedness_score = guardrail_service.validate_response_groundedness(
                answer, documents, threshold=0.3
            )
            
            if not is_grounded:
                logger.warning(
                    "Low groundedness detected",
                    score=groundedness_score,
                    question=request.question[:50]
                )
                # Não bloqueia, mas adiciona aviso
                answer = f"[AVISO: Resposta pode não estar totalmente baseada nos documentos]\n\n{answer}"
        
        # Sanitizar resposta (modo contextual - preserva dados dos documentos)
        if settings.enable_guardrails:
            answer = guardrail_service.sanitize_response(answer, preserve_context_data=True)
        
    except Exception as e:
        logger.error("Error processing question", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "processing_failed", "message": str(e)}
        )
    
    # 3. Preparar citações
    citations = [
        Citation(
            source=doc["source"],
            excerpt=doc["text"][:300] + "..." if len(doc["text"]) > 300 else doc["text"],
            page=doc["page"],
            score=round(doc["score"], 4)
        )
        for doc in documents
    ]
    
    # 4. Calcular métricas
    total_latency = (time.time() - start_time) * 1000
    total_tokens = prompt_tokens + completion_tokens
    context_size = sum(len(doc["text"]) for doc in documents)
    
    # Custo estimado (Llama2 local = grátis)
    estimated_cost = (
        prompt_tokens * settings.prompt_token_cost +
        completion_tokens * settings.completion_token_cost
    )
    
    metrics = Metrics(
        total_latency_ms=round(total_latency, 2),
        retrieval_latency_ms=round(retrieval_latency, 2),
        llm_latency_ms=round(llm_latency, 2),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=round(estimated_cost, 6),
        top_k_used=len(documents),
        context_size=context_size,
        groundedness_score=round(groundedness_score, 3) if groundedness_score else None
    )
    
    # 5. Registrar métricas
    metrics_service.record_request(
        query=request.question,
        answer=answer,
        total_latency=total_latency,
        retrieval_latency=retrieval_latency,
        llm_latency=llm_latency,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        top_k=request.top_k,
        context_size=context_size,
        citations_count=len(citations),
        blocked=False
    )
    
    logger.info(
        "Question processed successfully",
        total_latency_ms=total_latency,
        citations=len(citations)
    )
    
    return QuestionResponse(
        answer=answer,
        citations=citations,
        metrics=metrics,
        status="success"
    )


@app.get("/api/v1/metrics")
async def get_metrics():
    """
    Retorna métricas de observabilidade do serviço
    """
    stats = metrics_service.get_statistics()
    recent = metrics_service.get_recent_requests(limit=10)
    
    return {
        "statistics": stats,
        "recent_requests": recent,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global de exceções"""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
