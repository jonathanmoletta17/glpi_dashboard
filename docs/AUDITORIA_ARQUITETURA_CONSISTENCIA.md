# Auditoria de Arquitetura e Consistência – GLPI Dashboard

## 1. Contexto e Objetivo
Esta auditoria foi conduzida para validar a base arquitetural antes da execução dos planos descritos em `docs/action_plans`, garantindo que não existam dívidas estruturais capazes de perpetuar erros difíceis de rastrear. O foco abrange backend (Flask + Clean Architecture híbrida), frontend (React + Vite) e a cadeia de ingestão de dados do GLPI, com especial atenção à montagem de _criteria_ na API do GLPI.

Referências centrais:
- Diretrizes transversais dos planos de ação que priorizam padronização de contratos, OpenAPI, caching e alinhamento de configuração.【F:docs/action_plans/README.md†L1-L31】
- Componentes críticos do backend (`MetricsFacade`, adapters legados e serviços GLPI).【F:backend/core/application/services/metrics_facade.py†L1-L199】【F:backend/core/infrastructure/adapters/legacy_service_adapter.py†L1-L200】【F:backend/services/legacy/glpi_service_facade.py†L1-L200】
- Serviços do frontend responsáveis por contratos e consumo de dados.【F:frontend/services/api.ts†L1-L155】【F:frontend/types/api.ts†L1-L99】【F:frontend/services/httpClient.ts†L1-L179】

## 2. Visão Atual da Arquitetura
### 2.1 Backend
- **Ponto de entrada**: Flask `app.py` realiza configuração de logging, CORS e registra _blueprints_.【F:backend/app.py†L1-L45】
- **Configuração**: `config/settings.py` concentra validações robustas de variáveis de ambiente, _feature flags_ (`USE_LEGACY_SERVICES`, `USE_MOCK_DATA`) e parâmetros de observabilidade.【F:backend/config/settings.py†L1-L200】
- **Camada de aplicação**: `MetricsFacade` decide dinamicamente entre `LegacyServiceAdapter` (serviços GLPI herdados) e `GLPIMetricsAdapter`, mantendo contratos síncronos para Flask, porém invocando lógica assíncrona e cache unificado.【F:backend/core/application/services/metrics_facade.py†L1-L199】
- **Camada legacy**: `LegacyServiceAdapter` encapsula _retry_, monitoramento e conversão de dados consumindo `GLPIServiceFacade`, o qual ainda expõe a interface monolítica antiga através de serviços decompondo autenticação, cache e montagem de _criteria_.【F:backend/core/infrastructure/adapters/legacy_service_adapter.py†L1-L200】【F:backend/services/legacy/glpi_service_facade.py†L1-L200】
- **Cache**: `UnifiedCache` mantém cache em memória com TTL e estatísticas básicas, porém sem isolamento por processo (risco em ambientes com múltiplos workers).【F:backend/core/infrastructure/cache/unified_cache.py†L1-L118】
- **Consultas GLPI**: `metrics_service.py` e serviços correlatos continuam construindo manualmente estruturas `criteria`/`metacriteria` para filtros finos (datas, níveis, prioridades), exigindo preservação cuidadosa dessas regras em qualquer refatoração.【F:backend/services/legacy/metrics_service.py†L73-L158】

### 2.2 Frontend
- **Configuração**: `httpClient.ts` aplica axios com _retry_, placeholders de autenticação e descoberta automática de baseURL, enquanto `appConfig.ts` replica endpoints e _feature flags_ de forma estática.【F:frontend/services/httpClient.ts†L1-L179】【F:frontend/config/appConfig.ts†L1-L101】
- **Contratos**: Tipagens em `types/api.ts` esperam objetos completos (ex.: `DashboardMetrics` com totais, `data_source`, `is_mock_data`).【F:frontend/types/api.ts†L1-L99】
- **Serviços/Hooks**: `apiService` converte manualmente respostas aninhadas (`response.data.data.data`), aplica _fallbacks_ para dados mockados e ignora metadados de execução; hooks (`useMetrics`, `useRanking`, `useTickets`) apenas _polling_ os endpoints e não propagam filtros ou estado avançado.【F:frontend/services/api.ts†L1-L155】【F:frontend/hooks/useMetrics.ts†L1-L35】

