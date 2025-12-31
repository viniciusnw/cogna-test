#!/bin/bash

# Script para inicializar o ambiente e baixar modelo Llama2

echo "=== Micro-RAG Setup Script ==="
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Por favor, instale o Docker primeiro."
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

echo "✅ Docker e Docker Compose detectados"
echo ""

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    cp .env.example .env
    echo "✅ Arquivo .env criado"
else
    echo "ℹ️  Arquivo .env já existe"
fi

echo ""
echo "🚀 Iniciando containers..."
docker compose down ; docker compose up -d --build

echo ""
echo "⏳ Aguardando Ollama inicializar (30 segundos)..."
sleep 30

echo ""
echo "📦 Baixando modelo Llama2 (isso pode levar alguns minutos na primeira vez)..."
docker exec micro-rag-ollama ollama pull llama2

if [ $? -eq 0 ]; then
    echo "✅ Modelo Llama2 baixado com sucesso!"
else
    echo "⚠️  Erro ao baixar o modelo. Tente novamente manualmente:"
    echo "   docker exec micro-rag-ollama ollama pull llama2"
fi

echo ""
echo "🔄 Reiniciando serviço da API..."
docker compose restart api

echo ""
echo "⏳ Aguardando API inicializar (20 segundos)..."
sleep 20

echo ""
echo "✅ Setup completo!"
echo ""
echo "📚 Documentação da API: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/health"
echo "📊 Métricas: http://localhost:8000/api/v1/metrics"
echo ""
echo "Para fazer uma pergunta:"
echo 'curl -X POST http://localhost:8000/api/v1/ask -H "Content-Type: application/json" -d '"'"'{"question": "Do que se trata o contrato?"}'"'"
echo ""
echo "Para ver os logs:"
echo "docker compose logs -f api"
