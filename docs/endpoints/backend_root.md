# Endpoint: / (Root)

## Arquivo(s) de origem
- `backend/api/routes.py` (linha ~100-120)

## Método HTTP
`GET`

## Descrição técnica
Endpoint raiz da API que retorna informações básicas sobre o serviço, incluindo status, versão e links para documentação.

## Parâmetros de entrada
Nenhum parâmetro necessário.

## Resposta esperada (contract)
```json
{
  "message": "GLPI Dashboard API v1.0",
  "status": "running",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "metrics": "/metrics",
    "docs": "/docs"
  },
  "timestamp": "2025-01-27T10:30:00Z"
}
```

## Tipagem equivalente em TypeScript
```typescript
interface RootResponse {
  message: string;
  status: string;
  version: string;
  endpoints: {
    health: string;
    metrics: string;
    docs: string;
  };
  timestamp: string;
}
```

## Dependências
- **Backend**: Flask blueprint `api_bp`
- **Frontend**: Não consumido diretamente pelos hooks
- **Variáveis de ambiente**: Nenhuma específica

## Análise técnica

### Consistência
✅ **Boa**: Endpoint informativo padrão para APIs REST

### Possíveis problemas
- ⚠️ Não há tipagem TypeScript correspondente no frontend
- ⚠️ Endpoint não é consumido pelos hooks do frontend

### Sugestões de melhorias
1. **Criar interface TypeScript**: Adicionar tipagem em `frontend/types/api.ts`
2. **Documentar no OpenAPI**: Incluir no arquivo `openapi.yaml`
3. **Adicionar informações úteis**: Incluir uptime, ambiente atual
4. **Versionamento**: Considerar incluir informações de versionamento da API

## Status de implementação
✅ **Implementado** - Funcional no backend
❌ **Não tipado** - Sem interface TypeScript no frontend
❌ **Não consumido** - Não utilizado pelos componentes frontend