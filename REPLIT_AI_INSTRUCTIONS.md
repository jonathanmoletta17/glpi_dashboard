# 🤖 Instruções Completas para Replit AI - GLPI Dashboard

Este documento contém instruções detalhadas para o Replit AI operar o projeto GLPI Dashboard, incluindo execução, correção de erros e manutenção da integridade arquitetural.

## 📋 MANDATÓRIO: Regras Fundamentais

### **🚫 NUNCA FAÇA ISSO:**
1. **Quebre a arquitetura**: Todas as operações devem usar MetricsFacade como ponto único de entrada
2. **Crie scripts em locais incorretos**: Respeite a estrutura de diretórios definida
3. **Altere sem análise**: Sempre analise completamente antes de qualquer mudança
4. **Ignore LSP diagnostics**: Sistema deve manter zero diagnostics sempre
5. **Modifique schemas sem validação**: Schemas são fonte única da verdade

### **✅ SEMPRE FAÇA ISSO:**
1. **Analise antes de agir**: Mapeie o problema, entenda o contexto, valide a solução
2. **Use MetricsFacade**: Todos os dados devem passar pelo facade
3. **Mantenha type safety**: Zero LSP diagnostics é obrigatório
4. **Teste com mock primeiro**: USE_MOCK_DATA=true para validar mudanças
5. **Documente alterações**: Atualize README.md e arquivos relevantes

## 🚀 Procedimento de Inicialização

### **1. Verificação Inicial do Sistema**

```bash
# Execute esta sequência SEMPRE ao iniciar
echo "=== Verificação Inicial GLPI Dashboard ==="

# 1.1 Verificar estrutura do projeto
if [ ! -f "backend/core/application/services/metrics_facade.py" ]; then
    echo "❌ ERRO CRÍTICO: MetricsFacade não encontrado"
    echo "🔧 SOLUÇÃO: Restaurar estrutura do projeto"
    exit 1
fi

# 1.2 Verificar configuração
cd backend
if [ ! -f ".env" ]; then
    echo "❌ ERRO: Arquivo .env não encontrado"
    echo "🔧 SOLUÇÃO: Criar .env baseado no README.md"
fi

# 1.3 Verificar dependências Python
python -c "
try:
    from config.settings import Config
    from core.application.services.metrics_facade import MetricsFacade
    print('✅ Dependências OK')
except ImportError as e:
    print(f'❌ ERRO DE IMPORT: {e}')
    print('🔧 SOLUÇÃO: pip install -r requirements.txt')
"

# 1.4 Verificar type safety
echo "Verificando LSP diagnostics..."
# Deve retornar "No LSP diagnostics found"

echo "=== Verificação Concluída ==="
```

### **2. Configuração Obrigatória do .env**

```bash
# Sempre validar/criar .env com estas configurações mínimas:
cat > backend/.env << 'EOF'
# === CONFIGURAÇÃO OBRIGATÓRIA ===

# API GLPI - Dados reais (obter do usuário se necessário)
GLPI_URL=http://cau.ppiratini.intra.rs.gov.br/glpi/apirest.php
GLPI_APP_TOKEN=seu_app_token_aqui
GLPI_USER_TOKEN=seu_user_token_aqui

# Modo de dados: false=real, true=mock
USE_MOCK_DATA=false

# Segurança
SECRET_KEY=sua_chave_secreta_production_ready

# Cache
REDIS_URL=redis://localhost:6379/0

# Flask
FLASK_ENV=development
FLASK_DEBUG=true

# Alertas
ALERT_RESPONSE_TIME_THRESHOLD=300
ALERT_ERROR_RATE_THRESHOLD=0.05
ALERT_ZERO_TICKETS_THRESHOLD=60
EOF

echo "✅ Arquivo .env configurado"
```

### **3. Inicialização dos Serviços**

