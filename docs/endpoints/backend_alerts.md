# Endpoint: /alerts

## Arquivo(s) de origem
- `backend/api/routes.py` (linha ~1000-1100)

## Método HTTP
`GET`

## Descrição técnica
Endpoint que retorna alertas dinâmicos do sistema baseados em métricas de performance, status de serviços e thresholds configuráveis. Usado para notificações proativas no dashboard.

## Parâmetros de entrada

| Nome | Tipo | Obrigatório | Exemplo | Descrição |
|------|------|-------------|---------|----------|
| `severity` | string | Não | `high` | Filtrar por severidade: `low`, `medium`, `high`, `critical` |
| `category` | string | Não | `performance` | Filtrar por categoria: `performance`, `connectivity`, `system` |
| `limit` | integer | Não | `10` | Número máximo de alertas (padrão: 20) |
| `include_resolved` | boolean | Não | `false` | Incluir alertas já resolvidos |

## Resposta esperada (contract)
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "id": "alert_001",
        "title": "Alto tempo de resposta GLPI",
        "description": "API GLPI respondendo em 5.2s (threshold: 3s)",
        "severity": "high",
        "category": "performance",
        "status": "active",
        "created_at": "2025-01-27T10:25:00Z",
        "updated_at": "2025-01-27T10:30:00Z",
        "threshold_value": 3000,
        "current_value": 5200,
        "unit": "ms",
        "source": "glpi_monitor",
        "actions": [
          {
            "type": "check_glpi_status",
            "label": "Verificar Status GLPI",
            "url": "/health/glpi"
          }
        ]
      },
      {
        "id": "alert_002",
        "title": "Muitos tickets pendentes N1",
        "description": "45 tickets pendentes no N1 (threshold: 30)",
        "severity": "medium",
        "category": "workload",
        "status": "active",
        "created_at": "2025-01-27T09:15:00Z",
        "updated_at": "2025-01-27T10:30:00Z",
        "threshold_value": 30,
        "current_value": 45,
        "unit": "tickets",
        "source": "metrics_analyzer",
        "affected_technicians": ["João Silva", "Maria Santos"],
        "actions": [
          {
            "type": "view_pending_tickets",
            "label": "Ver Tickets Pendentes",
            "url": "/tickets?status=pending&level=N1"
          }
        ]
      },
      {
        "id": "alert_003",
        "title": "Cache Redis indisponível",
        "description": "Conexão com Redis falhou - usando fallback",
        "severity": "critical",
        "category": "connectivity",
        "status": "resolved",
        "created_at": "2025-01-27T08:45:00Z",
        "updated_at": "2025-01-27T09:30:00Z",
        "resolved_at": "2025-01-27T09:30:00Z",
        "source": "cache_monitor",
        "resolution": "Conexão restaurada automaticamente"
      }
    ],
    "summary": {
      "total_alerts": 15,
      "active_alerts": 12,
      "critical_count": 1,
      "high_count": 3,
      "medium_count": 6,
      "low_count": 2,
      "resolved_today": 8
    },
    "data_source": "system_monitor",
    "is_mock_data": false,
    "last_check": "2025-01-27T10:30:00Z"
  },
  "cached": false,
  "response_time_ms": 67.3,
  "correlation_id": "alerts_123456789"
}
```

## Tipagem equivalente em TypeScript
```typescript
type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
type AlertCategory = 'performance' | 'connectivity' | 'system' | 'workload' | 'security';
type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'suppressed';

interface AlertAction {
  type: string;
  label: string;
  url: string;
}

interface SystemAlert {
  id: string;
  title: string;
  description: string;
  severity: AlertSeverity;
  category: AlertCategory;
  status: AlertStatus;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  
  // Métricas (opcionais)
  threshold_value?: number;
  current_value?: number;
  unit?: string;
  
  // Contexto
  source: string;
  affected_technicians?: string[];
  actions?: AlertAction[];
  resolution?: string;
  
