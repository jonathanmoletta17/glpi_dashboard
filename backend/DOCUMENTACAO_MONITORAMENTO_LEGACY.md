# Sistema de Monitoramento Legacy - Documentação Completa

## Visão Geral

O sistema de monitoramento legacy foi implementado para fornecer observabilidade completa dos serviços legacy durante o processo de migração arquitetural. O sistema coleta métricas em tempo real, analisa a saúde dos serviços e fornece endpoints HTTP para monitoramento.

## Arquitetura

### Componentes Principais

1. **LegacyServiceMonitor** (`utils/legacy_monitoring.py`)
   - Monitor central que coleta e armazena métricas
   - Thread-safe para ambiente multi-threaded
   - Análise automática de saúde dos serviços

2. **Decorators de Monitoramento**
   - `@legacy_monitor.monitor_method(nome_metodo)`
   - Instrumentação transparente de métodos
   - Coleta automática de métricas de performance

3. **Endpoints HTTP** (`api/routes.py`)
   - `/api/monitoring/legacy/metrics` - Métricas detalhadas
   - `/api/monitoring/legacy/health` - Status de saúde
   - `/api/monitoring/legacy/reset` - Reset das métricas

## Métricas Coletadas

### Por Método Monitorado

- **call_count**: Número total de chamadas
- **error_count**: Número de erros ocorridos
- **error_rate_percent**: Taxa de erro em percentual
- **total_time**: Tempo total acumulado
- **avg_response_time**: Tempo médio de resposta
- **min_response_time**: Menor tempo de resposta
- **max_response_time**: Maior tempo de resposta
- **p95_response_time**: Percentil 95 dos tempos de resposta
- **last_call**: Timestamp da última chamada
- **recent_errors**: Lista dos últimos 5 erros com detalhes

### Histórico Mantido

- **response_times**: Últimas 100 medições de tempo
- **errors**: Últimos 50 erros com timestamp e detalhes

## Análise de Saúde

### Status Possíveis

- **healthy**: Todos os serviços funcionando normalmente
- **degraded**: Alguns problemas identificados
- **unhealthy**: Problemas críticos detectados

### Critérios de Avaliação

1. **Taxa de Erro**
   - > 5%: Marca como degraded
   - Adiciona issue específica

2. **Tempo de Resposta**
   - P95 > 1.0s: Marca como degraded
   - Indica lentidão no serviço

3. **Atividade Recente**
   - Sem chamadas recentes: Warning
   - Pode indicar problemas de conectividade

## Integração Implementada

### APIService (`services/legacy/api_service.py`)

Métodos monitorados:
- `get_metrics` → `api_service_get_metrics`
- `get_system_status` → `api_service_get_system_status`
- `get_dashboard_metrics` → `api_service_get_dashboard_metrics`

### LegacyServiceAdapter (`services/legacy/legacy_service_adapter.py`)

Métodos monitorados:
- `get_dashboard_metrics` → `legacy_adapter_get_dashboard_metrics`
- `get_dashboard_metrics_with_date_filter` → `legacy_adapter_get_dashboard_metrics_with_date_filter`
- `get_dashboard_metrics_with_modification_date_filter` → `legacy_adapter_get_dashboard_metrics_with_modification_date_filter`
- `get_dashboard_metrics_with_filters` → `legacy_adapter_get_dashboard_metrics_with_filters`
- `get_technician_ranking` → `legacy_adapter_get_technician_ranking`
- `get_new_tickets` → `legacy_adapter_get_new_tickets`
- `get_system_status` → `legacy_adapter_get_system_status`

## Endpoints HTTP

### GET /api/monitoring/legacy/metrics

**Descrição**: Retorna métricas detalhadas de todos os métodos monitorados

**Resposta de Sucesso (200)**:
```json
{
  "status": "success",
  "data": {
    "nome_do_metodo": {
      "call_count": 150,
      "error_count": 2,
      "error_rate_percent": 1.33,
      "avg_response_time": 0.245,
      "min_response_time": 0.120,
      "max_response_time": 0.890,
      "p95_response_time": 0.650,
      "last_call": "2024-09-14T10:30:45.123456",
      "recent_errors": [
        {
          "timestamp": "2024-09-14T10:25:30.123456",
          "error": "Connection timeout",
          "response_time": 5.0
        }
      ]
    }
  },
  "timestamp": "2024-09-14T10:30:45.123456",
  "total_methods": 8
}
```

### GET /api/monitoring/legacy/health

**Descrição**: Retorna status de saúde dos serviços legacy

