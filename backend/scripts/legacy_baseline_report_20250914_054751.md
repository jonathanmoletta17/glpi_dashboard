# Relatório de Baseline - Serviços Legacy GLPI

## 📋 Resumo Executivo

**Data de Execução:** 2025-09-14T05:47:34.856723
**Duração Total:** 0.28 minutos
**Saúde Geral:** EXCELLENT
**Nota de Performance:** A

### 🎯 Métricas Principais

- **Facade Success Rate:** 100.0
- **Avg Response Time Ms:** 441.146
- **P95 Response Time Ms:** 3429.132
- **Concurrent Success Rate:** 100.0

## 🧪 Resultados dos Testes

### 1. Teste Isolado do GLPIServiceFacade

**Taxa de Sucesso:** 100.0%
**Operações Totais:** 5
**Tempo Total:** 2.213s

#### Breakdown por Método:

| Método | Tempo Médio (ms) | Status |
|--------|------------------|--------|
| get_dashboard_metrics | 2049.548 | ✅ 100.0% |
| get_ticket_count | 77.465 | ✅ 100.0% |
| get_metrics_by_level | 0.0 | ✅ 100.0% |
| get_general_metrics | 78.715 | ✅ 100.0% |
| health_check | 0.0 | ✅ 100.0% |

### 3. Teste de Stress (100 Requisições Simultâneas)

**Requisições Bem-sucedidas:** 100/100
**Taxa de Sucesso:** 100.0%
**Uso de CPU:** +13.0%
**Uso de Memória:** +1.64 MB


## 💡 Recomendações

1. Implementar métricas de observabilidade (Prometheus/Grafana)
2. Adicionar alertas para degradação de performance
3. Estabelecer SLAs baseados nos resultados do baseline
4. Executar testes de baseline regularmente para detectar regressões

## 🖥️ Informações do Sistema

- **CPUs:** 20
- **Memória Total:** 63.66 GB
- **Plataforma:** win32
- **Python:** 3.12.1 (tags/v3.12.1:2305ca5, Dec  7 2023, 22:03:25) [MSC v.1937 64 bit (AMD64)]

---

*Relatório gerado automaticamente pelo Legacy Performance Baseline Tool*
