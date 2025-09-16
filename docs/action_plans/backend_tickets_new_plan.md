# Plano de Ação: Endpoint /tickets/new

## Insights extraídos
- A rota suporta filtros (`limit`, `status`, `priority`, `assigned_to`) e retorna envelope com `total_count`, `filters_applied` e metadados de cache.【F:docs/endpoints/backend_tickets_new.md†L16-L79】
- O frontend consome o endpoint via `apiService.getNewTickets` e hook `useTickets`, com refresh automático de 45s.【F:frontend/services/api.ts†L77-L93】【F:docs/endpoints/frontend_useTickets.md†L9-L68】

## Lacunas identificadas
- O serviço frontend envia apenas `limit`, ignorando filtros adicionais descritos no contrato, o que dificulta reproduzir cenários reais durante análises.【F:frontend/services/api.ts†L77-L93】【F:docs/endpoints/backend_tickets_new.md†L16-L79】
- Não há paginação implementada (cursor/offset) apesar da recomendação explícita, podendo sobrecarregar o frontend com listas grandes.【F:docs/endpoints/backend_tickets_new.md†L159-L177】
- Dados sensíveis (e-mail do solicitante) são entregues diretamente ao frontend sem ofuscação ou consentimento explícito.【F:docs/endpoints/backend_tickets_new.md†L35-L63】

## Próximas ações prioritárias
1. **Ampliar filtros no cliente**  
   - Atualizar `apiService.getNewTickets` para aceitar objeto de filtros (status, priority, technician, date range) e refletir `filters_applied` na resposta do hook.【F:frontend/services/api.ts†L77-L93】【F:docs/endpoints/backend_tickets_new.md†L16-L79】
   - Adaptar `useTickets` para receber opções (intervalo de refresh customizado, filtros dinâmicos) e propagar metadados (total_count, cached).
2. **Implementar paginação segura**  
   - Introduzir suporte a paginação por cursor/offset no backend (`/tickets/new`) e expor parâmetros (`page`, `cursor`, `page_size`) devidamente validados.【F:docs/endpoints/backend_tickets_new.md†L159-L177】
   - Ajustar hook/componente para lidar com carregamento incremental (infinite scroll ou paginação tradicional).
3. **Tratar dados sensíveis**  
   - Avaliar necessidade de mascarar ou omitir e-mails no payload, expondo apenas domínio ou inicial quando requerido.【F:docs/endpoints/backend_tickets_new.md†L35-L63】【F:docs/endpoints/backend_tickets_new.md†L165-L176】
   - Documentar política de privacidade e adicionar testes garantindo que ofuscação ocorre quando habilitada.

## Prompt sugerido para execução
> **Identidade**: Agente `GLPIDataIngestor` responsável por tickets recentes.
> **Objetivo**: Suportar filtros completos, paginação e proteção de dados sensíveis nos tickets novos.
> **Contexto**: Alterar `backend/api/routes.py`, serviços de tickets e `frontend/services/api.ts`/`useTickets.ts`; atualizar `frontend/types/api.ts` com envelope `NewTicketsResponse` completo.
> **Passos**: (1) Estender filtros e paginação no backend, (2) refletir mudanças no frontend, (3) mascarar e-mails conforme configuração, (4) criar testes (pytest + React Testing Library) e atualizar documentação.

## Validações recomendadas
- `pytest backend/tests/unit/test_tickets_new.py` cobrindo filtros, paginação e mascaramento.
- `npm run test -- useTickets` validando comportamento do hook com novos filtros.
- Teste manual `curl "http://localhost:5000/api/tickets/new?status=new&priority=high&limit=5"` verificando `filters_applied` e ofuscação.
