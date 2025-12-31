#!/bin/bash

# Script para verificar o status do Ollama e do modelo Llama2

echo "=== Diagnóstico do Micro-RAG ==="
echo ""

echo "1️⃣ Verificando containers..."
docker-compose ps

echo ""
echo "2️⃣ Verificando se Ollama está respondendo..."
OLLAMA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags)

if [ "$OLLAMA_STATUS" == "200" ]; then
    echo "✅ Ollama está online"
else
    echo "❌ Ollama não está respondendo (HTTP $OLLAMA_STATUS)"
    echo "   Tente: docker-compose restart ollama"
    exit 1
fi

echo ""
echo "3️⃣ Verificando modelos instalados..."
MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4)

if echo "$MODELS" | grep -q "llama2"; then
    echo "✅ Modelo Llama2 está instalado"
    echo ""
    echo "Modelos disponíveis:"
    echo "$MODELS"
else
    echo "❌ Modelo Llama2 NÃO encontrado"
    echo ""
    echo "Modelos disponíveis:"
    echo "$MODELS"
    echo ""
    echo "⚠️  AÇÃO NECESSÁRIA: Baixar o modelo Llama2"
    echo "Execute o comando:"
    echo "   docker exec micro-rag-ollama ollama pull llama2"
    echo ""
    echo "⏱️  Isso pode levar 10-15 minutos (o modelo tem ~4GB)"
    exit 1
fi

echo ""
echo "4️⃣ Testando geração de texto simples..."
TEST_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
    -d '{"model": "llama2", "prompt": "Say hello in one word", "stream": false}' \
    --max-time 60)

if echo "$TEST_RESPONSE" | grep -q "response"; then
    echo "✅ Ollama está gerando respostas"
    ANSWER=$(echo "$TEST_RESPONSE" | grep -o '"response":"[^"]*"' | cut -d'"' -f4 | head -c 50)
    echo "   Resposta: $ANSWER..."
else
    echo "⚠️  Ollama demorou muito para responder"
    echo "   O modelo pode estar carregando pela primeira vez"
    echo "   Aguarde 2-3 minutos e tente novamente"
fi

echo ""
echo "5️⃣ Verificando API FastAPI..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$API_STATUS" == "200" ]; then
    echo "✅ API FastAPI está respondendo"
    
    # Verificar health details
    HEALTH=$(curl -s http://localhost:8000/health)
    echo "   Status: $(echo $HEALTH | grep -o '"status":"[^"]*"' | cut -d'"' -f4)"
    echo "   Documentos indexados: $(echo $HEALTH | grep -o '"documents_indexed":[0-9]*' | cut -d':' -f2)"
else
    echo "❌ API FastAPI não está respondendo (HTTP $API_STATUS)"
    echo "   Verifique os logs: docker-compose logs api"
fi