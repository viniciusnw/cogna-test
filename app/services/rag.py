import time
import requests
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
import structlog

logger = structlog.get_logger()


class RAGService:
    """Serviço de Retrieval-Augmented Generation"""
    
    def __init__(
        self,
        collection,
        embedding_model: SentenceTransformer,
        ollama_base_url: str,
        ollama_model: str,
        top_k: int = 5
    ):
        self.collection = collection
        self.embedding_model = embedding_model
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self.top_k = top_k
        
    def retrieve_documents(self, query: str, top_k: int = None) -> Tuple[List[dict], float]:
        """
        Recupera documentos relevantes do índice
        
        Returns:
            Tuple[List[dict], float]: (documentos, latência em ms)
        """
        start_time = time.time()
        
        if top_k is None:
            top_k = self.top_k
        
        # Gerar embedding da query
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Buscar no ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Formatar resultados
        documents = []
        if results["documents"] and len(results["documents"]) > 0:
            for i in range(len(results["documents"][0])):
                documents.append({
                    "text": results["documents"][0][i],
                    "source": results["metadatas"][0][i]["source"],
                    "page": results["metadatas"][0][i]["page"],
                    "distance": results["distances"][0][i],
                    "score": 1 - results["distances"][0][i]  # Converter distância em score
                })
        
        latency = (time.time() - start_time) * 1000
        logger.info("Documents retrieved", count=len(documents), latency_ms=latency)
        
        return documents, latency
    
    def _build_prompt(self, query: str, documents: List[dict]) -> str:
        """Constrói o prompt para o LLM com o contexto recuperado"""
        # Limitar tamanho de cada documento para evitar prompts muito grandes
        max_chars_per_doc = 400
        
        context_parts = []
        for doc in documents[:3]:  # Usar no máximo 3 documentos mais relevantes
            text = doc['text'][:max_chars_per_doc]
            if len(doc['text']) > max_chars_per_doc:
                text += "..."
            context_parts.append(f"[{doc['source']}, pág. {doc['page']}]\n{text}")
        
        context = "\n\n".join(context_parts)
        
        # Prompt mais conciso
        prompt = f"""Responda a pergunta usando APENAS as informações dos documentos abaixo. 
Cite as fontes (arquivo e página).

DOCUMENTOS:
{context}

PERGUNTA: {query}

RESPOSTA:"""
        
        return prompt
    
    def generate_answer(
        self,
        query: str,
        documents: List[dict]
    ) -> Tuple[str, float, int, int]:
        """
        Gera resposta usando o LLM
        
        Returns:
            Tuple[str, float, int, int]: (resposta, latência ms, prompt_tokens, completion_tokens)
        """
        start_time = time.time()
        
        prompt = self._build_prompt(query, documents)
        
        # Estimar tokens (aproximação: ~4 caracteres por token)
        prompt_tokens = len(prompt) // 4
        
        # Tentar múltiplas vezes com timeout crescente
        max_retries = 3
        base_timeout = 180  # 3 minutos
        
        for attempt in range(max_retries):
            try:
                current_timeout = base_timeout * (attempt + 1)
                
                logger.info(
                    "Calling Ollama API",
                    attempt=attempt + 1,
                    timeout=current_timeout
                )
                
                # Chamar Ollama API
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "num_predict": 512,  # Limitar tokens de resposta
                        }
                    },
                    timeout=current_timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                answer = result.get("response", "")
                completion_tokens = len(answer) // 4
                
                latency = (time.time() - start_time) * 1000
                
                logger.info(
                    "Answer generated",
                    latency_ms=latency,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    attempt=attempt + 1
                )
                
                return answer, latency, prompt_tokens, completion_tokens
                
            except requests.exceptions.Timeout as e:
                logger.warning(
                    "Ollama timeout",
                    attempt=attempt + 1,
                    timeout=current_timeout,
                    error=str(e)
                )
                
                if attempt == max_retries - 1:
                    raise Exception(
                        f"O modelo LLM não respondeu após {max_retries} tentativas. "
                        "O modelo pode estar carregando pela primeira vez (isso pode levar 5-10 minutos). "
                        "Tente novamente em alguns minutos."
                    )
                    
                # Aguardar antes de tentar novamente
                time.sleep(5)
                
            except requests.exceptions.RequestException as e:
                logger.error("Error calling Ollama", error=str(e), attempt=attempt + 1)
                
                if attempt == max_retries - 1:
                    raise Exception(f"Erro ao comunicar com o modelo LLM: {str(e)}")
                    
                time.sleep(2)
    
    def answer_question(
        self,
        query: str,
        top_k: int = None
    ) -> Tuple[str, List[dict], float, float, int, int]:
        """
        Pipeline completo de RAG: retrieve + generate
        
        Returns:
            Tuple: (answer, documents, retrieval_latency, llm_latency, prompt_tokens, completion_tokens)
        """
        # Retrieval
        documents, retrieval_latency = self.retrieve_documents(query, top_k)
        
        if not documents:
            return (
                "Não encontrei informações relevantes nos documentos para responder sua pergunta.",
                [],
                retrieval_latency,
                0.0,
                0,
                0
            )
        
        # Generation
        answer, llm_latency, prompt_tokens, completion_tokens = self.generate_answer(
            query,
            documents
        )
        
        return answer, documents, retrieval_latency, llm_latency, prompt_tokens, completion_tokens
