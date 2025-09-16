# Plano de Ação: Endpoint /metrics

## Insights extraídos
- A documentação descreve resposta envelopada com `success`, `data` e blocos `niveis`, além de metadados de cache e correlação.【F:docs/endpoints/backend_metrics.md†L22-L76】
- O frontend espera métricas detalhadas (tendências, níveis) via hook dedicado e serviço centralizado.【F:docs/endpoints/backend_metrics.md†L97-L115】【F:docs/endpoints/frontend_useMetrics.md†L9-L63】

## Lacunas identificadas
- O `apiService.getMetrics` ainda pressupõe estrutura `response.data.data.data`, sinalizando desalinhamento entre contrato documentado e implementação atual.【F:frontend/services/api.ts†L13-L57】
- A tipagem `DashboardMetrics` usada no hook utiliza campos em maiúsculo (`N1`-`N4`), divergindo do contrato oficial em minúsculo (`n1`-`n4`).【F:docs/endpoints/frontend_useMetrics.md†L25-L63】
- O appConfig aponta endpoint `/metrics`, mas não provê mecanismos para filtros parametrizados mencionados na documentação (datas, tipos).【F:docs/endpoints/backend_metrics.md†L16-L20】【F:frontend/config/appConfig.ts†L12-L28】

## Próximas ações prioritárias
1. **Alinhar contrato backend → frontend**  
   - Ajustar o backend para responder exatamente conforme envelope `success/data` documentado ou adaptar `apiService` para consumir `response.data.data` apenas uma vez, evitando fallback para mocks.【F:docs/endpoints/backend_metrics.md†L22-L76】【F:frontend/services/api.ts†L13-L57】
   - Atualizar `DashboardMetrics` no frontend para usar as chaves em minúsculo e incluir campo `geral` apenas se vier do backend.
2. **Suportar filtros**  
   - Expor parâmetros `start_date`, `end_date` e `filter_type` no serviço (`apiService.getMetrics`) aceitando objeto de filtros e serializando querystring.【F:docs/endpoints/backend_metrics.md†L16-L20】
   - Criar testes cobrindo filtros no backend (ex.: pytest) e mocks de resposta no frontend.
3. **Validar contrato com Zod/Pydantic**  
   - Criar schema Pydantic para saída (`DashboardMetricsResponse`) garantindo presença de campos obrigatórios.【F:docs/endpoints/backend_metrics.md†L149-L155】
   - No frontend, usar Zod ou utilitário similar para validar payload antes de atualizar o estado.

## Prompt sugerido para execução
> **Identidade**: Agente `GLPIDataIngestor` encarregado de contratos de métricas.
> **Objetivo**: Eliminar `response.data.data.data`, padronizar chaves de `niveis` e implementar filtros documentados.
> **Contexto**: Ajuste `backend/api/routes.py` e `GLPIDashboardService` para obedecer ao contrato; atualize `frontend/services/api.ts`, `frontend/types/api.ts` e `useMetrics.ts` para refletir o schema real.
> **Passos**: (1) Harmonizar resposta do backend, (2) refatorar serviço/hook no frontend, (3) adicionar validações e testes (pytest + Vitest), (4) documentar filtros no README.

## Validações recomendadas
- `pytest backend/tests/unit/test_metrics.py` (adicionar caso se não existir) para validar envelope.
- `npm run test -- useMetrics` garantindo que parsing funciona com dados reais.
- Teste manual `curl "http://localhost:5000/api/metrics?start_date=2025-01-01&filter_type=creation"` e comparar com schema TypeScript.
