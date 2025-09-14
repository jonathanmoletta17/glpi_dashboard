# Troubleshooting Legacy Services

## Visão Geral

Este documento fornece cenários específicos de troubleshooting para os serviços legacy do GLPI Dashboard, incluindo diagnósticos detalhados e soluções práticas.

## Cenários Comuns de Problemas

### 1. Falha de Conectividade com GLPI

#### Sintomas
- Timeout nas requisições
- Erro 500 nos endpoints legacy
- Status "unhealthy" no health check

#### Diagnóstico
```bash
# Verificar conectividade básica
curl -v http://seu-glpi.com/apirest.php/

# Testar autenticação
curl -X POST http://seu-glpi.com/apirest.php/initSession \
  -H "Content-Type: application/json" \
  -d '{"login": "usuario", "password": "senha"}'

# Verificar logs do adapter
grep "connection" backend/logs/app.log | tail -10
```

#### Soluções
1. **Verificar configuração de rede**:
   ```bash
   # Testar DNS
   nslookup seu-glpi.com
   
   # Testar conectividade
   telnet seu-glpi.com 80
   ```

2. **Validar credenciais**:
   ```bash
   # Verificar variáveis de ambiente
   echo $GLPI_URL
   echo $GLPI_USER_TOKEN
   echo $GLPI_APP_TOKEN
   ```

3. **Configurar timeout**:
   ```bash
   export LEGACY_ADAPTER_TIMEOUT=30
   export LEGACY_ADAPTER_RETRY_COUNT=3
   ```

### 2. Performance Degradada

#### Sintomas
- Tempo de resposta > 2 segundos
- P95 > 300ms
- CPU alta no servidor

#### Diagnóstico
```bash
# Monitorar métricas em tempo real
watch -n 2 'curl -s http://localhost:5000/api/monitoring/legacy/metrics | jq ".metrics | to_entries[] | select(.value.avg_response_time > 1000)"'

# Verificar cache hit rate
curl -s http://localhost:5000/api/monitoring/legacy/metrics | jq '.cache_stats'

# Analisar queries lentas
grep "slow_query" backend/logs/app.log | tail -20
```

#### Soluções
1. **Otimizar cache**:
   ```bash
   # Aumentar TTL do cache
   export CACHE_TTL=300
   
   # Verificar uso de memória
   free -h
   ```

2. **Ajustar pool de conexões**:
   ```python
   # Em config/settings.py
   LEGACY_ADAPTER_POOL_SIZE = 20
   LEGACY_ADAPTER_MAX_OVERFLOW = 30
   ```

3. **Implementar circuit breaker**:
   ```bash
   export CIRCUIT_BREAKER_ENABLED=true
   export CIRCUIT_BREAKER_THRESHOLD=5
   ```

### 3. Taxa de Erro Alta

#### Sintomas
- error_rate_percent > 5%
- Muitos HTTP 500/502/503
- Falhas intermitentes

#### Diagnóstico
```bash
# Verificar erros recentes
curl http://localhost:5000/api/monitoring/legacy/health

# Logs detalhados de erro
grep "ERROR" backend/logs/app.log | grep "legacy_adapter" | tail -20

# Analisar códigos de status
grep "status_code" backend/logs/app.log | awk '{print $NF}' | sort | uniq -c
```

#### Soluções
1. **Verificar tokens GLPI**:
   ```bash
   # Testar token de usuário
   curl -H "Session-Token: $GLPI_USER_TOKEN" \
        -H "App-Token: $GLPI_APP_TOKEN" \
        http://seu-glpi.com/apirest.php/getMyProfiles
   ```

2. **Aumentar retry e timeout**:
   ```bash
   export LEGACY_ADAPTER_RETRY_COUNT=5
   export LEGACY_ADAPTER_RETRY_DELAY=2
   export LEGACY_ADAPTER_TIMEOUT=30
   ```

3. **Verificar permissões GLPI**:
   - Usuário deve ter perfil "Super-Admin" ou "Admin"
   - API REST deve estar habilitada
   - Verificar ACLs no GLPI

