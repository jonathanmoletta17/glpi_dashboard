# 01 — Princípios de Arquitetura

## 1. Valores Fundamentais
1. **Domínio primeiro**: entidades e regras de negócio do Service Desk (Ticket, Técnico, Fila, SLA, Categoria, Atendimento) vivem em módulos independentes de framework.
2. **Isolamento de integrações**: qualquer comunicação com a API GLPI, cache, filas ou storage externo ocorre por meio de _adapters_ plugáveis.
3. **Fluxo de dados mensurável**: cada métrica exposta no dashboard deve ter rastreabilidade ponta a ponta (GLPI → ingestão → agregação → API → UI).
4. **Observabilidade como requisito**: logs estruturados, métricas técnicas e rastreamento distribuído são obrigatórios para detectar regressões cedo.
5. **Contrato explícito**: não há acesso direto a modelos ou serviços de outra camada sem passar por interfaces públicas revisadas.

## 2. Estilo Arquitetural
- **Clean Architecture + Ports & Adapters**: domínio no centro, seguido de casos de uso, interfaces, infraestrutura e apresentação.
- **Hexagonal Services**: cada módulo expõe portas de entrada (casos de uso) e portas de saída (repositórios/adapters) com dependência invertida.
- **Event-driven para ingestão**: os workers traduzem eventos GLPI (ticket criado, atualizado, encerrado) para mensagens internas, permitindo reprocessamento idempotente.
- **GraphQL federado / REST curado**: a API pública oferece endpoints normalizados, enquanto um gateway interno pode expor GraphQL para agregações complexas.

## 3. Padrões de Projeto Obrigatórios
| Camada                | Padrões aplicáveis                                                                 | Objetivo                                                                 |
|-----------------------|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| Domínio               | Value Objects, Aggregate Roots, Domain Services                                     | Garantir invariantes (SLA, estados do ticket) e reduzir repetição.       |
| Aplicação (casos uso) | Command Handler, Query Handler, DTOs                                               | Orquestrar fluxos sem lidar com detalhes técnicos.                       |
| Infraestrutura        | Adapter, Repository, Gateway, Strategy, Circuit Breaker, Retry with backoff        | Encapsular GLPI, caches, filas e fontes analíticas.                      |
| Frontend              | Container/Presenter, Hooks especializados, Componentes Dumb/Smart, Atomic Design   | Separar lógica de dados de UI e garantir reuso consistente.              |

## 4. Heurísticas de Decisão
- **Adicionar dependência externa** somente se reduzir substancialmente o esforço total e existir plano de atualização/monitoramento.
- **Preferir configuração declarativa** (YAML/TOML/JSON) a _hardcode_, facilitando testes e _feature flags_.
- **Evitar acoplamento temporal**: processos assíncronos devem ter _timeouts_, retries e _dead-letter queues_.
- **Pensar em _failure modes_**: para cada caso de uso, documentar comportamento em quedas do GLPI, lentidão de rede e dados inconsistentes.
- **Priorizar simplicidade progressiva**: começar com o mínimo necessário, mas com espaço para escalar (ex.: usar Redis para cache, mas encapsulado para eventual troca).

## 5. Gestão de Dependências
1. **Camadas podem depender apenas de interfaces dos níveis internos**.
2. **Bibliotecas comuns** vivem em `packages/` e expõem APIs versionadas (`semantic versioning` interno).
3. **Feature Flags** controlam ativações graduais, evitando "big bang".
4. **Não existe import relativo atravessando limites de contexto**: comunicação sempre via casos de uso ou eventos.

## 6. Segurança e Compliance
- Armazenamento seguro de _secrets_ em `Vault`/`AWS Secrets Manager` (ou equivalente), carregados via variáveis de ambiente.
- Tokens GLPI renovados com _refresh schedulers_ monitorados.
- Sanitização e _rate limiting_ na API pública.
- Auditoria de acesso às métricas sensíveis (SLA, produtividade individual) com _trails_ imutáveis.

## 7. Estratégia de Evolução
- **Refatorar com propósito**: qualquer alteração estrutural requer RFC documentada aqui.
- **Testes de mutação** para garantir robustez de regras críticas (cálculo de SLA, ranking).
- **Playbooks de rollback**: cada deploy possui instruções de reversão e _feature toggles_ associados.
- **Métricas de arquitetura**: acompanhar _cycle time_, _deploy frequency_, _mean time to restore_ e _change fail percentage_.

> Estes princípios são vinculantes para toda a equipe. Divergências devem ser registradas em RFC antes de qualquer implementação.
