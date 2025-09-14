# Guia de Migração: Serviços Legacy para Clean Architecture

## Visão Geral

Este documento descreve a implementação da migração dos serviços legacy robustos para a Clean Architecture, mantendo 100% dos dados reais do GLPI.

## Arquitetura Implementada

```
API Routes → MetricsFacade → LegacyServiceAdapter → GLPIServiceFacade → Serviços Legacy → GLPI API
```

### Componentes Principais

#### 1. LegacyServiceAdapter
- **Localização**: `backend/core/infrastructure/adapters/legacy_service_adapter.py`
- **Função**: Bridge entre Clean Architecture e serviços legacy
- **Responsabilidades**:
  - Conversão de dados entre formatos
  - Implementação do contrato UnifiedGLPIServiceContract
  - Tratamento de erros e logging
  - Monitoramento de performance

#### 2. MetricsFacade Modificado
- **Localização**: `backend/core/application/services/metrics_facade.py`
- **Modificações**:
  - Suporte a múltiplos adapters
  - Configuração via feature flags
  - Logging detalhado de adapter utilizado

#### 3. Sistema de Monitoramento
- **Localização**: `backend/utils/legacy_monitoring.py`
- **Funcionalidades**:
  - Métricas de performance em tempo real
  - Detecção de degradação de serviço
  - Alertas automáticos

## Configuração

### Variáveis de Ambiente

```bash
# Controle de Adapter
USE_LEGACY_SERVICES=true          # Usar serviços legacy (recomendado)
USE_MOCK_DATA=false               # Nunca usar dados mock em produção

# Performance
LEGACY_ADAPTER_TIMEOUT=30         # Timeout em segundos
LEGACY_ADAPTER_RETRY_COUNT=3      # Número de tentativas

# Monitoramento
ENABLE_ADAPTER_METRICS=true       # Habilitar métricas
ADAPTER_PERFORMANCE_LOG=true      # Log de performance
```

### Configurações Recomendadas por Ambiente

#### Desenvolvimento
```bash
USE_LEGACY_SERVICES=true
USE_MOCK_DATA=false
LEGACY_ADAPTER_TIMEOUT=10
ENABLE_ADAPTER_METRICS=true
ADAPTER_PERFORMANCE_LOG=true
```

#### Produção
```bash
USE_LEGACY_SERVICES=true
USE_MOCK_DATA=false
LEGACY_ADAPTER_TIMEOUT=30
LEGACY_ADAPTER_RETRY_COUNT=3
ENABLE_ADAPTER_METRICS=true
ADAPTER_PERFORMANCE_LOG=false
```

## Endpoints de Monitoramento

### Métricas dos Serviços Legacy
```http
GET /api/monitoring/legacy/metrics
```

Retorna:
```json
{
  "status": "success",
  "metrics": {
    "get_dashboard_metrics": {
      "call_count": 1250,
      "error_count": 12,
      "error_rate_percent": 0.96,
      "avg_response_time": 0.245,
      "p95_response_time": 0.380
    }
  }
}
```

### Status de Saúde
```http
GET /api/monitoring/legacy/health
```

Retorna:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-14T10:30:00Z",
  "issues": []
}
```

### Reset de Métricas
```http
POST /api/monitoring/legacy/reset
```

Retorna:
```json
{
  "status": "success",
  "message": "Métricas resetadas com sucesso",
  "timestamp": "2025-01-14T10:30:00Z"
}
```

### Comparação de Adapters
```http
GET /api/comparison/metrics
```

## Implementação Detalhada

### Sistema de Monitoramento Legacy

O sistema de monitoramento (`legacy_monitoring.py`) implementa:

#### Decorator de Monitoramento
```python
@legacy_monitor.monitor_method("method_name")
def my_method(self):
    # Método será automaticamente monitorado
    pass
```

#### Métricas Coletadas
- **call_count**: Número total de chamadas
- **error_count**: Número de erros
- **error_rate_percent**: Taxa de erro em percentual
- **avg_response_time**: Tempo médio de resposta
- **p95_response_time**: Percentil 95 do tempo de resposta
- **last_call_time**: Timestamp da última chamada
- **last_error_time**: Timestamp do último erro

#### Análise de Saúde
O sistema analisa automaticamente:
- Taxa de erro > 5%: Warning
- Taxa de erro > 10%: Critical
- Tempo de resposta médio > 2s: Warning
- Tempo de resposta médio > 5s: Critical

### Integração com Componentes

#### APIService
Todos os métodos principais estão instrumentados:
- `get_metrics`
- `get_system_status`
- `get_dashboard_metrics`

#### LegacyServiceAdapter
Todos os métodos do adapter estão monitorados:
- `get_dashboard_metrics`
- `get_dashboard_metrics_with_date_filter`
- `get_dashboard_metrics_with_modification_date_filter`
- `get_dashboard_metrics_with_filters`
- `get_technician_ranking`
- `get_new_tickets`
- `get_system_status`

## Troubleshooting

### Problemas Comuns

#### 1. Erro: "LegacyServiceAdapter não encontrado"

**Sintoma**: `ImportError: cannot import name 'LegacyServiceAdapter'`

**Causa**: Adapter não foi criado ou não está no PYTHONPATH

**Solução**:
```bash
# Verificar se arquivo existe
ls backend/core/infrastructure/adapters/legacy_service_adapter.py

