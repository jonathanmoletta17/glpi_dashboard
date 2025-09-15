# Endpoint: /technician-performance

## Arquivo(s) de origem
- `backend/api/routes.py` (linha ~850-950)

## Método HTTP
`GET`

## Descrição técnica
Endpoint que retorna métricas detalhadas de performance de técnicos individuais, incluindo estatísticas de resolução, tempo médio, satisfação e comparações com médias do time.

## Parâmetros de entrada

| Nome | Tipo | Obrigatório | Exemplo | Descrição |
|------|------|-------------|---------|----------|
| `technician_id` | integer | Sim | `123` | ID do técnico no GLPI |
| `start_date` | string | Não | `2025-01-01` | Data inicial para análise (formato YYYY-MM-DD) |
| `end_date` | string | Não | `2025-01-31` | Data final para análise (formato YYYY-MM-DD) |
| `include_comparison` | boolean | Não | `true` | Incluir comparação com média do time |

## Resposta esperada (contract)
```json
{
  "success": true,
  "data": {
    "technician": {
      "id": 123,
      "name": "João Silva",
      "level": "N1",
      "department": "Suporte Técnico",
      "active_since": "2024-03-15T00:00:00Z"
    },
    "period": {
      "start_date": "2025-01-01T00:00:00Z",
      "end_date": "2025-01-31T23:59:59Z",
      "days_analyzed": 31
    },
    "metrics": {
      "tickets_resolved": 45,
      "tickets_assigned": 52,
      "resolution_rate": 86.5,
      "avg_resolution_time_hours": 4.2,
      "first_response_time_hours": 0.8,
      "customer_satisfaction": 4.3,
      "sla_compliance_rate": 92.1
    },
    "comparison": {
      "team_avg_resolution_time": 5.1,
      "team_avg_satisfaction": 4.1,
      "team_avg_sla_compliance": 88.5,
      "performance_score": 87.5,
      "rank_in_team": 3,
      "total_team_members": 12
    },
    "trends": {
      "resolution_time_trend": "-12%",
      "satisfaction_trend": "+5%",
      "tickets_trend": "+8%"
    },
    "categories": [
      {
        "name": "Hardware",
        "tickets_count": 28,
        "avg_resolution_time": 3.8,
        "satisfaction": 4.5
      },
      {
        "name": "Software",
        "tickets_count": 17,
        "avg_resolution_time": 5.1,
        "satisfaction": 4.0
      }
    ],
    "data_source": "glpi",
    "is_mock_data": false,
    "last_updated": "2025-01-27T10:30:00Z"
  },
  "cached": true,
  "response_time_ms": 234.7,
  "correlation_id": "perf_123456789"
}
```

## Resposta em caso de técnico não encontrado
```json
{
  "success": false,
  "error": {
    "code": "TECHNICIAN_NOT_FOUND",
    "message": "Técnico com ID 999 não encontrado",
    "details": "Verifique se o ID do técnico está correto e se ele está ativo no sistema"
  },
  "correlation_id": "perf_error_123"
}
```

## Tipagem equivalente em TypeScript
```typescript
interface TechnicianInfo {
  id: number;
  name: string;
  level: 'N1' | 'N2' | 'N3' | 'N4';
  department: string;
  active_since: string;
}

interface AnalysisPeriod {
  start_date: string;
  end_date: string;
  days_analyzed: number;
}

interface PerformanceMetrics {
  tickets_resolved: number;
  tickets_assigned: number;
  resolution_rate: number;
  avg_resolution_time_hours: number;
  first_response_time_hours: number;
  customer_satisfaction: number;
  sla_compliance_rate: number;
}

interface TeamComparison {
  team_avg_resolution_time: number;
  team_avg_satisfaction: number;
  team_avg_sla_compliance: number;
  performance_score: number;
  rank_in_team: number;
  total_team_members: number;
}

interface PerformanceTrends {
  resolution_time_trend: string;
  satisfaction_trend: string;
  tickets_trend: string;
}

interface CategoryPerformance {
  name: string;
  tickets_count: number;
  avg_resolution_time: number;
  satisfaction: number;
}

interface TechnicianPerformanceData {
  technician: TechnicianInfo;
  period: AnalysisPeriod;
  metrics: PerformanceMetrics;
  comparison: TeamComparison;
  trends: PerformanceTrends;
  categories: CategoryPerformance[];
  
  // Campos de identificação de fonte
  data_source: 'glpi' | 'mock' | 'unknown';
  is_mock_data: boolean;
  last_updated: string;
}

interface TechnicianPerformanceResponse {
  success: boolean;
  data: TechnicianPerformanceData;
  cached: boolean;
  response_time_ms: number;
  correlation_id: string;
}
```