## 3. Principais Inconsistências e Dívidas Técnicas
### 3.1 Convivência de Clean Architecture e legado
- `MetricsFacade` mantém bifurcação via `USE_LEGACY_SERVICES`, mas apenas inicializa `query_factory` quando usa o adapter novo; na opção legacy, toda a lógica permanece síncrona, causando duplicação de contratos e tratamentos de erro.【F:backend/core/application/services/metrics_facade.py†L41-L168】
- `LegacyServiceAdapter` adiciona _retry_, log estruturado e conversão, porém retorna diretamente `ApiResponse` (Pydantic) do legado, conflitando com expectativa de DTOs no domínio limpo e dificultando substituição progressiva.【F:backend/core/infrastructure/adapters/legacy_service_adapter.py†L69-L179】

### 3.2 Complexidade desnecessária na camada legacy
- `GLPIServiceFacade` reconstrói uma “mini arquitetua” interna (auth/cache/http/metrics/trends) mantendo a mesma interface monolítica, resultando em acoplamento forte e repetição de logs/cache em múltiplos níveis.【F:backend/services/legacy/glpi_service_facade.py†L21-L195】
- Lógicas de _criteria_ GLPI estão espalhadas entre `metrics_service`, `glpi_service_facade` e adaptadores, elevando risco de regressões quando filtros são ajustados.【F:backend/services/legacy/metrics_service.py†L73-L158】

### 3.3 Contratos inconsistentes entre camadas
- Frontend espera `DashboardMetrics` com campo `total`, `timestamp`, `data_source`, mas `apiService.getMetrics` monta um objeto incompleto e adiciona `niveis.geral`, divergindo do schema Pydantic que separa níveis (`N1..N4`) e totals já calculados.【F:frontend/services/api.ts†L15-L155】【F:frontend/types/api.ts†L16-L42】
- Respostas do backend embrulham dados em múltiplos níveis (`response.data.data.data`), indicando ausência de padronização `ApiResponse<T>` e validação automática mencionadas nos planos de ação.【F:frontend/services/api.ts†L11-L57】【F:docs/action_plans/README.md†L7-L23】

### 3.4 Configuração e _feature flags_ duplicadas
- `config/settings.py` controla `USE_MOCK_DATA`/`USE_LEGACY_SERVICES`, enquanto `appConfig.ts` e `httpClient.ts` mantêm lógica paralela de _mocks_, _retry_ e endpoints; sem sincronização automática, configurações podem divergir entre ambientes.【F:backend/config/settings.py†L78-L133】【F:frontend/services/httpClient.ts†L1-L179】【F:frontend/config/appConfig.ts†L1-L101】

### 3.5 Observabilidade e testes
- Middleware de observabilidade é registrado, mas faltam métricas específicas para diferenciar caminho legacy vs. novo e não há testes automatizados para garantir o contrato `ApiResponse` nas rotas.
- Hooks do frontend não expõem telemetria (ex.: tempo de resposta, erro cumulativo), inviabilizando diagnóstico rápido quando cache ou filtros quebram.【F:frontend/hooks/useMetrics.ts†L1-L35】

## 4. Recomendações de Reestruturação
### 4.1 Roadmap incremental (preservando _criteria_ GLPI)
1. **Estabilizar contratos**: aplicar `ApiResponse<T>` único no backend (camada Flask) e ajustar `apiService` para ler apenas `response.data` + metadados, eliminando o triplo `data` e garantindo validação Pydantic/Zod conforme plano transversal.【F:frontend/services/api.ts†L11-L57】【F:docs/action_plans/README.md†L7-L23】
2. **Faixa anti-regressão de critérios**: encapsular montagens de `criteria` em serviços reutilizáveis (ex.: `glpi_query_builder.py`) com testes unitários baseados nas combinações críticas vistas em `metrics_service`, evitando duplicidade em adapters.【F:backend/services/legacy/metrics_service.py†L73-L158】
3. **Camada de orquestração**: redefinir `MetricsFacade` para sempre retornar DTOs do domínio, delegando conversão de `ApiResponse` ao controller Flask. Criar _feature flag_ apenas para selecionar o _data source_ (legacy x GLPI direto) sem alterar contrato.【F:backend/core/application/services/metrics_facade.py†L41-L199】
4. **Adapter simplificado**: evoluir `LegacyServiceAdapter` para expor métodos mínimos (`fetch_metrics`, `fetch_tickets`, etc.) que retornem estruturas primitivas, deixando mapeamento Pydantic na camada de aplicação.【F:backend/core/infrastructure/adapters/legacy_service_adapter.py†L69-L179】
5. **Frontend alinhado**: gerar tipos a partir da OpenAPI atualizada, atualizar `apiService`/hooks para propagar filtros (datas, níveis, prioridade) e armazenar metadados (correlationId, cache hit) para observabilidade no dashboard.【F:frontend/services/api.ts†L11-L155】【F:frontend/hooks/useMetrics.ts†L1-L35】

