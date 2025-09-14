#!/bin/bash

# ===========================================
# SCRIPT DE DEPLOY - MIGRAÇÃO LEGACY
# ===========================================

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy da migração legacy..."
echo "Timestamp: $(date -Iseconds)"
echo "=========================================="

# Validar pré-requisitos
echo "🔍 Executando validações pré-deploy..."
python3 scripts/validate_production.py

if [ $? -ne 0 ]; then
    echo "❌ Validações falharam. Deploy cancelado."
    exit 1
fi

# Backup da configuração atual
echo "💾 Criando backup da configuração..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Aplicar nova configuração
echo "⚙️ Aplicando configuração de produção..."
cp backend/config/production.env .env

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Executar testes críticos
echo "🧪 Executando testes críticos..."
pytest backend/tests/test_legacy_service_adapter.py -v

if [ $? -ne 0 ]; then
    echo "❌ Testes falharam. Restaurando backup..."
    cp .env.backup.* .env
    exit 1
fi

# Reiniciar serviços
echo "🔄 Reiniciando aplicação..."
sudo systemctl restart glpi-dashboard
sudo systemctl restart nginx

# Aguardar inicialização
echo "⏳ Aguardando inicialização..."
sleep 10

# Validar deploy
echo "✅ Validando deploy..."
for i in {1..5}; do
    if curl -f -s http://localhost:5000/api/health > /dev/null; then
        echo "✅ Aplicação respondendo"
        break
    else
        echo "⏳ Tentativa $i/5 - aguardando..."
        sleep 5
    fi
done

# Testar endpoints críticos
echo "🔍 Testando endpoints críticos..."

# Testar métricas
if curl -f -s http://localhost:5000/api/metrics/v2 > /dev/null; then
    echo "✅ Endpoint de métricas OK"
else
    echo "❌ Endpoint de métricas falhou"
    exit 1
fi

# Testar monitoramento
if curl -f -s http://localhost:5000/api/monitoring/legacy/health > /dev/null; then
    echo "✅ Monitoramento legacy OK"
else
    echo "❌ Monitoramento legacy falhou"
    exit 1
fi

echo "=========================================="
echo "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
echo "📊 Status: Serviços legacy ativos"
echo "🔗 Monitoramento: http://localhost:5000/api/monitoring/legacy/health"
echo "📈 Métricas: http://localhost:5000/api/monitoring/legacy/metrics"
echo "=========================================="