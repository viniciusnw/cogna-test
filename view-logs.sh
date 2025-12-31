#!/bin/bash

# Script para visualizar e analisar logs do Micro-RAG

LOG_DIR="/mnt/www/Cogna/logs"
# Usar data UTC para corresponder aos logs
TODAY=$(date -u +%Y-%m-%d)
LOG_FILE="$LOG_DIR/micro-rag-$TODAY.log"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo "=== Micro-RAG Log Viewer ==="
    echo ""
    echo "Uso: ./view-logs.sh [opção]"
    echo ""
    echo "Opções:"
    echo "  tail           Acompanha logs em tempo real (padrão)"
    echo "  today          Mostra logs de hoje"
    echo "  errors         Mostra apenas erros"
    echo "  warnings       Mostra warnings"
    echo "  questions      Mostra perguntas recebidas"
    echo "  slow           Mostra requests lentas (>60s)"
    echo "  blocked        Mostra requests bloqueadas por guardrails"
    echo "  stats          Estatísticas dos logs"
    echo "  clean          Remove logs antigos (>7 dias)"
    echo ""
}

tail_logs() {
    echo -e "${GREEN}📊 Acompanhando logs em tempo real...${NC}"
    echo -e "${YELLOW}Ctrl+C para sair${NC}"
    echo ""
    tail -f "$LOG_FILE" | while read line; do
        if echo "$line" | grep -q '"level": "error"'; then
            echo -e "${RED}$line${NC}"
        elif echo "$line" | grep -q '"level": "warning"'; then
            echo -e "${YELLOW}$line${NC}"
        elif echo "$line" | grep -q 'Question processed'; then
            echo -e "${GREEN}$line${NC}"
        else
            echo "$line"
        fi
    done
}

show_today() {
    echo -e "${GREEN}📅 Logs de hoje ($TODAY)${NC}"
    echo ""
    cat "$LOG_FILE" | jq -r 'select(.event != null) | "\(.timestamp) [\(.level)] \(.event)"' 2>/dev/null || cat "$LOG_FILE"
}

show_errors() {
    echo -e "${RED}❌ Erros encontrados:${NC}"
    echo ""
    grep '"level": "error"' "$LOG_FILE" | jq -r '"\(.timestamp) - \(.event): \(.error // .message)"' 2>/dev/null
}

show_warnings() {
    echo -e "${YELLOW}⚠️  Warnings encontrados:${NC}"
    echo ""
    grep '"level": "warning"' "$LOG_FILE" | jq -r '"\(.timestamp) - \(.event)"' 2>/dev/null
}

show_questions() {
    echo -e "${BLUE}❓ Perguntas recebidas:${NC}"
    echo ""
    grep "Received question" "$LOG_FILE" | jq -r '"\(.timestamp) - \(.question)"' 2>/dev/null
}

show_slow() {
    echo -e "${YELLOW}🐌 Requests lentas (>60000ms):${NC}"
    echo ""
    grep "Question processed" "$LOG_FILE" | jq -r 'select(.total_latency_ms > 60000) | "\(.timestamp) - \(.total_latency_ms)ms - \(.citations) citações"' 2>/dev/null
}

show_blocked() {
    echo -e "${RED}🚫 Requests bloqueadas:${NC}"
    echo ""
    grep "Query blocked" "$LOG_FILE" | jq -r '"\(.timestamp) - Política: \(.violation)"' 2>/dev/null
}

show_stats() {
    echo -e "${GREEN}📊 Estatísticas dos Logs de Hoje${NC}"
    echo ""
    
    total_lines=$(wc -l < "$LOG_FILE")
    total_requests=$(grep -c "Received question" "$LOG_FILE" 2>/dev/null || echo 0)
    total_errors=$(grep -c '"level": "error"' "$LOG_FILE" 2>/dev/null || echo 0)
    total_warnings=$(grep -c '"level": "warning"' "$LOG_FILE" 2>/dev/null || echo 0)
    total_blocked=$(grep -c "Query blocked" "$LOG_FILE" 2>/dev/null || echo 0)
    
    echo "Total de linhas: $total_lines"
    echo "Total de requests: $total_requests"
    echo "Erros: $total_errors"
    echo "Warnings: $total_warnings"
    echo "Bloqueados: $total_blocked"
    echo ""
    
    if [ $total_requests -gt 0 ]; then
        success_rate=$(echo "scale=2; (($total_requests - $total_errors) / $total_requests) * 100" | bc)
        echo "Taxa de sucesso: ${success_rate}%"
    fi
    
    echo ""
    echo "Latências médias (quando disponível):"
    grep "Question processed" "$LOG_FILE" | jq -r '.total_latency_ms' 2>/dev/null | awk '{sum+=$1; count++} END {if(count>0) printf "  Total: %.2fms\n", sum/count}'
    grep "Documents retrieved" "$LOG_FILE" | jq -r '.latency_ms' 2>/dev/null | awk '{sum+=$1; count++} END {if(count>0) printf "  Retrieval: %.2fms\n", sum/count}'
    grep "Answer generated" "$LOG_FILE" | jq -r '.latency_ms' 2>/dev/null | awk '{sum+=$1; count++} END {if(count>0) printf "  LLM: %.2fms\n", sum/count}'
}

clean_old_logs() {
    echo -e "${YELLOW}🧹 Limpando logs antigos (>7 dias)...${NC}"
    find "$LOG_DIR" -name "micro-rag-*.log" -mtime +7 -delete
    echo -e "${GREEN}✅ Limpeza concluída${NC}"
}

# Main
case "${1:-tail}" in
    tail)
        tail_logs
        ;;
    today)
        show_today
        ;;
    errors)
        show_errors
        ;;
    warnings)
        show_warnings
        ;;
    questions)
        show_questions
        ;;
    slow)
        show_slow
        ;;
    blocked)
        show_blocked
        ;;
    stats)
        show_stats
        ;;
    clean)
        clean_old_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Opção inválida: $1${NC}"
        show_help
        exit 1
        ;;
esac