### 4. Dados Inconsistentes

#### Sintomas
- Diferenças entre adapters na comparação
- Valores nulos inesperados
- Formatação incorreta de datas

#### Diagnóstico
```bash
# Executar comparação detalhada
curl http://localhost:5000/api/comparison/metrics

# Verificar logs de conversão
grep "conversion" backend/logs/app.log | tail -10

# Testar mapeamento específico
python -c "
from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter
adapter = LegacyServiceAdapter()
result = adapter.get_dashboard_metrics('test_123')
print(f'Raw data: {result}')
"
```

#### Soluções
1. **Verificar mapeamento de campos**:
   ```python
   # Validar schemas em schemas/dashboard.py
   from schemas.dashboard import DashboardMetrics
   
   # Testar conversão
   raw_data = {...}  # dados do GLPI
   converted = DashboardMetrics(**raw_data)
   ```

2. **Corrigir timezone**:
   ```bash
   export TZ=America/Sao_Paulo
   export LEGACY_ADAPTER_TIMEZONE=America/Sao_Paulo
   ```

3. **Atualizar schemas Pydantic**:
   - Adicionar validadores customizados
   - Implementar conversores de tipo
   - Tratar valores nulos adequadamente

### 5. Memory Leak

#### Sintomas
- Uso crescente de memória
- OOM kills
- Performance degradando ao longo do tempo

#### Diagnóstico
```bash
# Monitorar uso de memória
ps aux | grep python | grep flask

# Verificar objetos Python em memória
python -c "
import gc
print(f'Objects in memory: {len(gc.get_objects())}')
"

# Analisar heap dump (se disponível)
python -m memory_profiler app.py
```

#### Soluções
1. **Implementar cleanup de conexões**:
   ```python
   # Em legacy_service_adapter.py
   def __del__(self):
       if hasattr(self, 'session'):
           self.session.close()
   ```

2. **Configurar garbage collection**:
   ```python
   import gc
   gc.set_threshold(700, 10, 10)
   ```

3. **Limitar cache size**:
   ```bash
   export CACHE_MAX_SIZE=1000
   export CACHE_CLEANUP_INTERVAL=3600
   ```

## Comandos de Diagnóstico Avançado

### Análise de Performance
```bash
# Profile de CPU
python -m cProfile -o profile.stats app.py

# Análise de I/O
strace -p $(pgrep -f "flask run") -e trace=network

# Monitoramento de threads
ps -eLf | grep python
```

### Debugging de Rede
```bash
# Capturar tráfego HTTP
tcpdump -i any -A -s 0 'port 80 or port 443'

# Analisar latência de rede
ping -c 10 seu-glpi.com
traceroute seu-glpi.com
```

### Análise de Logs
```bash
# Extrair métricas de performance dos logs
awk '/legacy_adapter/ && /response_time/ {print $0}' backend/logs/app.log | \
  grep -o 'response_time:[0-9.]*' | \
  cut -d: -f2 | \
  sort -n | \
  awk '{sum+=$1; count++} END {print "Avg:", sum/count, "Count:", count}'

# Contar erros por tipo
grep "ERROR" backend/logs/app.log | \
  grep "legacy_adapter" | \
  awk '{print $NF}' | \
  sort | uniq -c | sort -nr
```

## Scripts de Automação

### Health Check Automatizado
```bash
#!/bin/bash
# health_check.sh

HEALTH_URL="http://localhost:5000/api/monitoring/legacy/health"
ALERT_EMAIL="admin@empresa.com"

response=$(curl -s -w "%{http_code}" $HEALTH_URL)
http_code=${response: -3}
body=${response%???}

if [ "$http_code" != "200" ]; then
    echo "CRITICAL: Health check failed - HTTP $http_code" | \
        mail -s "GLPI Dashboard CRITICAL" $ALERT_EMAIL
    exit 1
fi

status=$(echo $body | jq -r '.status')
if [ "$status" != "healthy" ]; then
    echo "WARNING: Service unhealthy - $status" | \
        mail -s "GLPI Dashboard WARNING" $ALERT_EMAIL
    exit 1
fi

echo "OK: Service healthy"
```