  // Metadados
  tags?: string[];
  priority?: number;
}

interface AlertsSummary {
  total_alerts: number;
  active_alerts: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  resolved_today: number;
}

interface AlertsData {
  alerts: SystemAlert[];
  summary: AlertsSummary;
  
  // Campos de identificação de fonte
  data_source: 'system_monitor' | 'mock' | 'unknown';
  is_mock_data: boolean;
  last_check: string;
}

interface AlertsResponse {
  success: boolean;
  data: AlertsData;
  cached: boolean;
  response_time_ms: number;
  correlation_id: string;
}
```

## Dependências

### Backend
- `AlertManager` - Gerenciamento de alertas
- `PerformanceMonitor` - Monitoramento de métricas
- `GLPIServiceFacade` - Status de conectividade GLPI
- `unified_cache` - Status do cache Redis
- `ThresholdManager` - Configuração de thresholds
- `ResponseFormatter` - Formatação de respostas

### Frontend
- **Não consumido atualmente** pelos hooks principais
- **Uso potencial**: Componente de notificações, header alerts
- **Componente sugerido**: AlertsPanel, NotificationBell

### Variáveis de ambiente
- `ALERT_THRESHOLDS_CONFIG` - Configuração de thresholds
- `ALERT_RETENTION_DAYS` - Dias para manter alertas resolvidos
- `NOTIFICATION_ENABLED` - Habilitar notificações

## Análise técnica

### Consistência
✅ **Bem estruturado**: Alertas organizados com metadados completos
✅ **Campos de fonte**: Implementação correta de `data_source` e `is_mock_data`
✅ **Ações contextuais**: Links para resolução de problemas
✅ **Severidade clara**: Níveis bem definidos

### Possíveis problemas
- ⚠️ **Não consumido**: Frontend não utiliza este endpoint
- ⚠️ **Sem cache**: Alertas são calculados a cada chamada
- ⚠️ **Ruído**: Pode gerar muitos alertas falso-positivos
- ⚠️ **Sem persistência**: Alertas não são persistidos em banco

### Sugestões de melhorias
1. **Frontend integration**: Criar hook `useAlerts` e componente de notificações
2. **Persistência**: Salvar alertas em banco de dados
3. **Notificações push**: WebSocket/SSE para alertas em tempo real
4. **Configuração dinâmica**: Interface para configurar thresholds
5. **Escalação**: Sistema de escalação automática
6. **Integração externa**: Slack, email, SMS
7. **Machine Learning**: Detecção de anomalias inteligente
8. **Dashboard de alertas**: Página dedicada para gerenciar alertas

## Tipos de alertas implementados

### Performance
- Tempo de resposta GLPI alto
- Tempo de resposta da API alto
- Uso de CPU/memória alto

### Connectivity
- GLPI indisponível
- Redis indisponível
- Timeout de conexões

### Workload
- Muitos tickets pendentes
- SLA em risco
- Distribuição desigual de tickets

### System
- Erros de aplicação
- Falhas de cache
- Problemas de configuração

## Configuração de thresholds
```json
{
  "glpi_response_time_ms": 3000,
  "api_response_time_ms": 1000,
  "pending_tickets_n1": 30,
  "pending_tickets_n2": 20,
  "sla_risk_hours": 2,
  "memory_usage_percent": 80,
  "cpu_usage_percent": 85
}
```

## Status de implementação
✅ **Implementado** - Funcional no backend
✅ **Bem estruturado** - Alertas organizados e informativos
✅ **Thresholds configuráveis** - Sistema flexível de limites
✅ **Ações contextuais** - Links para resolução
❌ **Não consumido** - Frontend não utiliza este endpoint
❌ **Sem persistência** - Alertas não são salvos
❌ **Sem notificações** - Não há sistema de notificação ativa
⚠️ **Potencial subutilizado** - Sistema de alertas valioso não exposto