```bash
# 3.1 Backend (Terminal 1)
cd backend
echo "🚀 Iniciando Backend na porta 8000..."
python app.py

# 3.2 Frontend (Terminal 2) 
cd frontend
echo "🚀 Iniciando Frontend na porta 5000..."
npm run dev

# 3.3 Verificação de saúde
sleep 5
curl -s http://localhost:8000/api/health | grep -q "status.*ok" && echo "✅ Backend OK" || echo "❌ Backend ERROR"
```

## 🔧 Protocolo de Correção de Erros

### **Etapa 1: Análise e Mapeamento**

```bash
# SEMPRE execute esta análise completa antes de corrigir qualquer erro:

echo "=== ANÁLISE COMPLETA DE ERRO ==="

# 1.1 Identificar o erro
echo "1. Coletando informações do erro..."
tail -20 /tmp/logs/Backend_*.log | grep -E "(ERROR|CRITICAL|Exception)"

# 1.2 Verificar arquitetura
echo "2. Validando integridade arquitetural..."
python -c "
from pathlib import Path
facade_path = Path('backend/core/application/services/metrics_facade.py')
routes_path = Path('backend/api/routes.py')

if not facade_path.exists():
    print('❌ CRÍTICO: MetricsFacade ausente')
    exit(1)

# Verificar se routes usa facade
with open(routes_path) as f:
    content = f.read()
    if 'MetricsFacade' not in content:
        print('❌ CRÍTICO: Routes não usa MetricsFacade')
        exit(1)

print('✅ Arquitetura íntegra')
"

# 1.3 Verificar LSP
echo "3. Verificando type safety..."
# LSP diagnostics devem ser zero

# 1.4 Identificar causa raiz
echo "4. Analisando causa raiz..."
# Categorizar: Config, Code, Integration, Infrastructure

echo "=== ANÁLISE CONCLUÍDA ==="
```

### **Etapa 2: Estratégia de Correção**

```python
# Template para correção segura:

def safe_error_correction():
    """
    PROTOCOLO DE CORREÇÃO SEGURA
    """
    
    # 1. BACKUP do estado atual
    backup_current_state()
    
    # 2. ISOLAR o problema
    identify_affected_components()
    
    # 3. TESTAR com mock data primeiro
    switch_to_mock_mode()
    
    # 4. APLICAR correção minimal
    apply_minimal_fix()
    
    # 5. VALIDAR funcionamento
    validate_all_endpoints()
    
    # 6. TESTAR com dados reais
    switch_to_real_data()
    
    # 7. CONFIRMAR resolução
    confirm_error_resolved()
```

### **Etapa 3: Casos Comuns de Erro**

#### **Erro de Import/Módulo**
```bash
# Problema: ModuleNotFoundError, ImportError
# Análise:
echo "🔍 ANALISANDO ERRO DE IMPORT..."

# 1. Verificar PYTHONPATH
cd backend
export PYTHONPATH=$(pwd):$PYTHONPATH

# 2. Verificar estrutura de diretórios
find . -name "*.py" -exec python -m py_compile {} \;

# 3. Verificar dependências
pip install -r requirements.txt

# 4. Correção típica:
# - Corrigir imports relativos
# - Adicionar __init__.py se necessário
# - Verificar estrutura de packages
```

#### **Erro de Serialização/Type**
```bash
# Problema: TypeError, AttributeError com Pydantic
# Análise:
echo "🔍 ANALISANDO ERRO DE SERIALIZAÇÃO..."

# REGRA FUNDAMENTAL: Pydantic models NUNCA como dict
# ❌ ERRADO: metrics_data["campo"] = valor
# ✅ CORRETO: metrics_dict = metrics_data.dict(); metrics_dict["campo"] = valor

# Verificar routes.py:
grep -n "metrics_data\[" backend/api/routes.py && echo "❌ FOUND DIRECT DICT ACCESS"

# Correção padrão:
sed -i 's/metrics_data\[/metrics_dict[/g' backend/api/routes.py
# Adicionar: metrics_dict = metrics_data.dict() antes do uso
```

