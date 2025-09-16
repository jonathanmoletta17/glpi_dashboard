# Plano de Ação: Serviço apiService

## Insights extraídos
- Documentação descreve métodos simples (`getMetrics`, `getTechnicianRanking`, `getNewTickets`, `getSystemStatus`) utilizando `httpClient` diretamente.【F:docs/endpoints/frontend_apiService.md†L13-L124】
- Implementação atual usa `httpClientWithRetry`, trata envelopes incompletos (ex.: `response.data.data.data`) e retorna estruturas parciais com fallbacks mock.【F:frontend/services/api.ts†L10-L154】

## Lacunas identificadas
- Serviço não reutiliza um tipo genérico `ApiResponse<T>`, resultando em parsing manual e risco de divergência entre endpoints.【F:frontend/services/api.ts†L10-L154】
- Métodos carecem de suporte a parâmetros ricos (objetos vs string query) e descartam metadados (`cached`, `correlation_id`).【F:frontend/services/api.ts†L60-L123】
- Ausência de métodos para novos endpoints (`/alerts`, `/technician-performance`, `/health`, `/root`), dificultando expansão futura.【F:docs/endpoints/backend_alerts.md†L181-L199】【F:docs/endpoints/backend_technician_performance.md†L178-L200】

## Próximas ações prioritárias
1. **Centralizar parsing e envelopes**  
   - Criar utilitário `extractData<T>(response: ApiResponse<T>)` que valida presença de `success`/`data` e lança erro se contrato inválido, eliminando verificações aninhadas.【F:frontend/services/api.ts†L10-L154】
   - Usar generics com `ApiResponse<T>` em todos os métodos, preservando metadados nas respostas.
2. **Expandir cobertura de endpoints**  
   - Adicionar métodos para `/alerts`, `/technician-performance`, `/health`, `/openapi.yaml`, `/config/migration`, entre outros documentados, retornando tipos específicos.【F:docs/endpoints/backend_alerts.md†L14-L199】【F:docs/endpoints/backend_technician_performance.md†L14-L188】【F:docs/endpoints/backend_health.md†L16-L177】
   - Converter parâmetros para objetos (ex.: `getTechnicianRanking(filters: RankingFilters)`), serializando internamente.
3. **Padronizar tratamento de erros e retries**  
   - Consolidar lógica de fallback (ex.: métricas mock) em um módulo separado para evitar replicação.
   - Registrar métricas de falha/sucesso por endpoint para futura observabilidade.

## Prompt sugerido para execução
> **Identidade**: Agente `GLPIDataIngestor` responsável pelo cliente REST.
> **Objetivo**: Refatorar `apiService` para usar envelopes padronizados, suportar novos endpoints e preservar metadados.
> **Contexto**: Trabalhar em `frontend/services/api.ts`, `frontend/types/api.ts`, utilitários de querystring e testes; integrar novos métodos aos hooks correspondentes.
> **Passos**: (1) Introduzir `ApiResponse<T>` genérico, (2) refatorar métodos existentes e adicionar endpoints faltantes, (3) criar testes unitários para cada método, (4) atualizar documentação de uso.

## Validações recomendadas
- `npm run test -- apiService` cobrindo parsing de envelopes e erros.
- Verificação manual via Storybook/Playground para cada método novo.
- Monitorar logs para confirmar que retrys (`httpClientWithRetry`) permanecem funcionais após refatoração.
