# 05 — Governança de Qualidade e Automação

## 1. Objetivos
Estabelecer mecanismos para impedir regressões estruturais, garantir consistência entre camadas e detectar violações arquiteturais antes que cheguem a produção.

## 2. Fluxo de Desenvolvimento
1. **RFC obrigatória** para mudanças que alterem estrutura, contratos ou integrações.
2. **Branches curtas** (`feature/...`, `fix/...`) criadas a partir de `main`.
3. **Pull Request** precisa referenciar seções desta documentação.
4. **Code Review** em duas etapas:
   - Review técnico (engenharia) → valida padrões de código e testes.
   - Review de arquitetura (Arquiteto/Tech Lead) → confirma alinhamento com princípios.
5. **Checklists automáticos** impedem merge sem todos os _checks_ verdes.

## 3. Pipeline CI/CD
| Etapa                | Ferramentas                         | Objetivo                                                                        |
|----------------------|-------------------------------------|----------------------------------------------------------------------------------|
| `lint`               | `ruff`, `mypy`, `black --check`, `eslint`, `stylelint` | Garantir padrões de estilo e tipagem.                                          |
| `unit-tests`         | `pytest`, `vitest`                  | Validar lógica de domínio e componentes isolados.                              |
| `contract-tests`     | `pytest` + `respx`, `pact`, `msw`   | Garantir compatibilidade GLPI ↔ backend ↔ frontend.                             |
| `security`           | `bandit`, `pip-audit`, `npm audit`, `trivy` | Detectar vulnerabilidades.                                                     |
| `build`              | Docker multi-stage, `next build`    | Confirmar que artefatos são geráveis.                                          |
| `deploy-preview`     | Vercel / Kubernetes namespace       | Criar ambiente efêmero para QA e stakeholders.                                 |
| `smoke-tests`        | `pytest -m smoke`, `playwright`     | Verificar endpoints críticos e páginas chave.                                  |

## 4. Gatekeepers Arquiteturais
- **Import Linter** configurado para bloquear dependências cíclicas entre pacotes.
- **Deptry** evita dependências órfãs ou não utilizadas.
- **Madge** (frontend) identifica ciclos de importação.
- **ArchUnit (Python)** com regras customizadas assegurando limites de camadas (`apps` não importam diretamente `glpi_contracts`).
- **Template de `pyproject.toml`** define extras opcionais (`api`, `worker`, `dev`) para evitar instalações desnecessárias.

## 5. Dados e Integridade
- **Testes de mutação** com `mutmut` (backend) e `stryker` (frontend) em _schedules_ semanais.
- **Data quality checks**: dbt ou scripts `great_expectations` rodando após ingestões completas.
- **Backfill seguro**: processos `one-shot` precisam de `dry-run` obrigatório e _toggle_ de enable/disable.
- **Schema Registry**: eventos versionados via Confluent Schema Registry ou equivalente.

## 6. Observabilidade e Alertas
- **Prometheus/Grafana**: métricas técnicas e de negócio.
- **Loki/ELK**: logs estruturados com `trace_id`.
- **Tempo real**: dashboards de ingestão (lag, throughput, retries) e API (p95 latency, error rate).
- **Alertas**: PagerDuty/Telegram integrados com thresholds definidos em `platform/docs/slo.md`.

## 7. Gestão de Configuração
- Variáveis sensíveis somente em `platform/infrastructure/secrets/` (criptografado).
- Configurações por ambiente em `config/*.yaml` carregadas via `shared.config`.
- _Feature flags_ armazenadas em provider dedicado, nunca em código.
- _Secrets_ rotacionados trimestralmente e auditados automaticamente.

## 8. Documentação Viva
- Este diretório (`refatorado/glpi_dashboard`) é espelhado no Confluence/Notion, com sincronização automática a cada merge.
- **ADR (Architecture Decision Records)** em `docs/adrs/` complementam mudanças.
- _Changelog_ automatizado com `git-cliff`.
- _Diagrams as Code_ (Structurizr, Mermaid) versionados em `docs/`.

## 9. Políticas de Deploy
- `main` sempre _deployable_.
- Deploy contínuo automatizado após aprovação manual (gate de produto).
- _Canary releases_ monitoradas por 30 minutos antes de _rollout_ completo.
- _Rollback_ automático se `error_rate > 3%` ou `lag > 10 min` pós-deploy.

## 10. Governança de Pessoas e Processos
- Reuniões semanais de arquitetura para revisar métricas e dívidas.
- _Pairing_ obrigatório para mudanças em módulos críticos (`criteria_builder`, `aggregators`, `ranking`).
- _Post-mortem_ padrão (`blameless`) para incidentes > 1h, com ações registradas em backlog.
- Capacitação contínua (trilhas internas) para GLPI API, Clean Architecture, Observabilidade.

> O não cumprimento destes guardrails bloqueia releases e deve ser tratado como incidente crítico.