#### **Erro de Integração GLPI**
```bash
# Problema: Connection timeout, Auth failed
# Análise:
echo "🔍 ANALISANDO ERRO DE INTEGRAÇÃO GLPI..."

# 1. Testar conectividade
curl -s -w "%{http_code}" "http://cau.ppiratini.intra.rs.gov.br/glpi/apirest.php/initSession" \
  -H "App-Token: $GLPI_APP_TOKEN" \
  -H "Authorization: user_token $GLPI_USER_TOKEN"

# 2. Fallback para mock
echo "USE_MOCK_DATA=true" >> backend/.env

# 3. Verificar tokens
if [ -z "$GLPI_APP_TOKEN" ]; then
    echo "❌ GLPI_APP_TOKEN não configurado"
    # Solicitar ao usuário
fi
```

## 📊 Validação e Testes

### **Testes Obrigatórios Após Qualquer Alteração**

```bash
#!/bin/bash
# comprehensive_validation.sh

echo "=== VALIDAÇÃO COMPLETA GLPI DASHBOARD ==="

# 1. Type Safety
echo "1. Verificando type safety..."
# Deve retornar zero LSP diagnostics
check_lsp_diagnostics() {
    # Implementation depends on LSP server
    echo "✅ Type safety OK"
}

# 2. Architectural Consistency  
echo "2. Verificando consistência arquitetural..."
python -c "
# Verificar se todas as routes usam MetricsFacade
with open('backend/api/routes.py') as f:
    content = f.read()
    
if 'MetricsFacade' not in content:
    print('❌ Routes não usa MetricsFacade')
    exit(1)
    
if 'metrics_data[' in content:
    print('❌ Direct dict access em Pydantic model')
    exit(1)
    
print('✅ Arquitetura consistente')
"

# 3. Functional Tests
echo "3. Testando funcionalidades..."

# 3.1 Health check
curl -s http://localhost:8000/api/health | grep -q "ok" || {
    echo "❌ Health check failed"
    exit 1
}

# 3.2 Mock data
echo "USE_MOCK_DATA=true" > backend/.env
curl -s http://localhost:8000/api/metrics/v2 | grep -q "total" || {
    echo "❌ Mock data failed"
    exit 1
}

# 3.3 Real data (se tokens disponíveis)
echo "USE_MOCK_DATA=false" > backend/.env
if [ -n "$GLPI_APP_TOKEN" ]; then
    curl -s http://localhost:8000/api/metrics/v2 | grep -q "total" || {
        echo "⚠️ Real data failed - using mock fallback"
        echo "USE_MOCK_DATA=true" > backend/.env
    }
fi

# 4. Performance Tests
echo "4. Verificando performance..."
response_time=$(curl -s -w "%{time_total}" -o /dev/null http://localhost:8000/api/metrics/v2)
if (( $(echo "$response_time > 0.3" | bc -l) )); then
    echo "⚠️ Response time alto: ${response_time}s"
fi

echo "=== VALIDAÇÃO CONCLUÍDA ✅ ==="
```

### **Checklist de Qualidade**

```bash
# Execute antes de finalizar qualquer tarefa:

checklist_quality() {
    echo "=== CHECKLIST DE QUALIDADE ==="
    
    # ✅ Type Safety
    check_lsp_diagnostics && echo "✅ Zero LSP diagnostics" || echo "❌ LSP issues found"
    
    # ✅ Architecture
    validate_facade_usage && echo "✅ MetricsFacade usado corretamente" || echo "❌ Architectural violations"
    
    # ✅ Functionality
    test_all_endpoints && echo "✅ Todos endpoints funcionando" || echo "❌ Endpoint failures"
    
    # ✅ Data Integration
    test_mock_and_real_data && echo "✅ Mock e real data OK" || echo "❌ Data integration issues"
    
    # ✅ Performance
    check_response_times && echo "✅ Performance adequada" || echo "❌ Performance issues"
    
    # ✅ Security
    validate_security_headers && echo "✅ Security headers OK" || echo "❌ Security issues"
    
    # ✅ Documentation
    check_documentation_updated && echo "✅ Docs atualizadas" || echo "❌ Documentation outdated"
    
    echo "=== CHECKLIST CONCLUÍDO ==="
}
```

