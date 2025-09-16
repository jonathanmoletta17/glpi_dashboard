# Plano de Ação: Endpoint /technician-performance

## Insights extraídos
- A documentação apresenta contrato rico com métricas detalhadas, comparações, tendências e cache de 30 minutos.【F:docs/endpoints/backend_technician_performance.md†L21-L188】
- O endpoint exige `technician_id` e aceita filtros de período e `include_comparison` para controlar análise.【F:docs/endpoints/backend_technician_performance.md†L14-L55】
- Atualmente não há consumo no frontend, apesar do potencial para páginas de detalhe e gráficos dedicados.【F:docs/endpoints/backend_technician_performance.md†L178-L200】

## Lacunas identificadas
- O frontend carece de serviço/hook para buscar dados de performance, inviabilizando uso do endpoint documentado.【F:frontend/services/api.ts†L10-L125】
- Não existem testes automatizados garantindo cálculo de métricas e comparação com médias, especialmente quando `include_comparison=false`.
- Falta política clara para exposição de dados sensíveis (ex.: satisfação, rank) e controle de acesso.

## Próximas ações prioritárias
1. **Disponibilizar consumo frontend**  
   - Adicionar método `getTechnicianPerformance(params)` em `apiService` aceitando `{ technicianId, startDate, endDate, includeComparison }` e retornando `TechnicianPerformanceResponse` completo.【F:docs/endpoints/backend_technician_performance.md†L14-L166】
   - Criar hook `useTechnicianPerformance` com suporte a cache local, polling configurável e tratamento de loading/erro.
2. **Validar cálculos e cache**  
   - Adicionar testes pytest para cenários com/sem comparação, diferentes períodos e validação de cache TTL (30 min).【F:docs/endpoints/backend_technician_performance.md†L74-L188】
   - Incluir testes de contrato garantindo presença de campos obrigatórios (metrics, comparison, trends, categories).
3. **Governança de dados**  
   - Definir regra de autorização (token ou roles) antes de expor métricas sensíveis; registrar no README de segurança.
   - Adicionar feature flag (`ENABLE_TECH_PERFORMANCE`) para controlar disponibilidade do endpoint em produção.

## Prompt sugerido para execução
> **Identidade**: Agente `GLPIDataIngestor` especializado em relatórios de performance.
> **Objetivo**: Habilitar consumo do endpoint `/technician-performance` pelo frontend com contratos validados e políticas de acesso.
> **Contexto**: Alterar `frontend/services/api.ts`, adicionar novo hook em `frontend/hooks/`, tipagens em `frontend/types/api.ts`, e criar testes (frontend e pytest). Ajustar backend para respeitar feature flag quando necessário.
> **Passos**: (1) Modelar tipos TS, (2) implementar serviço/hook, (3) criar testes e documentação de segurança, (4) revisar cache TTL.

## Validações recomendadas
- `pytest backend/tests/unit/test_technician_performance.py` cobrindo parâmetros obrigatórios e opcionais.
- `npm run test -- useTechnicianPerformance` (novo) validando fluxo no frontend.
- Teste manual `curl "http://localhost:5000/api/technician-performance?technician_id=123&include_comparison=true"` verificando payload completo.
