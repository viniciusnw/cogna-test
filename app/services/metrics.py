import time
import structlog
from typing import Dict, List
from datetime import datetime
from collections import defaultdict


logger = structlog.get_logger()


class MetricsService:
    """Serviço de observabilidade e métricas"""
    
    def __init__(self):
        self.request_count = 0
        self.blocked_count = 0
        self.latencies: List[float] = []
        self.retrieval_latencies: List[float] = []
        self.llm_latencies: List[float] = []
        self.token_usage: List[int] = []
        self.request_history: List[Dict] = []
        
    def record_request(
        self,
        query: str,
        answer: str,
        total_latency: float,
        retrieval_latency: float,
        llm_latency: float,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        top_k: int,
        context_size: int,
        citations_count: int,
        blocked: bool = False,
        blocked_reason: str = None
    ):
        """Registra métricas de uma requisição"""
        self.request_count += 1
        
        if blocked:
            self.blocked_count += 1
        
        if not blocked:
            self.latencies.append(total_latency)
            self.retrieval_latencies.append(retrieval_latency)
            self.llm_latencies.append(llm_latency)
            self.token_usage.append(total_tokens)
        
        # Manter histórico das últimas 100 requisições
        request_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "query_length": len(query),
            "answer_length": len(answer) if answer else 0,
            "total_latency_ms": total_latency,
            "retrieval_latency_ms": retrieval_latency,
            "llm_latency_ms": llm_latency,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "top_k": top_k,
            "context_size": context_size,
            "citations_count": citations_count,
            "blocked": blocked,
            "blocked_reason": blocked_reason
        }
        
        self.request_history.append(request_log)
        if len(self.request_history) > 100:
            self.request_history.pop(0)
        
        logger.info(
            "Request recorded",
            request_count=self.request_count,
            blocked=blocked,
            total_latency_ms=total_latency
        )
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas agregadas"""
        if not self.latencies:
            return {
                "total_requests": self.request_count,
                "blocked_requests": self.blocked_count,
                "success_requests": 0,
                "block_rate": 0.0,
                "avg_latency_ms": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "avg_retrieval_latency_ms": 0.0,
                "avg_llm_latency_ms": 0.0,
                "avg_tokens": 0.0,
                "total_tokens": 0
            }
        
        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)
        
        return {
            "total_requests": self.request_count,
            "blocked_requests": self.blocked_count,
            "success_requests": len(self.latencies),
            "block_rate": self.blocked_count / self.request_count if self.request_count > 0 else 0.0,
            "avg_latency_ms": sum(self.latencies) / n,
            "p50_latency_ms": sorted_latencies[n // 2],
            "p95_latency_ms": sorted_latencies[int(n * 0.95)],
            "p99_latency_ms": sorted_latencies[int(n * 0.99)],
            "avg_retrieval_latency_ms": sum(self.retrieval_latencies) / len(self.retrieval_latencies),
            "avg_llm_latency_ms": sum(self.llm_latencies) / len(self.llm_latencies),
            "avg_tokens": sum(self.token_usage) / len(self.token_usage),
            "total_tokens": sum(self.token_usage)
        }
    
    def get_recent_requests(self, limit: int = 10) -> List[Dict]:
        """Retorna as requisições mais recentes"""
        return self.request_history[-limit:]


# Singleton instance
metrics_service = MetricsService()
