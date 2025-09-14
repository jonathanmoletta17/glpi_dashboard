# Contrato de Dados API-Dashboard

## Validação do Contrato de Dados (13/09/2025)

### 1. Endpoint: `/api/metrics`

#### Resposta da API:
```json
{
  "cached": boolean,
  "correlation_id": string,
  "data": {
    "filters_applied": null,
    "niveis": {
      "n1": { "novos": 14, "pendentes": 16, "progresso": 23, "resolvidos": 144, "total": 197 },
      "n2": { "novos": 8, "pendentes": 14, "progresso": 13, "resolvidos": 60, "total": 95 },
      "n3": { "novos": 4, "pendentes": 8, "progresso": 6, "resolvidos": 28, "total": 46 },
      "n4": { "novos": 1, "pendentes": 2, "progresso": 2, "resolvidos": 7, "total": 12 }
    },
    "novos": 27,
    "pendentes": 40,
    "progresso": 44,
    "resolvidos": 239,
    "tendencias": {
      "novos": "+15%",
      "pendentes": "-4%",
      "progresso": "+16%",
      "resolvidos": "+20%"
    },
    "timestamp": "Sat, 13 Sep 2025 05:14:37 GMT",
    "total": 350
  },
  "success": true,
  "timestamp": "2025-09-13T05:14:37.656715"
}
```

#### Interface TypeScript (frontend/types/api.ts):
```typescript
interface DashboardMetrics {
  niveis: {
    n1: LevelMetrics;
    n2: LevelMetrics;
    n3: LevelMetrics;
    n4: LevelMetrics;
    geral: LevelMetrics; // ⚠️ API NÃO RETORNA 'geral'
  };
  tendencias?: {...};
  timestamp?: string;
}
```

**❌ INCONSISTÊNCIA IDENTIFICADA:**
- Frontend espera `niveis.geral` mas API não retorna
- Frontend calcula totais somando n1+n2+n3+n4 manualmente

**✅ SOLUÇÃO IMPLEMENTADA:**
- Dashboard calcula totais somando os níveis individuais
- Não depende de `niveis.geral` da API

---

### 2. Endpoint: `/api/technicians/ranking`

#### Resposta da API (quando há dados):
```json
{
  "correlation_id": string,
  "data": [
    {
      "id": string,
      "name": string,
      "level": string,
      "rank": number,
      "total": number
    }
  ],
  "filters_applied": {...},
  "message": string,
  "success": true
}
```

#### Interface TypeScript:
```typescript
interface TechnicianRanking {
  id: string;
  name: string;
  level: string;
  rank: number;
  total: number;
  score?: number; // opcional
}
```

**✅ CONTRATO CONSISTENTE**
- Todos os campos obrigatórios estão presentes
- Campos opcionais tratados corretamente

---

### 3. Endpoint: `/api/tickets/new`

#### Resposta da API (quando há dados):
```json
{
  "data": [
    {
      "id": string,
      "title": string,
      "description": string,
      "date": string,
      "requester": string,
      "priority": string,
      "status": string
    }
  ],
  "filters_applied": {...},
  "message": string,
  "success": true
}
```

#### Interface TypeScript:
```typescript
interface NewTicket {
  id: string;
  title: string;
  description: string;
  date: string;
  requester: string;
  priority: string;
  status: string;
  level?: string; // opcional
}
```

**✅ CONTRATO CONSISTENTE**
- Todos os campos obrigatórios estão presentes
- Campo `level` é opcional

---

## Resumo da Validação

### ✅ Pontos Fortes:
1. **Estrutura geral consistente** - API e frontend seguem padrão ApiResponse
2. **Tratamento de erros robusto** - Frontend trata casos de arrays vazios
3. **Campos opcionais bem definidos** - Usando `?` no TypeScript
4. **Refresh automático** - Dados atualizados a cada 30 segundos

### ⚠️ Pontos de Atenção:
1. **niveis.geral não existe na API** - Frontend calcula manualmente (OK)
2. **Dados do GLPI offline** - Arrays vazios retornados (esperado em dev)

### 📊 Status do Contrato:
- **Métricas**: ✅ Funcionando (com cálculo manual de totais)
- **Ranking**: ✅ Contrato correto (aguardando dados)
- **Tickets**: ✅ Contrato correto (aguardando dados)

## Conclusão

O contrato de dados entre API e Dashboard está **SÓLIDO e FUNCIONAL**, com apenas uma pequena diferença no campo `niveis.geral` que é tratada adequadamente pelo frontend através de cálculo manual dos totais.