### Performance Monitor
```bash
#!/bin/bash
# performance_monitor.sh

METRICS_URL="http://localhost:5000/api/monitoring/legacy/metrics"
THRESHOLD_MS=2000

metrics=$(curl -s $METRICS_URL)
avg_time=$(echo $metrics | jq -r '.metrics | to_entries[] | .value.avg_response_time' | \
           awk '{sum+=$1; count++} END {print sum/count}')

if (( $(echo "$avg_time > $THRESHOLD_MS" | bc -l) )); then
    echo "ALERT: Average response time ${avg_time}ms exceeds threshold ${THRESHOLD_MS}ms" | \
        mail -s "GLPI Dashboard Performance Alert" admin@empresa.com
fi
```

### Log Rotation
```bash
#!/bin/bash
# rotate_logs.sh

LOG_DIR="backend/logs"
MAX_SIZE="100M"
MAX_FILES=10

find $LOG_DIR -name "*.log" -size +$MAX_SIZE -exec gzip {} \;
find $LOG_DIR -name "*.log.gz" | sort -r | tail -n +$((MAX_FILES+1)) | xargs rm -f
```

## Rollback Procedures

### Rollback Completo
```bash
#!/bin/bash
# rollback_legacy.sh

echo "Iniciando rollback dos serviços legacy..."

# 1. Desabilitar serviços legacy
export USE_LEGACY_SERVICES=false
echo "✓ Serviços legacy desabilitados"

# 2. Ativar dados mock (emergência)
export USE_MOCK_DATA=true
echo "✓ Dados mock ativados"

# 3. Reiniciar aplicação
sudo systemctl restart glpi-dashboard
echo "✓ Aplicação reiniciada"

# 4. Verificar status
sleep 10
status=$(curl -s http://localhost:5000/api/health | jq -r '.status')
if [ "$status" = "healthy" ]; then
    echo "✓ Rollback concluído com sucesso"
else
    echo "✗ Falha no rollback - verificar logs"
    exit 1
fi
```

### Rollback Parcial
```bash
# Desabilitar apenas endpoints específicos
export LEGACY_ENDPOINTS_DISABLED="metrics,tickets"

# Manter cache por mais tempo durante problemas
export CACHE_TTL=3600

# Reduzir timeout para falhar mais rápido
export LEGACY_ADAPTER_TIMEOUT=5
```

## Monitoramento Proativo

### Alertas Críticos
- Response time P95 > 500ms
- Error rate > 2%
- Memory usage > 80%
- Disk space < 10%
- GLPI connectivity failures

### Métricas de Negócio
- Tickets processados por minuto
- Taxa de conversão de dados
- Disponibilidade do serviço
- Satisfação do usuário (SLA)

### Dashboard Recomendado
```json
{
  "panels": [
    {
      "title": "Response Time",
      "type": "graph",
      "targets": ["legacy_adapter_response_time"]
    },
    {
      "title": "Error Rate",
      "type": "singlestat",
      "targets": ["legacy_adapter_error_rate"]
    },
    {
      "title": "Cache Hit Rate",
      "type": "gauge",
      "targets": ["cache_hit_rate"]
    }
  ]
}
```

## Contatos de Emergência

- **Equipe de Desenvolvimento**: dev-team@empresa.com
- **Administrador GLPI**: glpi-admin@empresa.com
- **Infraestrutura**: infra@empresa.com
- **Plantão 24x7**: +55 11 9999-9999

## Referências

- [Documentação GLPI API](https://glpi-developer-documentation.readthedocs.io/)
- [Flask Performance Tuning](https://flask.palletsprojects.com/en/2.0.x/deploying/)
- [Python Memory Profiling](https://docs.python.org/3/library/tracemalloc.html)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/configure.html)