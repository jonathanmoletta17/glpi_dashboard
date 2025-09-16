# Planos de Ação – GLPI Dashboard

## Contexto Geral
- A documentação existente mapeia integrações backend ↔ frontend, porém aponta lacunas em hooks, validação de contratos e cobertura da OpenAPI.【F:docs/endpoints/README.md†L35-L73】
- Diversos endpoints possuem documentação detalhada mas carecem de implementação completa no frontend (ex.: `/alerts`, `/technician-performance`, `/health`).【F:docs/endpoints/README.md†L37-L47】

## Prioridades Transversais
1. **Padronização de contratos**  
   - Implementar estrutura `ApiResponse<T>` compartilhada e validar com Pydantic/Zod conforme recomendado.【F:docs/endpoints/README.md†L75-L113】
   - Atualizar serviços/hooks para preservar metadados (`cached`, `correlation_id`, `filters_applied`).
2. **Cobertura OpenAPI + Codegen**  
   - Expandir `openapi.yaml` para todos os endpoints e automatizar lint/geração de tipos (ver plano específico).【F:docs/endpoints/backend_openapi.md†L16-L164】
3. **Infra de caching e retries**  
   - Melhorar estratégia de cache e retry nos clientes (frontend/back) alinhando com recomendações de docs (cache inteligente, TTL adaptativo).【F:docs/endpoints/README.md†L59-L70】
4. **Feature flags e configuração**  
   - Sincronizar `.env` e `appConfig` garantindo que variáveis críticas sejam validadas e documentadas.【F:docs/endpoints/frontend_appConfig.md†L48-L200】

## Sequência Recomendada
1. **Contrato e codegen**: implementar `ApiResponse<T>` + validação, atualizar OpenAPI e gerar tipos.
2. **Serviços/Hooks críticos**: refatorar `apiService`, `useMetrics`, `useRanking`, `useTickets` para usar contratos atualizados e suportar filtros.
3. **Novos consumidores**: criar hooks/serviços para `/alerts`, `/technician-performance`, `/health`, `/root`.
4. **Configuração e infraestrutura**: alinhar `httpClient` e `appConfig`, validar envs, ajustar retries/cache.
5. **Observabilidade e testes**: adicionar testes pytest/Vitest, métricas de retry/cache e documentação no README principal.

## Artefatos Gerados
- Planos individuais por endpoint/serviço encontram-se neste diretório (`docs/action_plans/`). Consulte-os para instruções específicas, prompts e validações.

## Próximos Passos
- Nomear responsáveis por cada plano (ex.: `GLPIDataIngestor` para contratos, `DashboardDesigner` para UI) seguindo prompts sugeridos.
- Montar cronograma incremental (ex.: Semana 1 – contratos e codegen; Semana 2 – hooks; Semana 3 – endpoints extras; Semana 4 – observabilidade).
- Acompanhar progresso via checklist compartilhado e validar cada entrega com os testes recomendados.
