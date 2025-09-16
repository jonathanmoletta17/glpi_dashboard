# Plano de Ação: Endpoint /status

## Insights extraídos
- Endpoint simplificado retorna estado geral com campos `status`, `glpi_status`, `cache_status`, `data_source` e metadados de cache/correlação.【F:docs/endpoints/backend_status.md†L16-L94】
- O frontend possui método `getSystemStatus`, porém aplica fallbacks genéricos que ignoram `success/cached` e converte resposta em formato alternativo.【F:frontend/services/api.ts†L96-L124】
- Documentação sugere integração com alertas e melhorias de realtime/histórico.【F:docs/endpoints/backend_status.md†L123-L137】

## Lacunas identificadas
- Tipagens TypeScript não refletem o envelope (apenas fallback `SystemStatus` sem campos `cached`/`correlation_id`).【F:docs/endpoints/backend_status.md†L60-L94】【F:frontend/services/api.ts†L96-L124】
- Ausência de hook dedicado com polling configurável; componentes precisam lidar manualmente com loading e erros.【F:docs/endpoints/backend_status.md†L105-L160】
- Cache fixo de 60s pode mascarar falhas críticas; não há lógica adaptativa baseada em severidade.【F:docs/endpoints/backend_status.md†L123-L137】

## Próximas ações prioritárias
1. **Alinhar cliente frontend**  
   - Ajustar `apiService.getSystemStatus` para retornar `SystemStatusResponse` completo, removendo fallback que altera estrutura e expondo `cached`, `correlation_id` e `issues` quando presentes.【F:frontend/services/api.ts†L96-L124】【F:docs/endpoints/backend_status.md†L16-L94】
   - Criar hook `useSystemStatus` com opções de polling adaptativo (intervalo menor quando degradado/offline).
2. **Tipagem e UI**  
   - Definir `SystemStatusResponse` em `frontend/types/api.ts` conforme documentação.【F:docs/endpoints/backend_status.md†L60-L94】
   - Atualizar componentes do dashboard para exibir badges de severidade, origem dos dados e mensagens de issues.
3. **Otimizar cache/observabilidade**  
   - Tornar TTL configurável via `SYSTEM_STATUS_CACHE_TTL` e reduzir automaticamente quando status ≠ `operational`。【F:docs/endpoints/backend_status.md†L110-L137】
   - Registrar transições de estado em log/alerta para integração com `/alerts`.

## Prompt sugerido para execução
> **Identidade**: Agente `DashboardDesigner` responsável por status operacional.
> **Objetivo**: Alinhar contrato do endpoint `/status`, exibir indicadores visuais e ajustar cache adaptativo.
> **Contexto**: Atualizar `frontend/services/api.ts`, criar `useSystemStatus`, modificar componentes do dashboard e ajustar lógica de cache no backend (`backend/api/routes.py`). Documentar novas variáveis (`SYSTEM_STATUS_CACHE_TTL`).
> **Passos**: (1) Atualizar tipos/serviço, (2) criar hook + UI, (3) implementar cache adaptativo e logs no backend, (4) escrever testes (pytest + React) cobrindo estados operational/degraded/offline.

## Validações recomendadas
- `pytest backend/tests/unit/test_status.py` cobrindo TTL adaptativo e envelope.
- `npm run test -- useSystemStatus` validando hook e parsing de issues.
- Testes manuais alterando `SYSTEM_STATUS_CACHE_TTL` e simulando falhas de GLPI para verificar atualização do front.
