# Plano de Ação: Endpoint /alerts

## Insights extraídos
- O endpoint fornece alertas detalhados com filtros por severidade, categoria, limite e possibilidade de incluir resolvidos.【F:docs/endpoints/backend_alerts.md†L14-L99】
- A resposta contém lista de alertas, resumo agregado e metadados de fonte/cached para uso em dashboards.【F:docs/endpoints/backend_alerts.md†L21-L169】
- Atualmente o frontend não consome essa rota, apesar de sugerir componentes como `AlertsPanel` ou `NotificationBell`.【F:docs/endpoints/backend_alerts.md†L181-L199】

## Lacunas identificadas
- Falta serviço/hook no frontend para buscar e exibir alertas com filtragem dinâmica.【F:docs/endpoints/backend_alerts.md†L181-L199】
- Não existem variáveis de ambiente documentadas no frontend para controlar exibição de alertas (ex.: `VITE_ENABLE_ALERTS`).
- Ausência de testes garantindo ordenação por severidade e tratamento de alertas resolvidos.

## Próximas ações prioritárias
1. **Implementar consumo no frontend**  
   - Adicionar `getAlerts(filters)` em `apiService` retornando `AlertsResponse`, bem como hook `useAlerts` com suporte a filtros reativos e polling configurável.【F:docs/endpoints/backend_alerts.md†L14-L169】
   - Criar componentes UI (badge no header, painel detalhado) aproveitando campos `summary` e `actions`.
2. **Configurar feature flags e UX**  
   - Incluir `VITE_ENABLE_ALERTS` e `VITE_ALERT_POLL_INTERVAL` em `.env.example`, permitindo desligar alertas em ambientes que não suportam o monitoramento.【F:docs/endpoints/backend_alerts.md†L186-L189】
   - Documentar thresholds e categorias disponíveis no README.
3. **Cobrir com testes**  
   - Backend: teste pytest verificando filtros (`severity`, `category`, `include_resolved`) e ordenação por criticidade.【F:docs/endpoints/backend_alerts.md†L14-L69】
   - Frontend: teste de hook e componente garantindo diferenciação visual por severidade e presença de ações contextuais.

## Prompt sugerido para execução
> **Identidade**: Agente `DashboardDesigner` com foco em alertas proativos.
> **Objetivo**: Expor alertas dinâmicos no frontend com filtros configuráveis e controles de exibição.
> **Contexto**: Atualizar `frontend/services/api.ts`, criar `useAlerts` e componentes visuais; ajustar `.env.example` e documentação. Validar backend com testes de filtro/ordenção.
> **Passos**: (1) Implementar serviço/hook e tipos TS, (2) criar UI para alertas, (3) adicionar feature flag + docs, (4) escrever testes (pytest + React Testing Library).

## Validações recomendadas
- `pytest backend/tests/unit/test_alerts.py` cobrindo filtros e resumo agregado.
- `npm run test -- useAlerts` garantindo parsing adequado.
- Teste manual `curl "http://localhost:5000/api/alerts?severity=high&include_resolved=false"` avaliando resposta e fontes.
