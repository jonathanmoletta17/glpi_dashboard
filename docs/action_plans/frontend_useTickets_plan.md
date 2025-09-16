# Plano de Ação: Hook useTickets

## Insights extraídos
- Hook faz polling a cada 45s e retorna lista de tickets novos sem suporte a filtros avançados.【F:docs/endpoints/frontend_useTickets.md†L9-L88】
- Contrato backend inclui campos `total_count`, `filters_applied`, `cached` e metadados de origem.【F:docs/endpoints/backend_tickets_new.md†L23-L127】

## Lacunas identificadas
- Hook/serviço retornam apenas array de tickets, descartando `total_count`, `cached` e `correlation_id` necessários para UX e debugging.【F:frontend/services/api.ts†L77-L93】【F:docs/endpoints/backend_tickets_new.md†L23-L127】
- Não há forma de aplicar filtros (status, priority, date range) a partir do frontend, embora documentados no backend.【F:docs/endpoints/backend_tickets_new.md†L16-L79】【F:docs/endpoints/frontend_useTickets.md†L25-L68】
- Falta estratégia de paginação/infinite scroll; hook sempre substitui lista inteira.

## Próximas ações prioritárias
1. **Alinhar contrato de resposta**  
   - Atualizar serviço/hook para retornar objeto `{ tickets, totalCount, cached, filtersApplied, correlationId }`, preservando dados de origem (`data_source`, `is_mock_data`).【F:docs/endpoints/backend_tickets_new.md†L23-L127】
   - Expor `setFilters` no hook, permitindo ajustes dinâmicos (status, priority, technician, limit).
2. **Paginação e UX**  
   - Implementar paginação incremental (cursor/offset) no hook e nos componentes, reduzindo carga inicial.【F:docs/endpoints/backend_tickets_new.md†L159-L177】
   - Adicionar indicadores visuais para fonte de dados, SLA restante e badges de prioridade.
3. **Testes e monitoramento**  
   - Criar testes de hook simulando mudanças de filtros, paginação e falhas de rede.
   - Documentar processos de ofuscação de dados sensíveis (e-mail) e validar via testes.

## Prompt sugerido para execução
> **Identidade**: Agente `DashboardDesigner` orientado a tickets.
> **Objetivo**: Estender `useTickets` para suportar filtros/paginação e preservar metadados do backend.
> **Contexto**: Ajustar `frontend/services/api.ts`, `frontend/hooks/useTickets.ts`, componentes do dashboard e tipos TS; alinhar com mudanças no backend (`/tickets/new`).
> **Passos**: (1) Atualizar serviço e hook, (2) implementar paginação e UI correspondente, (3) adicionar testes, (4) documentar novas props/variáveis.

## Validações recomendadas
- `npm run test -- useTickets` cobrindo filtros, paginação e erros.
- Teste manual com `curl` e comparação da UI (contagem total vs exibida).
- Monitorar logs de backend para validar recebimento de filtros/paginação.
