import re
from typing import Tuple, Optional, List
from app.models.schemas import GuardrailViolation
import structlog

logger = structlog.get_logger()


class GuardrailService:
    """Serviço para validação de guardrails de segurança com detecção contextual"""
    
    # Padrões de prompt injection (mais robustos)
    INJECTION_PATTERNS = [
        r"ignore\s*[^\w]*\s*(previous|above|prior|all)\s*[^\w]*\s*instructions?",
        r"disregard\s*[^\w]*\s*(previous|above|prior|all)\s*[^\w]*\s*instructions?",
        r"forget\s*[^\w]*\s*(previous|above|prior|all)\s*[^\w]*\s*instructions?",
        r"system\s*[^\w]*\s*prompt",
        r"reveal\s*[^\w]*\s*(your|the)\s*[^\w]*\s*prompt",
        r"show\s*[^\w]*\s*me\s*[^\w]*\s*(your|the)\s*[^\w]*\s*prompt",
        r"what\s*[^\w]*\s*are\s*[^\w]*\s*your\s*[^\w]*\s*instructions",
        r"bypass\s*[^\w]*\s*security",
        r"jail\s*break",
        r"pretend\s*[^\w]*\s*you\s*[^\w]*\s*(are|to\s*be)",
        r"act\s*[^\w]*\s*as\s*[^\w]*\s*(if|though)",
        r"roleplay\s*[^\w]*\s*as",
        r"you\s*[^\w]*\s*are\s*[^\w]*\s*now",
        r"new\s*[^\w]*\s*instructions?",
    ]
    
    # Padrões de dados sensíveis
    SENSITIVE_PATTERNS = [
        r"\b\d{3}[\.\-]?\d{3}[\.\-]?\d{3}[\.\-]?\d{2}\b",  # CPF
        r"\b\d{2}[\.\-]?\d{3}[\.\-]?\d{3}/?\d{4}[\.\-]?\d{2}\b",  # CNPJ
        r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",  # Cartão de crédito
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email (menos restritivo)
    ]
    
    # Palavras-chave de domínio inválido
    OUT_OF_DOMAIN_KEYWORDS = [
        "cpf", "rg", "senha", "password", "cartão de crédito", "credit card",
        "número do cartão", "cvv", "código de segurança", "dados pessoais",
        "informações bancárias", "conta bancária", "saldo bancário",
        "receita médica", "prontuário", "exame médico"
    ]
    
    # Conteúdo inadequado (com contexto)
    INAPPROPRIATE_CONTENT = {
        # Termo: (contexto_suspeito, severidade)
        "hack": (r"(how\s+to|como|tutorial|guide|realizar|fazer)", "medium"),
        "exploit": (r"(use|usar|aplicar|find|encontrar)", "high"),
        "vulnerability": (r"(find|discover|exploit|usar)", "medium"),
        "malware": (r"(create|criar|desenvolver|make)", "high"),
        "virus": (r"(create|criar|desenvolver|spread|espalhar)", "high"),
        "fraude": (r"(como|fazer|realizar|aplicar)", "high"),
        "roubo": (r"(como|fazer|realizar|planejar)", "high"),
        "furto": (r"(como|fazer|realizar|planejar)", "high"),
    }
    
    def __init__(self, max_query_length: int = 500, enable_llm_guardrail: bool = False):
        self.max_query_length = max_query_length
        self.enable_llm_guardrail = enable_llm_guardrail
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[GuardrailViolation]]:
        """
        Valida a query contra todas as regras de guardrail
        
        Returns:
            Tuple[bool, Optional[GuardrailViolation]]: (is_valid, violation_details)
        """
        # 1. Verificar tamanho
        if len(query) > self.max_query_length:
            return False, GuardrailViolation(
                blocked=True,
                reason="Query too long",
                policy="MAX_LENGTH_POLICY",
                message=f"A pergunta excede o tamanho máximo permitido de {self.max_query_length} caracteres."
            )
        
        # 2. Verificar prompt injection
        query_lower = query.lower()
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return False, GuardrailViolation(
                    blocked=True,
                    reason="Prompt injection attempt detected",
                    policy="INJECTION_PREVENTION_POLICY",
                    message="Sua pergunta contém padrões que violam nossas políticas de segurança. Por favor, reformule sua pergunta."
                )
        
        # 3. Verificar dados sensíveis solicitados
        for keyword in self.OUT_OF_DOMAIN_KEYWORDS:
            if keyword in query_lower:
                return False, GuardrailViolation(
                    blocked=True,
                    reason="Request for sensitive or out-of-domain information",
                    policy="DOMAIN_RESTRICTION_POLICY",
                    message="Sua pergunta solicita informações sensíveis ou fora do domínio dos documentos disponíveis. Não posso fornecer esse tipo de informação."
                )
        
        # 4. Verificar padrões de dados sensíveis na query
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, query):
                return False, GuardrailViolation(
                    blocked=True,
                    reason="Sensitive data pattern detected in query",
                    policy="DATA_PROTECTION_POLICY",
                    message="Sua pergunta contém padrões de dados sensíveis. Por favor, remova informações pessoais da pergunta."
                )
        
        # 5. Verificar conteúdo inadequado (com contexto)
        for keyword, (suspicious_context, severity) in self.INAPPROPRIATE_CONTENT.items():
            if keyword in query_lower:
                # Verificar se está em contexto suspeito
                if re.search(suspicious_context, query_lower, re.IGNORECASE):
                    logger.warning(
                        "Suspicious content detected",
                        keyword=keyword,
                        severity=severity,
                        query=query[:50]
                    )
                    return False, GuardrailViolation(
                        blocked=True,
                        reason=f"Inappropriate content with suspicious context: {keyword}",
                        policy="CONTENT_SAFETY_POLICY",
                        message="Sua pergunta contém conteúdo inadequado ou potencialmente malicioso."
                    )
                else:
                    # Palavra presente mas sem contexto suspeito - apenas log
                    logger.info(
                        "Flagged keyword in safe context",
                        keyword=keyword,
                        query=query[:50]
                    )
        
        # Query válida
        return True, None
    
    def sanitize_response(self, response: str, preserve_context_data: bool = True) -> str:
        """
        Remove informações sensíveis da resposta
        
        Args:
            response: Resposta a ser sanitizada
            preserve_context_data: Se True, preserva dados que vieram dos documentos fonte
        """
        if not preserve_context_data:
            # Modo agressivo - remove todos os padrões
            response = re.sub(
                r"\b\d{3}[\.\-]?\d{3}[\.\-]?\d{3}[\.\-]?\d{2}\b",
                "[CPF REMOVIDO]",
                response
            )
            
            response = re.sub(
                r"\b\d{2}[\.\-]?\d{3}[\.\-]?\d{3}/?\d{4}[\.\-]?\d{2}\b",
                "[CNPJ REMOVIDO]",
                response
            )
            
            response = re.sub(
                r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
                "[CARTÃO REMOVIDO]",
                response
            )
        else:
            # Modo contextual - apenas marca com aviso
            cpf_count = len(re.findall(r"\b\d{3}[\.\-]?\d{3}[\.\-]?\d{3}[\.\-]?\d{2}\b", response))
            cnpj_count = len(re.findall(r"\b\d{2}[\.\-]?\d{3}[\.\-]?\d{3}/?\d{4}[\.\-]?\d{2}\b", response))
            
            if cpf_count > 0 or cnpj_count > 0:
                logger.warning(
                    "Sensitive data in response",
                    cpf_count=cpf_count,
                    cnpj_count=cnpj_count
                )
        
        return response
    
    def validate_response_groundedness(
        self,
        response: str,
        source_documents: List[dict],
        threshold: float = 0.5
    ) -> Tuple[bool, float]:
        """
        Valida se a resposta está baseada nos documentos fonte (groundedness)
        
        Args:
            response: Resposta gerada pelo LLM
            source_documents: Documentos usados como contexto
            threshold: Threshold de overlap mínimo (0-1)
            
        Returns:
            Tuple[bool, float]: (is_grounded, overlap_score)
        """
        if not source_documents:
            return False, 0.0
        
        # Extrair palavras significativas da resposta (sem stopwords)
        stopwords = {
            'o', 'a', 'de', 'do', 'da', 'em', 'no', 'na', 'para', 'com', 'por',
            'que', 'se', 'os', 'as', 'dos', 'das', 'um', 'uma', 'é', 'ao', 'são',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
        }
        
        response_words = set(
            word.lower() for word in re.findall(r'\b\w+\b', response)
            if len(word) > 3 and word.lower() not in stopwords
        )
        
        # Extrair palavras dos documentos fonte
        source_text = ' '.join(doc.get('text', '') for doc in source_documents)
        source_words = set(
            word.lower() for word in re.findall(r'\b\w+\b', source_text)
            if len(word) > 3 and word.lower() not in stopwords
        )
        
        if not response_words:
            return False, 0.0
        
        # Calcular overlap
        overlap = len(response_words & source_words)
        overlap_score = overlap / len(response_words)
        
        is_grounded = overlap_score >= threshold
        
        logger.info(
            "Groundedness check",
            overlap_score=round(overlap_score, 3),
            is_grounded=is_grounded,
            response_words=len(response_words),
            overlap_words=overlap
        )
        
        return is_grounded, overlap_score
        # Substituir CNPJs
        response = re.sub(
            r"\b\d{2}[\.\-]?\d{3}[\.\-]?\d{3}/?\d{4}[\.\-]?\d{2}\b",
            "[CNPJ REMOVIDO]",
            response
        )
        
        # Substituir números de cartão
        response = re.sub(
            r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
            "[CARTÃO REMOVIDO]",
            response
        )
        
        return response
