# Plano de Refatoração do GLPI Dashboard

## Contexto
O estado atual do projeto acumula serviços duplicados, pastas desatualizadas e integrações fragilizadas com a API do GLPI. As tentativas recentes de reutilizar scripts da pasta `service/legacy/` evidenciaram inconsistências e baixa previsibilidade: apenas a listagem de tickets novos opera corretamente, enquanto outras funcionalidades quebram com frequência e são difíceis de manter.

## Objetivo do diretório `refatorado/glpi_dashboard`
Criar uma base documental completa antes de qualquer reescrita de código, definindo:

- visão arquitetural consolidada para backend, frontend e pipelines de dados;
- contratos bem especificados entre camadas (GLPI API ⇄ Ingestão ⇄ Backend ⇄ Frontend);
- padrões de projeto, metodologias e guardrails de qualidade para impedir novas dívidas técnicas;
- roteiro de implementação incremental garantindo preservação das consultas `criteria` do GLPI.

Todo o código futuro deverá nascer seguindo estas diretrizes, sem reutilizar automaticamente artefatos legados que não passem pela validação descrita aqui.

## Estrutura da Documentação
1. [01_Principios_Arquitetura.md](01_Principios_Arquitetura.md) — Valores, padrões e heurísticas de decisão.
2. [02_Estrutura_Pastas.md](02_Estrutura_Pastas.md) — Layout de diretórios para aplicações e pacotes compartilhados.
3. [03_Contratos_Backend.md](03_Contratos_Backend.md) — Interfaces, casos de uso e integrações GLPI.
4. [04_Contratos_Frontend.md](04_Contratos_Frontend.md) — Componentização, estado, consumo de métricas.
5. [05_Governanca_Qualidade.md](05_Governanca_Qualidade.md) — Automação, testes, observabilidade e compliance.
6. [06_Roadmap_Implementacao.md](06_Roadmap_Implementacao.md) — Sequência tática para construir o produto refatorado.

Cada documento é versionado e deve ser atualizado antes de qualquer mudança estrutural no código, mantendo este diretório como a **fonte da verdade**.

## Como usar
1. **Leitura obrigatória** para todo colaborador antes de tocar no código.
2. **Processo de RFC**: propostas de alteração devem referenciar seções específicas deste diretório e só podem ser aceitas após revisão de arquitetura.
3. **Checklist de implementação**: cada epics/tarefa só inicia quando os critérios das seções relevantes estiverem marcados como atendidos.

## Próximos passos
- Validar coletivamente os documentos e ajustar conforme feedback do time.
- Bloquear merges que não façam referência explícita às diretrizes desta pasta.
- Iniciar execução do roadmap seguindo a ordem definida em `06_Roadmap_Implementacao.md`.
