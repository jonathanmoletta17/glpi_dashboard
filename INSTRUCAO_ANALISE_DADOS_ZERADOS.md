# Instrução para Análise de Dados Zerados - Consulta ao Projeto Similar

## Contexto do Problema

Estou enfrentando um problema no meu dashboard GLPI onde os dados retornam com valores zerados:
- `ticket_count: 0` para todos os técnicos
- `performance_score: null` para todos os técnicos
- `data_source: "unknown"` em todos os registros

O endpoint `/api/technicians/ranking` está funcionando e retornando técnicos, mas com métricas vazias.

## Pergunta para a IA do Projeto Similar

**"Preciso de sua ajuda para diagnosticar um problema de dados zerados no meu dashboard GLPI. Meu endpoint está retornando técnicos mas com ticket_count=0 e performance_score=null. Com base na sua experiência, quais são os pontos críticos que devo analisar para identificar e corrigir essas inconsistências? Por favor, me forneça um checklist detalhado cobrindo:**

### 1. Análise da Fonte de Dados
- Como verificar se a conexão com o banco GLPI está correta?
- Quais tabelas do GLPI são essenciais para contagem de tickets?
- Como validar se os IDs dos técnicos estão corretos?
- Que queries SQL devo executar para testar diretamente no banco?

### 2. Análise das Queries e Filtros
- Quais são os filtros mais comuns que podem zerar resultados?
- Como debuggar queries que retornam dados vazios?
- Que campos de data/período são críticos para contagem de tickets?
- Como verificar se os JOINs entre tabelas estão corretos?

### 3. Análise da Lógica de Negócio
- Que regras de negócio podem estar filtrando todos os tickets?
- Como verificar se os status de tickets estão sendo considerados?
- Que tipos de tickets devem ser incluídos na contagem?
- Como validar se os cálculos de performance estão corretos?

### 4. Análise de Configuração
- Quais configurações do GLPI podem afetar a visibilidade dos dados?
- Como verificar permissões de usuário/entidade no GLPI?
- Que variáveis de ambiente são críticas para o funcionamento?
- Como validar se o cache não está interferindo?

### 5. Debugging Técnico
- Que logs específicos devo ativar para rastrear o problema?
- Como testar as queries diretamente no banco de dados?
- Que ferramentas de debug você recomenda?
- Como validar se os dados existem no GLPI mas não estão sendo recuperados?

### 6. Testes de Validação
- Como criar testes para verificar a integridade dos dados?
- Que cenários de teste devo implementar?
- Como comparar os resultados com o GLPI diretamente?
- Que métricas devo monitorar para detectar problemas futuros?

**Por favor, seja específico e inclua exemplos de código, queries SQL e comandos que posso executar para diagnosticar cada ponto. Preciso de um plano de ação passo-a-passo para resolver esse problema de dados zerados."**

---

## Como Usar Esta Instrução

1. Copie a pergunta acima
2. Cole na conversa com a IA do projeto similar
3. Analise a resposta detalhada
4. Implemente as sugestões de debugging
5. Execute os testes recomendados
6. Documente os achados para correção

## Informações Adicionais do Contexto

- **Arquitetura**: Legacy Service Adapter + GLPI Service Facade
- **Endpoint problemático**: `/api/technicians/ranking`
- **Sintomas**: Dados retornam mas com métricas zeradas
- **Status**: Conexão funcionando, técnicos sendo listados
- **Cache**: Ativo (cached: true no retorno)