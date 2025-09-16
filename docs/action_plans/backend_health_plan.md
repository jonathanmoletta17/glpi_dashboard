# Plano de Ação: Endpoint /health

## Insights extraídos
- Endpoint entrega estado detalhado dos serviços GLPI/Redis e métricas básicas de sistema, porém sem cache e sem tipagem frontend.【F:docs/endpoints/backend_health.md†L16-L177】
- Recomendação explícita para implementar cache curto, controle de nível de detalhe e documentação OpenAPI.【F:docs/endpoints/backend_health.md†L147-L159】

## Lacunas identificadas
- O frontend não possui tipo `HealthResponse`, impedindo validação estática do contrato.【F:docs/endpoints/backend_health.md†L79-L111】
- Requisições repetidas executam verificações completas (sem cache), impactando tempo de resposta em cenários com degradação.【F:docs/endpoints/backend_health.md†L142-L149】
- Informações sensíveis (uso de memória, tokens) podem ser expostas sem restrição de ambiente.【F:docs/endpoints/backend_health.md†L141-L157】

## Próximas ações prioritárias
1. **Padronizar contrato**  
   - Documentar rota `/health` na OpenAPI e criar interface `HealthResponse` em `frontend/types/api.ts` com enums correspondentes.【F:docs/endpoints/backend_health.md†L79-L111】【F:docs/endpoints/backend_health.md†L147-L159】
   - Expor método `getHealth()` em `apiService` com fallback e testes unitários.
2. **Adicionar cache e níveis de detalhe**  
   - Introduzir cache curto (30-60s) usando `cache_with_filters` ou mecanismo equivalente para reduzir carga.【F:docs/endpoints/backend_health.md†L147-L149】
   - Implementar parâmetro `detail=basic|full` para controlar volume de informações retornadas, restringindo métricas sensíveis em produção.【F:docs/endpoints/backend_health.md†L147-L157】
3. **Fortalecer observabilidade**  
   - Registrar eventos de health check no `performance_monitor` e disponibilizar status agregado para integração com `/alerts`.
   - Criar testes automatizados cobrindo cenários `healthy`, `degraded` e `unhealthy` com e sem cache.

## Prompt sugerido para execução
> **Identidade**: Agente `GLPIDataIngestor` focado em observabilidade.
> **Objetivo**: Padronizar e proteger o endpoint `/health`, incluindo cache, tipagem e documentação.
> **Contexto**: Ajustar `backend/api/routes.py`, middleware de cache e `frontend/services/api.ts`/`types/api.ts`; atualizar OpenAPI e documentação de segurança.
> **Passos**: (1) Criar tipo TS + método `getHealth`, (2) adicionar cache e parâmetro de detalhe no backend, (3) escrever testes pytest cobrindo diferentes estados, (4) atualizar OpenAPI/README.

## Validações recomendadas
- `pytest backend/tests/unit/test_health.py` validando cenários healthy/unhealthy e cache.
- `npm run test -- getHealth` (novo) exercitando serviço frontend.
- Teste manual `curl "http://localhost:5000/api/health?detail=basic"` vs `detail=full` verificando redacted fields.
