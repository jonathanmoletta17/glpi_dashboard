# Plano de Ação: Endpoint /technicians/ranking

## Insights extraídos
- A rota aceita filtros de data, nível e limite, retornando lista ordenada de técnicos com metadados de cache e correlação.【F:docs/endpoints/backend_technicians_ranking.md†L16-L64】【F:backend/api/routes.py†L687-L840】
- O frontend consome o endpoint via `apiService.getTechnicianRanking` e hook `useRanking`, porém a interface atual ignora filtros opcionais.【F:frontend/services/api.ts†L60-L74】【F:docs/endpoints/frontend_useRanking.md†L9-L76】

## Lacunas identificadas
- O serviço frontend não aceita parâmetros estruturados; ele recebe apenas uma string opcional, dificultando uso dos filtros descritos.【F:frontend/services/api.ts†L60-L74】
- Não há validação TypeScript para o envelope `success/data/cached`, levando o hook a perder informações de metadados (e.g., `filters_applied`).【F:docs/endpoints/backend_technicians_ranking.md†L67-L97】
- Falta teste automatizado cobrindo o fluxo com filtros e cache (apenas logs mostram execução).【F:backend/api/routes.py†L721-L804】

## Próximas ações prioritárias
1. **Refatorar cliente frontend**  
   - Atualizar `getTechnicianRanking` para aceitar objeto de filtros (`{ startDate, endDate, level, entityId, limit }`) e serializá-lo corretamente, preservando envelope completo retornado pelo backend.【F:frontend/services/api.ts†L60-L74】【F:docs/endpoints/backend_technicians_ranking.md†L16-L64】
   - Ajustar `useRanking` para expor estado de filtros ativos e metadados (`cached`, `filters_applied`).
2. **Compartilhar contrato**  
   - Criar tipo `TechnicianRankingResponse` em `frontend/types/api.ts` incluindo `filters_applied` e `correlation_id` conforme documentação.【F:docs/endpoints/backend_technicians_ranking.md†L67-L97】
   - Garantir que o backend retorne sempre `success`/`data` mesmo quando a lista estiver vazia (já tratado, mas adicionar teste).
3. **Cobrir com testes e monitoramento**  
   - Escrever teste pytest que chama `/technicians/ranking` com e sem filtros, validando uso de cache (`cached` true/false) e resposta vazia controlada.【F:backend/api/routes.py†L721-L840】
   - No frontend, adicionar teste de hook (React Testing Library) simulando resposta com filtros.

## Prompt sugerido para execução
> **Identidade**: Agente `GLPIDataIngestor` com foco em ranking.
> **Objetivo**: Permitir filtros ricos no ranking de técnicos e alinhar tipagem/contrato.
> **Contexto**: Trabalhar em `frontend/services/api.ts`, `frontend/hooks/useRanking.ts`, `frontend/types/api.ts` e testes correspondentes; complementar com teste pytest em `backend/tests/`.
> **Passos**: (1) Modelar DTO de filtros, (2) refatorar serviço/hook, (3) criar testes (frontend + backend), (4) atualizar documentação de uso de filtros no README.

## Validações recomendadas
- `pytest backend/tests/unit/test_ranking.py` (criar se inexistente) cobrindo filtros e cache.
- `npm run test -- useRanking` para garantir que hook consome novo contrato.
- Teste manual `curl "http://localhost:5000/api/technicians/ranking?level=N1&limit=5"` comparando com resposta tipada.