# Verificar imports
python -c "from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter; print('OK')"
```

#### 2. Performance Degradada

**Sintoma**: Tempo de resposta > 1s

**Diagnóstico**:
```bash
# Verificar métricas
curl http://localhost:5000/api/monitoring/legacy/metrics

# Verificar logs
tail -f backend/logs/app.log | grep "legacy_adapter"
```

**Soluções**:
- Verificar conectividade com GLPI
- Aumentar timeout: `LEGACY_ADAPTER_TIMEOUT=60`
- Verificar cache do GLPI
- Analisar queries lentas

#### 3. Erro: "legacy_monitor não encontrado"

**Sintoma**: `ImportError: cannot import name 'legacy_monitor'`

**Causa**: Sistema de monitoramento não foi importado corretamente

**Solução**:
```bash
# Verificar se arquivo existe
ls backend/utils/legacy_monitoring.py

# Verificar import
python -c "from utils.legacy_monitoring import legacy_monitor; print('OK')"
```

#### 4. Métricas não aparecem

**Sintoma**: Endpoint `/api/monitoring/legacy/metrics` retorna métricas vazias

**Causa**: Métodos não foram chamados ou decorators não foram aplicados

**Solução**:
1. Verificar se os decorators estão aplicados nos métodos
2. Fazer algumas chamadas para os endpoints da API
3. Verificar logs para erros de instrumentação

#### 5. Status de saúde sempre "unhealthy"

**Sintoma**: Endpoint `/api/monitoring/legacy/health` sempre retorna status não saudável

**Diagnóstico**:
```bash
# Verificar métricas detalhadas
curl http://localhost:5000/api/monitoring/legacy/metrics

# Verificar se há muitos erros
grep -i error backend/logs/app.log | tail -20
```

**Soluções**:
- Verificar conectividade com GLPI
- Analisar logs de erro
- Verificar configurações de timeout
- Resetar métricas se necessário: `POST /api/monitoring/legacy/reset`

## Testes

### Teste Manual dos Endpoints

```bash
# Testar métricas
curl -X GET http://localhost:5000/api/monitoring/legacy/metrics

# Testar saúde
curl -X GET http://localhost:5000/api/monitoring/legacy/health

# Resetar métricas
curl -X POST http://localhost:5000/api/monitoring/legacy/reset
```

### Script de Teste Automatizado

Use o arquivo `test_legacy_monitoring.py` para testes automatizados:

```bash
cd backend
python test_legacy_monitoring.py
```

## Monitoramento em Produção

### Alertas Recomendados

1. **Taxa de Erro Alta**:
   - Condição: `error_rate_percent > 5`
   - Ação: Investigar logs e conectividade GLPI

2. **Performance Degradada**:
   - Condição: `avg_response_time > 2`
   - Ação: Verificar recursos do servidor e GLPI

3. **Serviço Indisponível**:
   - Condição: Status health != "healthy"
   - Ação: Verificar conectividade e reiniciar se necessário

### Logs Importantes

Monitorar os seguintes padrões nos logs:
- `legacy_adapter`: Operações do adapter
- `legacy_monitor`: Métricas e monitoramento
- `ERROR`: Erros gerais
- `WARNING`: Avisos de performance

## Próximos Passos

1. **Implementar Alertas Automáticos**:
   - Integração com sistemas de monitoramento (Prometheus, Grafana)
   - Notificações por email/Slack

2. **Otimizações de Performance**:
   - Cache de métricas
   - Compressão de dados
   - Pool de conexões

3. **Expansão do Monitoramento**:
   - Métricas de negócio
   - Monitoramento de recursos do sistema
   - Análise de tendências

4. **Documentação Adicional**:
   - Runbooks operacionais
   - Guias de troubleshooting específicos
   - Documentação de APIs

## Referências

- [Documentação do Sistema de Monitoramento](DOCUMENTACAO_MONITORAMENTO_LEGACY.md)
- [Relatório de Testes de Performance](RELATORIO_TESTES_PERFORMANCE.md)
- [Configuração GLPI](CONFIGURACAO_GLPI.md)
- [Troubleshooting Geral](TROUBLESHOOTING.md)