### 4.2 Opção de reescrita controlada
Caso se opte por reescrever o backend:
- Definir módulos explícitos (`glpi_client`, `metrics_repository`, `metrics_service`, `dashboard_api`) e mover a lógica de _criteria_ intacta para uma camada `query_builders`, garantindo paridade com `metrics_service` existente antes de desmontar o legado.【F:backend/services/legacy/metrics_service.py†L73-L158】
- Implementar _ports/adapters_ simples (FastAPI/Flask) usando testes de aceitação contra o GLPI real ou _fixtures_ gravadas para não quebrar filtros.
- Manter `USE_MOCK_DATA` como _feature flag_ de fallback até que a nova cadeia esteja validada em produção limitada.【F:backend/config/settings.py†L78-L90】

### 4.3 Simplificação de configuração
- Consolidar configurações em um manifesto (ex.: `config/runtime_settings.json`) gerado a partir de variáveis de ambiente e consumido pelo frontend, eliminando divergência entre `appConfig.ts` e backend.
- Expor endpoint `/config/runtime` autenticado que devolva flags ativas e limites de cache, alimentando o dashboard de observabilidade.

## 5. Automação e Governança Recomendadas
1. **Lint + Formatação**: aplicar `ruff`/`black` no backend e `eslint`/`prettier` no frontend para evitar deriva estrutural.
2. **Testes de contrato**: criar suíte pytest que chama endpoints e valida modelos Pydantic (ex.: `ApiResponse[DashboardMetrics]`), além de testes Vitest para `apiService`/hooks com _fixtures_ simulando respostas GLPI.【F:frontend/services/api.ts†L11-L155】
3. **Testes arquiteturais**: usar `pytest-arch` ou `import-linter` para garantir dependências unidirecionais (ex.: `core.domain` não pode importar `services.legacy`).
4. **CI/CD**: pipeline com etapas de lint, testes, geração de OpenAPI e _schema diff_ (falha se modelos divergirem). Incluir etapa que roda consultas GLPI com _criteria_ conhecidos para detectar mudanças no sistema remoto.
5. **Observabilidade**: instrumentar `MetricsFacade` para registrar qual adapter foi usado, tempo de resposta, cache hit/miss e ID de correlação, expondo métricas Prometheus segmentadas por fonte de dados.【F:backend/core/application/services/metrics_facade.py†L41-L199】【F:backend/core/infrastructure/cache/unified_cache.py†L1-L118】

## 6. Integração com os Planos de Ação Existentes
- **Fase 0 – Hardening arquitetural**: executar itens 4.1.1–4.1.4 antes dos planos de serviços/hooks descritos em `action_plans`, garantindo base estável para codegen e OpenAPI.【F:docs/action_plans/README.md†L7-L23】
- **Fase 1 – Contratos & Codegen**: alinhar `ApiResponse<T>` e publicar OpenAPI; em seguida, regenerar tipos no frontend para remover _fallbacks_ manuais.【F:frontend/services/api.ts†L11-L57】
- **Fase 2 – Hooks e Observabilidade**: atualizar `useMetrics/useRanking/useTickets` para consumir filtros, expor status de cache e integrar métricas no dashboard conforme metas de SLA.
- **Fase 3 – Extensão de endpoints**: somente após consolidação estrutural, implementar `/alerts`, `/technician-performance`, `/health` conforme planos específicos.

## 7. Próximos Passos e Riscos
1. **Mapear dependências críticas**: listar quais telas/relatórios dependem da cadeia legacy antes de desativá-la.
2. **Criar _playbook_ de rollback**: documentar como reativar `USE_LEGACY_SERVICES` e mocks se a nova cadeia falhar em produção.【F:backend/config/settings.py†L78-L90】
3. **Versionar _criteria_ GLPI**: armazenar consultas validadas (ex.: JSON/YAML) para comparação automática entre versões.
4. **Riscos principais**:
   - Quebra de filtros GLPI por alterações silenciosas no servidor – mitigado com testes de regressão baseados nas montagens atuais.【F:backend/services/legacy/metrics_service.py†L73-L158】
   - Divergência entre contrato backend ↔ frontend – mitigado com codegen e lint de contratos.【F:frontend/types/api.ts†L1-L99】
   - Falta de isolamento do cache em produção multi-worker – considerar backend Redis ou invalidar cache ao iniciar múltiplos processos.【F:backend/core/infrastructure/cache/unified_cache.py†L1-L118】

Com estes ajustes e governança, o projeto ganha rastreabilidade, elimina inconsistências históricas e cria base sólida para evoluir o dashboard sem replicar dívidas técnicas.
