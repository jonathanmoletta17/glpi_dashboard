# INSTRUÇÃO PARA ANÁLISE CODEX - PROBLEMA DE ENDPOINTS RETORNANDO NULL

## CONTEXTO DO PROBLEMA

O sistema GLPI Dashboard apresenta um comportamento inconsistente onde:
- **FUNCIONA**: Endpoint de tickets novos retorna dados corretamente
- **PROBLEMA**: Outros endpoints retornam dados null ou vazios

## MISSÃO PARA O CODEX

Realize uma **AUDITORIA COMPLETA** do sistema para identificar as causas raiz do problema de endpoints retornando null e forneça correções específicas em modo de instrução.

## ÁREAS DE INVESTIGAÇÃO OBRIGATÓRIAS

### 1. ANÁLISE DE ENDPOINTS API
**Investigar:**
- Diferenças na implementação entre endpoint de tickets novos vs outros endpoints
- Parâmetros de consulta, filtros e critérios utilizados
- Estrutura de resposta da API GLPI para cada endpoint
- Validação de permissões e autenticação por endpoint

**Arquivos principais:**
- `backend/services/api_service.py`
- `backend/services/glpi_service_facade.py`
- `backend/services/trends_service.py`
- `backend/services/metrics_service.py`
- `backend/services/dashboard_service.py`

### 2. ANÁLISE DE CONFIGURAÇÕES E AUTENTICAÇÃO
**Investigar:**
- Configurações de autenticação e tokens
- Perfis de usuário e permissões no GLPI
- Headers HTTP e parâmetros de sessão
- Configurações de ambiente e variáveis

**Arquivos principais:**
- `backend/services/authentication_service.py`
- `backend/services/http_client_service.py`
- `backend/config/settings.py`
- `.env` e arquivos de configuração

### 3. ANÁLISE DE SCHEMAS E VALIDAÇÃO DE DADOS
**Investigar:**
- Schemas Pydantic para validação de resposta
- Mapeamento de campos entre API GLPI e sistema
- Transformação e serialização de dados
- Validação de tipos e estruturas

**Arquivos principais:**
- `backend/schemas/`
- `backend/models/`
- Arquivos de mapeamento de dados

### 4. ANÁLISE DE LOGS E DEBUGGING
**Investigar:**
- Logs de requisições HTTP para endpoints que falham
- Respostas brutas da API GLPI
- Códigos de status HTTP retornados
- Mensagens de erro ou warnings

**Arquivos de debug:**
- `backend/scripts/debug_*.py`
- Logs de aplicação
- Resultados de validação GLPI

### 5. ANÁLISE COMPARATIVA DE FUNCIONAMENTO
**Investigar:**
- Por que especificamente tickets novos funcionam?
- Quais são as diferenças na implementação?
- Existe algum padrão nos endpoints que falham?
- Configurações específicas para tickets novos?

## METODOLOGIA DE ANÁLISE REQUERIDA

### PASSO 1: MAPEAMENTO COMPLETO
1. **Listar TODOS os endpoints** do sistema
2. **Categorizar** por status (funcionando/falhando)
3. **Identificar padrões** nos que falham
4. **Documentar diferenças** na implementação

### PASSO 2: ANÁLISE TÉCNICA PROFUNDA
1. **Comparar código** entre endpoints funcionais e com falha
2. **Analisar fluxo de dados** completo (API → Backend → Frontend)
3. **Verificar configurações** específicas por endpoint
4. **Examinar logs** e respostas da API GLPI

### PASSO 3: IDENTIFICAÇÃO DE CAUSAS RAIZ
1. **Problemas de autenticação/autorização**
2. **Configurações incorretas de consulta**
3. **Mapeamento inadequado de dados**
4. **Validação de schemas falhando**
5. **Problemas de permissões no GLPI**
6. **Configurações de ambiente**

### PASSO 4: CORREÇÕES ESPECÍFICAS
Para cada problema identificado, forneça:
1. **Diagnóstico preciso** da causa
2. **Código de correção** específico
3. **Arquivos a serem modificados**
4. **Testes para validação**
5. **Configurações necessárias**

## FORMATO DE RESPOSTA REQUERIDO

### ESTRUTURA DO RELATÓRIO
```markdown
# RELATÓRIO DE AUDITORIA - ENDPOINTS RETORNANDO NULL

## 1. RESUMO EXECUTIVO
- Problema identificado
- Causa raiz principal
- Impacto no sistema
- Prioridade de correção

## 2. ANÁLISE DETALHADA POR ENDPOINT
### Endpoint: [Nome]
- **Status**: Funcionando/Falhando
- **Causa identificada**: [Descrição]
- **Evidências**: [Logs, código, configurações]
- **Correção necessária**: [Específica]

## 3. CORREÇÕES PRIORITÁRIAS
### Correção 1: [Título]
**Problema**: [Descrição]
**Solução**: [Código/configuração]
**Arquivos**: [Lista de arquivos]
**Teste**: [Como validar]

## 4. PLANO DE IMPLEMENTAÇÃO
1. Ordem de correções
2. Dependências entre correções
3. Testes de validação
4. Rollback se necessário

## 5. CONFIGURAÇÕES RECOMENDADAS
- Variáveis de ambiente
- Configurações GLPI
- Permissões necessárias
- Headers HTTP
```

## CRITÉRIOS DE SUCESSO

A análise será considerada completa quando:

✅ **Identificar a causa raiz** do problema de dados null
✅ **Explicar por que tickets novos funcionam** e outros não
✅ **Fornecer correções específicas** para cada endpoint
✅ **Incluir código de correção** pronto para implementação
✅ **Documentar configurações** necessárias
✅ **Prover testes de validação** para cada correção
✅ **Estabelecer ordem de prioridade** das correções

## RECURSOS DISPONÍVEIS

### Documentação Existente
- `docs/ANALISE_*.md` - Análises técnicas anteriores
- `docs/CORRECOES_*.md` - Correções já implementadas
- `BYTEROVER.md` - Handbook do projeto
- `backend/docs/GLPIHttpClientService_Improvements.md` - Melhorias recentes

### Scripts de Debug
- `backend/scripts/debug_*.py` - Scripts de debugging
- `backend/scripts/validate_glpi_debug.py` - Validação GLPI
- Resultados de validação em `backend/glpi_validation_results_*.json`

### Testes
- `tests/unit/test_http_client_service.py` - Testes do cliente HTTP
- Outros testes unitários disponíveis

## INSTRUÇÕES FINAIS

1. **SEJA ESPECÍFICO**: Não forneça soluções genéricas
2. **INCLUA CÓDIGO**: Toda correção deve ter código específico
3. **TESTE TUDO**: Cada correção deve ter teste de validação
4. **PRIORIZE**: Ordene correções por impacto e facilidade
5. **DOCUMENTE**: Explique o "porquê" de cada correção

**IMPORTANTE**: Esta análise será usada para implementação imediata das correções. Seja preciso, específico e actionável em todas as recomendações.

---

**Data de criação**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Versão**: 1.0
**Responsável**: Análise Codex ChatGPT
**Implementação**: Trae AI Assistant