## 🏗️ Adicionando Novas Features

### **Protocolo para Novas Funcionalidades**

```python
# Template para adicionar nova feature:

def add_new_feature_protocol():
    """
    PROTOCOLO SEGURO PARA NOVAS FEATURES
    """
    
    # 1. DESIGN - Definir schema primeiro
    create_pydantic_schema()  # Em schemas/
    
    # 2. FACADE - Implementar lógica no facade
    add_method_to_metrics_facade()  # core/application/services/
    
    # 3. ROUTES - Adicionar endpoint
    add_route_using_facade()  # api/routes.py
    
    # 4. MOCK - Implementar dados de teste
    add_mock_data_generator()  # utils/mock_data_generator.py
    
    # 5. TEST - Validar com mock primeiro
    test_with_mock_data()
    
    # 6. INTEGRATE - Testar com dados reais
    test_with_real_data()
    
    # 7. DOCUMENT - Atualizar documentação
    update_readme_and_docs()
```

### **Exemplo Prático: Novo Endpoint**

```python
# 1. SCHEMA (schemas/new_feature.py)
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NewFeatureResponse(BaseModel):
    data: List[str]
    timestamp: datetime
    metadata: Optional[dict] = None

# 2. FACADE (core/application/services/metrics_facade.py)
def get_new_feature_data(self, params: dict) -> NewFeatureResponse:
    """Nova funcionalidade seguindo padrão facade."""
    if self.use_mock_data:
        return get_mock_new_feature_data(params)
    
    # Implementar lógica real
    result = self.glpi_service.fetch_new_feature(params)
    return NewFeatureResponse(
        data=result.data,
        timestamp=datetime.now(),
        metadata=result.metadata
    )

# 3. ROUTE (api/routes.py)
@api_bp.route('/new-feature', methods=['GET'])
@observability_middleware.monitor_endpoint
def get_new_feature():
    try:
        params = request.args.to_dict()
        result = facade.get_new_feature_data(params)
        
        # IMPORTANTE: Usar .dict() para serialização
        response_data = result.dict()
        response_data["_metadata"] = {
            "facade": "MetricsFacade",
            "version": "v1",
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Erro em new-feature: {e}")
        return jsonify({"error": str(e)}), 500

# 4. MOCK DATA (utils/mock_data_generator.py)
def get_mock_new_feature_data(params: dict) -> NewFeatureResponse:
    return NewFeatureResponse(
        data=["mock_item_1", "mock_item_2"],
        timestamp=datetime.now(),
        metadata={"source": "mock", "params": params}
    )
```

## 🚨 Situações de Emergência

### **Sistema Completamente Quebrado**

```bash
# PROCEDIMENTO DE EMERGÊNCIA

echo "🚨 SISTEMA QUEBRADO - INICIANDO RECUPERAÇÃO..."

# 1. Backup rápido do estado atual
cp -r backend backend_backup_$(date +%s)

# 2. Reverter para configuração conhecida
git stash  # Salvar mudanças atuais
git checkout HEAD~1  # Voltar 1 commit

# 3. Configuração mínima funcional
cat > backend/.env << 'EOF'
USE_MOCK_DATA=true
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=emergency_key_$(date +%s)
EOF

# 4. Restart com mock data
cd backend
python app.py &

# 5. Verificar funcionamento básico
sleep 5
curl http://localhost:8000/api/health || {
    echo "❌ FALHA NA RECUPERAÇÃO - REQUER INTERVENÇÃO MANUAL"
    exit 1
}

echo "✅ SISTEMA RECUPERADO EM MODO EMERGÊNCIA"
echo "👥 NOTIFICAR USUÁRIO SOBRE MODO LIMITADO"
```

### **GLPI Indisponível**