## Dependências

### Backend
- `GLPIServiceFacade` - Dados de tickets e técnicos
- `TechnicianPerformanceService` - Cálculos de métricas
- `StatisticsCalculator` - Cálculos estatísticos
- `unified_cache` - Cache de performance (TTL: 1800s)
- `ResponseFormatter` - Formatação de respostas
- `safe_int_param`, `safe_date_string` - Validação de parâmetros

### Frontend
- **Não consumido atualmente** pelos hooks principais
- **Uso potencial**: Páginas de detalhes de técnicos
- **Componente sugerido**: TechnicianDetailPage, PerformanceChart

### Variáveis de ambiente
- `GLPI_URL` - URL da API GLPI
- `GLPI_USER_TOKEN` - Token de usuário GLPI
- `GLPI_APP_TOKEN` - Token da aplicação GLPI
- `PERFORMANCE_CACHE_TTL` - TTL do cache (padrão: 1800s)

## Análise técnica

### Consistência
✅ **Boa estrutura**: Endpoint bem organizado e informativo
✅ **Campos de fonte**: Implementação correta de `data_source` e `is_mock_data`
✅ **Validação robusta**: Validação de parâmetros implementada
✅ **Cache otimizado**: Cache longo (30min) para dados que mudam pouco

### Possíveis problemas
- ⚠️ **Complexidade de cálculo**: Métricas podem ser custosas de calcular
- ⚠️ **Não consumido**: Frontend não utiliza este endpoint
- ⚠️ **Dados sensíveis**: Informações de performance podem ser sensíveis
- ⚠️ **Sem paginação**: Categorias podem ser muitas

### Sugestões de melhorias
1. **Frontend integration**: Criar hook `useTechnicianPerformance`
2. **Componente de detalhes**: Página de detalhes do técnico
3. **Gráficos**: Visualizações de tendências e comparações
4. **Filtros avançados**: Filtrar por categoria, período customizado
5. **Exportação**: Permitir exportar relatórios em PDF/Excel
6. **Alertas**: Alertas para performance abaixo da média
7. **Benchmarking**: Comparação com períodos anteriores
8. **Gamificação**: Sistema de badges/conquistas

## Casos de uso
1. **Avaliação de performance**: Gestores avaliando técnicos
2. **Identificação de treinamento**: Áreas que precisam de melhoria
3. **Reconhecimento**: Identificar top performers
4. **Planejamento**: Distribuição de carga de trabalho
5. **Relatórios gerenciais**: Dashboards executivos

## Métricas calculadas

### Resolution Rate
```
resolution_rate = (tickets_resolved / tickets_assigned) * 100
```

### Performance Score
```
performance_score = weighted_average(
  resolution_rate * 0.3,
  sla_compliance_rate * 0.3,
  customer_satisfaction * 20 * 0.25,  // normalizado para 0-100
  (1 / avg_resolution_time_hours) * 10 * 0.15  // inverso do tempo
)
```

## Status de implementação
✅ **Implementado** - Funcional no backend
✅ **Bem estruturado** - Métricas completas e organizadas
✅ **Cached** - Sistema de cache otimizado
✅ **Validado** - Parâmetros validados corretamente
❌ **Não consumido** - Frontend não utiliza este endpoint
❌ **Sem tipagem frontend** - Interfaces TypeScript não criadas
⚠️ **Potencial subutilizado** - Dados valiosos não expostos ao usuário