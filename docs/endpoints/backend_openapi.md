# Endpoint: /openapi.yaml

## Arquivo(s) de origem
- `backend/api/routes.py` (linha ~1580-1604)
- `backend/openapi.yaml` (arquivo de especificação)

## Método HTTP
`GET`

## Descrição técnica
Endpoint que serve a especificação OpenAPI (Swagger) da API em formato YAML, permitindo documentação automática e geração de clientes.

## Parâmetros de entrada
Nenhum parâmetro necessário.

## Resposta esperada (contract)
**Content-Type**: `application/x-yaml` ou `text/yaml`

```yaml
openapi: 3.0.3
info:
  title: GLPI Dashboard API
  description: API para dashboard de métricas e tickets do GLPI
  version: 1.0.0
  contact:
    name: Equipe de Desenvolvimento
    email: dev@empresa.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: http://localhost:5000
    description: Servidor de desenvolvimento
  - url: https://api.glpidashboard.empresa.com
    description: Servidor de produção

paths:
  /:
    get:
      summary: Informações da API
      description: Retorna informações básicas sobre a API
      responses:
        '200':
          description: Informações da API
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiInfo'
  
  /metrics:
    get:
      summary: Métricas do dashboard
      description: Retorna métricas consolidadas do GLPI
      parameters:
        - name: start_date
          in: query
          schema:
            type: string
            format: date
          description: Data inicial para filtro
        - name: end_date
          in: query
          schema:
            type: string
            format: date
          description: Data final para filtro
      responses:
        '200':
          description: Métricas obtidas com sucesso
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetricsResponse'
  
  /technicians/ranking:
    get:
      summary: Ranking de técnicos
      description: Retorna ranking de técnicos por performance
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
          description: Número máximo de técnicos
      responses:
        '200':
          description: Ranking obtido com sucesso
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RankingResponse'

components:
  schemas:
    ApiInfo:
      type: object
      properties:
        message:
          type: string
        status:
          type: string
        version:
          type: string
        endpoints:
          type: object
        timestamp:
          type: string
          format: date-time
    
    DashboardMetrics:
      type: object
      properties:
        niveis:
          $ref: '#/components/schemas/NiveisMetrics'
        total:
          type: integer
        novos:
          type: integer
        pendentes:
          type: integer
        progresso:
          type: integer
        resolvidos:
          type: integer
        data_source:
          type: string
          enum: [glpi, mock, unknown]
        is_mock_data:
          type: boolean
        timestamp:
          type: string
          format: date-time
    
    TechnicianRanking:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        level:
          type: string
          enum: [N1, N2, N3, N4, UNKNOWN]
        ticket_count:
          type: integer
        performance_score:
          type: number
        data_source:
          type: string
          enum: [glpi, mock, unknown]
        is_mock_data:
          type: boolean

  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key

security:
  - ApiKeyAuth: []
```

## Tipagem equivalente em TypeScript
```typescript
// Não aplicável - arquivo YAML de especificação
// Usado para gerar tipos TypeScript automaticamente

interface OpenAPISpec {
  openapi: string;
  info: {
    title: string;
    description: string;
    version: string;
    contact?: {
      name: string;
      email: string;
    };
    license?: {
      name: string;
      url: string;
    };
  };
  servers: Array<{
    url: string;
    description: string;
  }>;
  paths: Record<string, any>;
  components: {
    schemas: Record<string, any>;
    securitySchemes?: Record<string, any>;
  };
  security?: Array<Record<string, string[]>>;
}
```

## Dependências

### Backend
- `Flask` - Servir arquivo estático
- `send_from_directory` - Envio de arquivos
- `backend/openapi.yaml` - Arquivo de especificação

### Frontend
- **Não consumido diretamente** pelos hooks
- **Uso**: Documentação, geração de tipos, testes
- **Ferramentas**: Swagger UI, OpenAPI Generator

### Variáveis de ambiente
- `API_BASE_URL` - URL base para servidores na spec
- `API_VERSION` - Versão da API

## Análise técnica

### Consistência
✅ **Padrão OpenAPI**: Segue especificação OpenAPI 3.0.3
✅ **Documentação**: Fornece documentação estruturada
⚠️ **Completude**: Nem todos os endpoints estão documentados
⚠️ **Sincronização**: Pode ficar desatualizada com o código

### Possíveis problemas
- ⚠️ **Manutenção manual**: Especificação pode ficar desatualizada
- ⚠️ **Cobertura parcial**: Nem todos os endpoints documentados
- ⚠️ **Validação**: Não há validação automática da spec
- ⚠️ **Versionamento**: Não há controle de versão da API

### Sugestões de melhorias
1. **Geração automática**: Usar decorators para gerar spec automaticamente
2. **Validação**: Implementar validação de requests/responses
3. **Swagger UI**: Servir interface Swagger UI em `/docs`
4. **Completude**: Documentar todos os endpoints
5. **Versionamento**: Implementar versionamento da API
6. **Testes**: Usar spec para testes de contrato
7. **Geração de tipos**: Gerar tipos TypeScript automaticamente
8. **CI/CD**: Validar spec no pipeline

## Ferramentas relacionadas

### Swagger UI
```bash
# Servir documentação interativa
swagger-ui-serve openapi.yaml
```

### OpenAPI Generator
```bash
# Gerar cliente TypeScript
openapi-generator-cli generate -i openapi.yaml -g typescript-fetch -o ./generated
```

### Validação
```bash
# Validar especificação
swagger-codegen validate -i openapi.yaml
```

## Endpoints documentados
✅ `/` - Informações da API
✅ `/metrics` - Métricas do dashboard
✅ `/technicians/ranking` - Ranking de técnicos
❌ `/tickets/new` - Não documentado
❌ `/health` - Não documentado
❌ `/status` - Não documentado
❌ `/alerts` - Não documentado
❌ `/technician-performance` - Não documentado

## Schemas definidos
✅ `ApiInfo` - Informações básicas da API
✅ `DashboardMetrics` - Métricas do dashboard
✅ `TechnicianRanking` - Dados de ranking
❌ `NewTicket` - Schema não definido
❌ `SystemStatus` - Schema não definido
❌ `SystemAlert` - Schema não definido

## Status de implementação
✅ **Endpoint funcional** - Serve arquivo YAML corretamente
✅ **Especificação básica** - OpenAPI 3.0.3 válida
✅ **Schemas principais** - Tipos básicos definidos
❌ **Documentação completa** - Muitos endpoints não documentados
❌ **Swagger UI** - Interface não disponível
❌ **Geração automática** - Spec mantida manualmente
⚠️ **Sincronização** - Pode ficar desatualizada

## Próximos passos
1. **Documentar endpoints restantes**: Adicionar todos os endpoints
2. **Implementar Swagger UI**: Servir em `/docs`
3. **Automatizar geração**: Usar Flask-RESTX ou similar
4. **Validação**: Implementar validação de requests
5. **Testes de contrato**: Usar spec para testes