**Códigos de Status**:
- 200: Healthy
- 206: Degraded (Partial Content)
- 503: Unhealthy (Service Unavailable)

**Resposta**:
```json
{
  "status": "success",
  "data": {
    "overall_health": "degraded",
    "issues": [
      "api_service_get_metrics: alta taxa de erro (6.5%)",
      "legacy_adapter_get_dashboard_metrics: tempo de resposta alto (P95: 1.2s)"
    ],
    "healthy_methods": 6,
    "total_methods": 8
  },
  "timestamp": "2024-09-14T10:30:45.123456"
}
```

### POST /api/monitoring/legacy/reset

**Descrição**: Reset todas as métricas coletadas

**Resposta de Sucesso (200)**:
```json
{
  "status": "success",
  "message": "Métricas legacy resetadas com sucesso",
  "timestamp": "2024-09-14T10:30:45.123456"
}
```

## Como Usar

### 1. Instrumentar Novos Métodos

```python
from utils.legacy_monitoring import legacy_monitor

class MeuServico:
    @legacy_monitor.monitor_method("meu_servico_metodo_importante")
    def metodo_importante(self):
        # Lógica do método
        return resultado
```

### 2. Acessar Métricas Programaticamente

```python
from utils.legacy_monitoring import legacy_monitor

# Obter resumo das métricas
metricas = legacy_monitor.get_metrics_summary()

# Verificar saúde dos serviços
saude = legacy_monitor.get_health_status()

print(f"Status geral: {saude['overall_health']}")
for issue in saude.get('issues', []):
    print(f"Problema: {issue}")
```

### 3. Monitoramento via HTTP

```bash
# Verificar métricas
curl http://localhost:5000/api/monitoring/legacy/metrics

# Verificar saúde
curl http://localhost:5000/api/monitoring/legacy/health

# Resetar métricas
curl -X POST http://localhost:5000/api/monitoring/legacy/reset
```

## Teste e Validação

### Script de Teste

O arquivo `test_legacy_monitoring.py` fornece testes completos:

```bash
# Executar testes
python test_legacy_monitoring.py
```

### Testes Incluídos

1. **Teste de Endpoints**: Valida todos os endpoints HTTP
2. **Teste de Integração**: Testa o monitor diretamente
3. **Geração de Métricas**: Simula chamadas para coletar dados
4. **Validação de Reset**: Confirma limpeza das métricas

## Configuração e Personalização

### Thresholds de Saúde

Pode ser customizado editando `legacy_monitoring.py`:

```python
# Critérios atuais
if metrics['error_rate_percent'] > 5:  # Taxa de erro
    overall_health = "degraded"
    
if metrics['p95_response_time'] > 1.0:  # Tempo de resposta
    overall_health = "degraded"
```

### Tamanho do Histórico

```python
# Configuração atual
'response_times': deque(maxlen=100),  # Últimas 100 chamadas
'errors': deque(maxlen=50)            # Últimos 50 erros
```

## Logging

O sistema utiliza o logger `legacy_monitor` para registrar eventos:

```python
import logging
logging.getLogger('legacy_monitor').setLevel(logging.INFO)
```

## Considerações de Performance

- **Thread-Safe**: Utiliza locks para acesso concorrente
- **Memória Limitada**: Histórico limitado para evitar vazamentos
- **Overhead Mínimo**: Decorators com impacto mínimo na performance
- **Coleta Assíncrona**: Métricas coletadas sem bloquear execução

## Próximos Passos

1. **Alertas**: Implementar notificações automáticas
2. **Dashboards**: Integrar com ferramentas de visualização
3. **Exportação**: Suporte para Prometheus/Grafana
4. **Histórico Persistente**: Armazenar métricas em banco de dados
5. **Análise Preditiva**: Detectar tendências e padrões

## Troubleshooting

### Problemas Comuns

1. **Métricas não aparecem**
   - Verificar se os decorators foram aplicados
   - Confirmar que os métodos estão sendo chamados

2. **Erro de importação**
   - Verificar se o arquivo `legacy_monitoring.py` existe
   - Confirmar estrutura de diretórios

3. **Endpoints não respondem**
   - Verificar se o servidor Flask está rodando
   - Confirmar que as rotas foram registradas

### Debug

```python
# Verificar métricas diretamente
from utils.legacy_monitoring import legacy_monitor
print(legacy_monitor.metrics)
```

---

**Implementado em**: 14/09/2024  
**Versão**: 1.0  
**Status**: Produção