# Plano de Ação: Endpoint / (Root)

## Insights extraídos
- O endpoint raiz apenas fornece metadados da API e hoje não é consumido pelo frontend nem possui tipagem compartilhada.【F:docs/endpoints/backend_root.md†L9-L68】

## Lacunas identificadas
- O serviço `apiService` não expõe uma chamada `getRoot`, limitando diagnósticos rápidos pela interface.【F:frontend/services/api.ts†L10-L125】
- O arquivo de tipos não declara a interface `RootResponse`, impossibilitando validação estática do contrato citado na documentação.【F:docs/endpoints/backend_root.md†L30-L43】
- A especificação OpenAPI carece da rota raiz, dificultando geração automática de clientes.【F:docs/endpoints/backend_root.md†L59-L63】【F:docs/endpoints/backend_openapi.md†L1-L108】

## Próximas ações prioritárias
1. **Criar tipagem compartilhada**  
   - Adicionar `RootResponse` em `frontend/types/api.ts` conforme estrutura documentada.【F:docs/endpoints/backend_root.md†L30-L43】
   - Exportar o tipo para futuros hooks/testes.
2. **Disponibilizar chamada no serviço**  
   - Incluir `getRoot()` em `apiService` usando o cliente HTTP padrão, retornando `RootResponse` e reaproveitando tratamento de erro existente.【F:frontend/services/api.ts†L10-L125】
3. **Automatizar verificação de saúde**  
   - Criar teste de integração simples (Jest/Vitest) que valide status HTTP 200 e presença de campos obrigatórios.
4. **Atualizar documentação OpenAPI**  
   - Inserir a rota `/` no arquivo `openapi.yaml` e garantir exposição pelo endpoint `/openapi.yaml`.

## Prompt sugerido para execução
> **Identidade**: Você é o agente `GLPIDataIngestor` focado em alinhar contratos REST.
> **Objetivo**: Implementar o método `getRoot`, tipar `RootResponse` e atualizar `openapi.yaml` com o endpoint raiz.
> **Contexto**: Use `frontend/services/api.ts` para adicionar o método, `frontend/types/api.ts` para declarar a interface e ajuste o arquivo OpenAPI seguindo o contrato existente.
> **Passos**: (1) Criar o tipo TS, (2) adicionar método no serviço com tratamento de erro padrão, (3) documentar rota na OpenAPI, (4) escrever teste de integração básico usando Vitest.

## Validações recomendadas
- Executar `npm run test` no frontend para garantir que novos tipos e testes passam.
- Realizar `curl http://localhost:5000/api/` e comparar com a interface `RootResponse`.
- Rodar validação de lint/formatação após ajustes (`npm run lint`).
