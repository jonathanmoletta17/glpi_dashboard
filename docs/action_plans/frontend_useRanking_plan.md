# Plano de Ação: Hook useRanking

## Insights extraídos
- Hook atual realiza fetch a cada 60s, mas não aceita filtros nem retorna metadados de cache/correlação.【F:docs/endpoints/frontend_useRanking.md†L9-L87】
- O contrato backend prevê filtros (`limit`, `start_date`, `end_date`, `level`, `entity_id`) e campos adicionais na resposta.【F:docs/endpoints/backend_technicians_ranking.md†L16-L97】

## Lacunas identificadas
- `useRanking` chama serviço sem parâmetros estruturados, impossibilitando explorar filtros avançados do backend.【F:frontend/services/api.ts†L60-L74】
- Hook não expõe `filters_applied`, `cached` ou `correlation_id`, impedindo UI de exibir contexto da consulta.【F:docs/endpoints/backend_technicians_ranking.md†L67-L97】
- Intervalo fixo de 60s não considera cenários de degradação ou dashboards em background.

## Próximas ações prioritárias
1. **Adicionar suporte a filtros e metadados**  
   - Atualizar hook para receber objeto `{ filters, refreshInterval }`, invocar serviço com querystring gerada a partir de filtros e armazenar `response.metadata` separadamente.【F:docs/endpoints/backend_technicians_ranking.md†L16-L97】【F:frontend/services/api.ts†L60-L74】
   - Expor `setFilters` ou método `updateFilters` para permitir interação via UI.
2. **Integração com caching e estados**  
   - Considerar uso de TanStack Query/SWR para caching e refetch automático ao focar a aba.
   - Incluir fallback visual quando `is_mock_data` estiver true.
3. **Testes e documentação**  
   - Criar testes de hook verificando atualização ao mudar filtros, tratamento de erros e exibição de ranking vazio.
   - Atualizar README com exemplos de uso (combinação com dropdowns de nível/entidade).

## Prompt sugerido para execução
> **Identidade**: Agente `DashboardDesigner` para ranking de técnicos.
> **Objetivo**: Permitir filtros ricos, metadados e caching no `useRanking`.
> **Contexto**: Refatorar `frontend/hooks/useRanking.ts`, `frontend/services/api.ts` e tipos associados; adicionar testes.
> **Passos**: (1) Ajustar serviço/hook para aceitar filtros, (2) expor metadados, (3) integrar com caching adaptativo, (4) documentar e testar.

## Validações recomendadas
- `npm run test -- useRanking` com cenários de filtros e erro de rede.
- UI manual exibindo ranking filtrado por nível/entidade.
- Monitorar logs do backend para garantir que filtros estão chegando corretamente (`[ROUTES DEBUG]`).
