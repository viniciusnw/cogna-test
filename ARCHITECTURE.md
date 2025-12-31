# Micro-RAG - Decisões de Arquitetura

## Visão Geral

Este documento detalha as decisões arquiteturais do projeto Micro-RAG, explicando os trade-offs e justificativas para cada escolha.

## 1. Ingestão e Indexação

### 1.1 Estratégia de Chunking

**Decisão:** RecursiveCharacterTextSplitter com chunk_size=500 e overlap=50

**Justificativa:**

- **500 caracteres** (~125 tokens) permite contexto suficiente sem exceder limites
- **10% overlap** (50 chars) evita perda de informação nas fronteiras
- **Recursive splitter** respeita estrutura natural do texto
- Popular no ecossistema LangChain por dividir texto de forma inteligente e recursiva

**Trade-offs:**

- ✅ Bom equilíbrio contexto/performance
- ✅ Funciona bem para documentos estruturados
- ❌ Pode quebrar tabelas ou listas
- ❌ Não considera semântica profunda

### 1.2 Modelo de Embeddings

**Decisão:** all-MiniLM-L6-v2

**Justificativa:**

- Gratuito e local
- 384 dimensões (leve)
- Multilíngue (PT/EN)
- Latência baixa (~20ms)

**Trade-offs:**

- ✅ Rápido e eficiente
- ✅ Sem custos
- ❌ Qualidade inferior a modelos maiores
- ❌ Performance moderada em PT-BR

### 1.3 Vector Database

**Decisão:** ChromaDB

**Justificativa:**

- Fácil setup com persistence
- SQLite backend
- Suficiente para <100k documentos
- Boa DX

**Trade-offs:**

- ✅ Simplicidade
- ✅ Persistence automática
- ❌ Performance limitada em escala
- ❌ Sem clustering/replicação

## 2. RAG Pipeline

### 2.1 Top-K Selection

**Decisão:** Top-K = 5 (default, configurável 1-10)

**Justificativa:**

- 5 chunks × 500 chars = ~2500 chars de contexto
- Llama2 suporta 4096 tokens (~16k chars)
- Margem para prompt e resposta

**Trade-offs:**

- ✅ Contexto rico
- ✅ Múltiplas fontes
- ❌ Pode incluir documentos irrelevantes
- ❌ Aumenta latência levemente

### 2.2 Re-ranking

**Decisão:** NÃO implementado

**Justificativa:**

- Aumentaria latência em 200-500ms
- Complexidade adicional

**Quando reconsiderar:**

- Top-K > 10
- Necessidade de precisão crítica
- Budget de latência permitir

### 2.3 LLM Selection

**Decisão:** Ollama + Llama2-7B

**Alternativas:**
| Modelo | Custo/1M tokens | Latência | Qualidade |
|--------|----------------|----------|----------- |
| GPT-4        | $30-60 | 2-4s  | ⭐⭐⭐⭐⭐     |
| GPT-3.5      | $1-2   | 1-2s  | ⭐⭐⭐⭐       |
| Claude       | $8-24  | 1-3s  | ⭐⭐⭐⭐⭐     |
| Llama2 Local | $0     | 5-15s | ⭐⭐⭐         |

**Justificativa:**

- Zero custo
- Privacidade total
- Controle completo
- Bom para POC/demo

**Trade-offs:**

- ✅ Grátis
- ✅ Privado
- ✅ Sem rate limits
- ❌ Latência alta sem GPU
- ❌ Qualidade inferior
- ❌ Requer infra própria

## 3. Guardrails

### 3.1 Abordagem

**Decisão:** Rule-based + Regex patterns

**Justificativa:**

- Latência ~1-5ms vs ~500ms (LLM)
- Determinístico e explicável
- Fácil de manter e debugar

**Trade-offs:**

- ✅ Rápido
- ✅ Previsível
- ❌ Requer manutenção manual
- ❌ Pode ter falsos positivos

### 3.2 Camadas de Proteção

1. **Input Validation:** Tamanho, formato
2. **Pattern Matching:** Injection, dados sensíveis
3. **Keyword Filtering:** Domínio, conteúdo
4. **Output Sanitization:** Remoção de PII

**Justificativa:**

- Defense in depth
- Cada camada captura tipos diferentes de ataques
- Última linha de defesa no output

## 4. Observabilidade

### 4.1 Métricas Coletadas

**Por Requisição:**

- Timestamps
- Latências (total, retrieval, LLM)
- Tokens (prompt, completion, total)
- Top-K usado
- Tamanho do contexto
- Número de citações
- Status de bloqueio

**Agregadas:**

- Count total
- Taxa de bloqueio
- Percentis de latência (p50, p95, p99)
- Média de tokens

**Justificativa:**

- Permite debugging detalhado
- Base para SLOs
- Identificação de anomalias

### 4.2 Storage

**Decisão:** In-memory (últimas 100 requisições)

**Justificativa:**

- Suficiente para POC
- Zero overhead de setup
- Dados disponíveis via API

## 5. Deployment

### 5.1 Containerização

**Decisão:** Docker + Docker Compose

**Componentes:**

- `ollama`: Serviço LLM
- `api`: FastAPI application
- Volumes para persistence

**Justificativa:**

- Reprodutível
- Isolado
- Fácil de escalar (horizontalmente)

### 5.2 Network Architecture

```
┌─────────────────────────┐
│  Internet/Load Balancer │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   FastAPI (Port 8000)   │
│   - Guardrails          │
│   - RAG Orchestration   │
└───────┬────────┬────────┘
        │        │
        ▼        ▼
┌──────────┐ ┌──────────┐
│ ChromaDB │ │  Ollama  │
│ (Vectors)│ │ (11434)  │
└──────────┘ └──────────┘
```

**Justificativa:**

- API Gateway pattern
- Isolamento de responsabilidades
- Ollama não exposto diretamente

## 6. Segurança

### 6.1 Threat Model

**Ameaças Consideradas:**

1. Prompt Injection
2. Data Exfiltration (PII)
3. DoS via queries longas
4. Out-of-domain requests

**Mitigações:**

1. Pattern matching + blocklist
2. Output sanitization
3. Rate limiting (futuro) + max length
4. Keyword filtering

## 7. Qualidade de Resposta

### 7.1 Groundedness

**Problema:** Como garantir que respostas vêm dos documentos?

**Abordagens:**

1. **Prompt Engineering:** Instruções explícitas
2. **Citation Requirement:** Forçar citações

## 8. Limitações

1. **Latência Alta:** 5-15s sem GPU
2. **Escala Limitada:** ChromaDB in-memory
3. **Português:** Llama2 tem viés em inglês
4. **Tabelas/Imagens:** Não processadas
5. **Guardrails Simples:** Regex-based e Rule-