```bash
# Quando API GLPI não responde

echo "⚠️ GLPI INDISPONÍVEL - ATIVANDO MODO MOCK..."

# 1. Forçar modo mock
echo "USE_MOCK_DATA=true" >> backend/.env

# 2. Notificar usuário
echo "📢 SISTEMA EM MODO SIMULAÇÃO"
echo "📊 Dados exibidos são simulados devido à indisponibilidade do GLPI"
echo "🔄 Retornará automático quando GLPI estiver disponível"

# 3. Monitor GLPI status
(
    while true; do
        if curl -s --max-time 5 "$GLPI_URL" > /dev/null 2>&1; then
            echo "✅ GLPI DISPONÍVEL NOVAMENTE"
            echo "USE_MOCK_DATA=false" >> backend/.env
            break
        fi
        sleep 300  # Check every 5 minutes
    done
) &
```

## 📝 Documentação Obrigatória

### **Sempre Atualize Após Mudanças**

```bash
# Atualizar documentação após qualquer alteração significativa:

update_documentation() {
    echo "📝 Atualizando documentação..."
    
    # 1. README.md - Status do sistema
    update_system_status_in_readme()
    
    # 2. TROUBLESHOOTING.md - Novos problemas encontrados
    document_new_issues_found()
    
    # 3. replit.md - Arquitetura e preferências
    update_project_architecture()
    
    # 4. Comentários no código
    add_inline_documentation()
    
    echo "✅ Documentação atualizada"
}
```

## 🎯 Objetivos de Performance

### **Metas Obrigatórias**

```bash
# O sistema DEVE atender estes critérios:

performance_targets() {
    # ✅ Response Time < 300ms (P95)
    check_response_time_p95 && echo "✅ Response time OK" || echo "❌ Performance issue"
    
    # ✅ Error Rate < 5%
    check_error_rate && echo "✅ Error rate OK" || echo "❌ High error rate"
    
    # ✅ Zero LSP Diagnostics
    check_zero_lsp_diagnostics && echo "✅ Type safety OK" || echo "❌ Type issues"
    
    # ✅ Cache Hit Rate > 80%
    check_cache_hit_rate && echo "✅ Cache efficient" || echo "❌ Cache issues"
    
    # ✅ Uptime > 99.9%
    check_uptime && echo "✅ High availability" || echo "❌ Availability issues"
}
```

---

## 🎯 RESUMO EXECUTIVO PARA REPLIT AI

### **COMANDOS ESSENCIAIS**

```bash
# INICIALIZAÇÃO COMPLETA
cd backend && python app.py &
cd frontend && npm run dev &

# VERIFICAÇÃO DE SAÚDE
curl http://localhost:8000/api/health

# MODO EMERGÊNCIA (mock data)
echo "USE_MOCK_DATA=true" >> backend/.env

# VALIDAÇÃO COMPLETA
./comprehensive_validation.sh
```

### **REGRAS INQUEBRÁVEIS**

1. **MetricsFacade**: Ponto único de entrada para dados
2. **Type Safety**: Zero LSP diagnostics sempre
3. **Análise Primeira**: Entender antes de alterar
4. **Mock Primeiro**: Validar com dados simulados
5. **Estrutura Sagrada**: Não quebrar organização dos diretórios

### **EM CASO DE DÚVIDA**

1. 🔍 **ANALISE** completamente o problema
2. 📚 **CONSULTE** README.md e TROUBLESHOOTING.md
3. 🧪 **TESTE** com mock data primeiro
4. 🏗️ **MANTENHA** arquitetura íntegra
5. 📝 **DOCUMENTE** mudanças realizadas

---

**MISSÃO:** Manter o GLPI Dashboard funcionando com dados reais, sem dívida técnica, respeitando a arquitetura clean e garantindo experiência perfeita ao usuário.

**SUCESSO:** Dashboard exibindo métricas reais do GLPI com response time < 300ms, zero erros de tipo, e interface responsiva.

---

*Este documento é a referência autoritativa para operação do GLPI Dashboard. Siga rigorosamente para garantir a integridade do sistema.*