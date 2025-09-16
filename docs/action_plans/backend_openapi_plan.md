# Plano de Ação: Endpoint /openapi.yaml

## Insights extraídos
- Endpoint serve especificação OpenAPI v3 com caminhos principais (`/`, `/metrics`, `/technicians/ranking`), permitindo geração de clientes.【F:docs/endpoints/backend_openapi.md†L16-L164】
- A documentação destaca necessidade de manter a spec sincronizada com contrato real, incluindo autenticação via header `X-API-Key`.【F:docs/endpoints/backend_openapi.md†L95-L163】

## Lacunas identificadas
- Spec não cobre todos os endpoints existentes (ex.: `/tickets/new`, `/status`, `/alerts`, `/technician-performance`).
- Não há pipeline automatizado para validar se o YAML está consistente com código (lint, diff).
- Frontend não utiliza codegen; tipos são mantidos manualmente, aumentando risco de divergência.

## Próximas ações prioritárias
1. **Atualizar cobertura da OpenAPI**  
   - Incluir todos os endpoints documentados nas análises (`/tickets/new`, `/status`, `/health`, `/alerts`, `/technician-performance`, etc.), com parâmetros e respostas correspondentes.【F:docs/endpoints/backend_openapi.md†L51-L163】
   - Garantir descrição de códigos de erro (`4xx`, `5xx`) e schemas referenciados.
2. **Automatizar validação**  
   - Adicionar etapa de CI (ex.: `speccy` ou `openapi-cli`) para lint/validate do arquivo `openapi.yaml`.
   - Criar teste pytest que verifica existência do arquivo e resposta HTTP correta (`Content-Type` YAML, status 200).
3. **Integrar com geração de tipos**  
   - Configurar script (`npm run generate:api`) usando `openapi-typescript` ou similar para gerar tipos TS automaticamente e reduzir manutenção manual.
   - Documentar processo no README (desenvolvedores devem rodar geração após mudanças na API).

## Prompt sugerido para execução
> **Identidade**: Agente `GLPIDataIngestor` focado em documentação de API.
> **Objetivo**: Expandir e validar `openapi.yaml`, cobrindo todos os endpoints e habilitando geração automática de tipos.
> **Contexto**: Atualizar arquivo `backend/openapi.yaml`, ajustar rota `/openapi.yaml`, configurar scripts NPM/CI para lint/generate.
> **Passos**: (1) Mapear endpoints faltantes e adicionar ao YAML, (2) configurar ferramentas de validação (CI), (3) integrar codegen no frontend e atualizar README.

## Validações recomendadas
- Executar `npx @redocly/cli lint backend/openapi.yaml` (ou ferramenta equivalente) localmente e no CI.
- Rodar script `npm run generate:api` e confirmar que tipos gerados compilaram sem erros.
- Testar manualmente `curl http://localhost:5000/api/openapi.yaml` verificando cabeçalhos e conteúdo atualizado.
