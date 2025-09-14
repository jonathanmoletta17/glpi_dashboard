# 🔧 Guia de Troubleshooting - GLPI Dashboard

Este guia contém soluções para problemas comuns encontrados durante o desenvolvimento e operação do GLPI Dashboard.

## 🚨 Problemas Críticos

### **Backend não inicia**

**Sintomas:**
- Erro ao executar `python app.py`
- Falha na importação de módulos
- Erro de configuração

**Soluções:**

1. **Verificar dependências:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Verificar arquivo .env:**
```bash
# Deve existir e conter pelo menos:
GLPI_URL=http://seu-glpi.com/apirest.php
GLPI_APP_TOKEN=seu_token
GLPI_USER_TOKEN=seu_token
USE_MOCK_DATA=true  # Para testar sem API real
```

3. **Verificar Python version:**
```bash
python --version  # Deve ser 3.11+
```

### **Erro de conexão com GLPI**

**Sintomas:**
- Timeout errors
- Authentication failed
- Connection refused

**Soluções:**

1. **Testar conexão manual:**
```bash
curl -X GET "http://seu-glpi.com/apirest.php/initSession" \
  -H "Content-Type: application/json" \
  -H "App-Token: SEU_APP_TOKEN" \
  -H "Authorization: user_token SEU_USER_TOKEN"
```

2. **Usar modo mock temporariamente:**
```bash
# No .env
USE_MOCK_DATA=true
```

3. **Verificar firewall/proxy:**
- Confirme que a URL GLPI está acessível
- Verifique se não há proxy bloqueando

### **Erro 500 Internal Server Error**

**Sintomas:**
- Endpoints retornam HTTP 500
- Erro de serialização
- TypeError em logs

**Soluções:**

1. **Verificar logs:**
```bash
tail -f /tmp/logs/Backend_*.log | grep ERROR
```

2. **Restart o backend:**
```bash
cd backend
python app.py
```

3. **Verificar LSP diagnostics:**
```bash
# Deve retornar "No LSP diagnostics found"
# Se houver erros, o sistema não funcionará corretamente
```

## ⚠️ Problemas Comuns

### **Frontend não conecta com Backend**

**Sintomas:**
- Errors de CORS
- Network errors
- API calls failing

**Soluções:**

1. **Verificar se backend está rodando:**
```bash
curl http://localhost:8000/api/health
```

2. **Verificar CORS:**
```python
# Em config/settings.py deve ter:
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5000",
    "http://127.0.0.1:3000", 
    "http://127.0.0.1:5000"
]
```

3. **Verificar porta do frontend:**
- Frontend deve rodar na porta 5000
- Backend deve rodar na porta 8000

### **Cache não funciona**

**Sintomas:**
- Respostas sempre lentas
- Dados não são cached
- Redis connection errors

**Soluções:**

1. **Verificar Redis:**
```bash
redis-cli ping  # Deve retornar PONG
```

2. **Verificar configuração:**
```bash
# No .env deve ter:
REDIS_URL=redis://localhost:6379/0
```

3. **Restart Redis:**
```bash
redis-server
```

### **Mock Data não funciona**

**Sintomas:**
- Erro ao gerar dados mock
- Dados sempre vazios
- Inconsistência nos dados

**Soluções:**

1. **Verificar configuração:**
```bash
# No .env:
USE_MOCK_DATA=true
```

2. **Testar mock data diretamente:**
```bash
cd backend
python -c "
from utils.mock_data_generator import get_mock_dashboard_metrics
print(get_mock_dashboard_metrics())
"
```

3. **Verificar imports:**
- Certifique-se que `utils.mock_data_generator` está acessível

## 🔍 Debugging Avançado

### **Logs Estruturados**

**Localização dos logs:**
```bash
# Logs principais
/tmp/logs/Backend_*.log

# Logs específicos do workflow
tail -f /tmp/logs/Backend_$(date +%Y%m%d)*.log
```

**Filtrar logs por tipo:**
```bash
# Apenas erros
grep "ERROR" /tmp/logs/Backend_*.log

# Performance issues
grep "duration_seconds" /tmp/logs/Backend_*.log | grep -E "[1-9]\."

# Cache operations
grep "cache" /tmp/logs/Backend_*.log
```

### **Performance Issues**

**Sintomas:**
- Response time > 300ms
- Timeouts frequentes
- Alta CPU usage

**Diagnóstico:**

1. **Verificar métricas:**
```bash
curl http://localhost:8000/api/metrics/v2 | grep -E "(duration|response_time)"
```

2. **Verificar cache hit rate:**
```bash
redis-cli info stats | grep keyspace
```

3. **Profile de performance:**
```bash
# Adicionar timing nos logs
grep "api_request_duration" /tmp/logs/Backend_*.log | tail -20
```

**Soluções:**
- Aumentar timeout de cache
- Otimizar queries GLPI
- Implementar cache warming

### **Memory Issues**

**Sintomas:**
- Out of memory errors
- Gradual degradação
- High memory usage

**Diagnóstico:**
```bash
# Monitor memory usage
free -m

# Check Python processes
ps aux | grep python
```

**Soluções:**
- Restart backend periodicamente
- Implementar garbage collection
- Otimizar estruturas de dados

## 🧪 Testes de Validação

### **Health Check Completo**

```bash
#!/bin/bash
# health_check.sh

echo "=== GLPI Dashboard Health Check ==="

# 1. Backend alive
echo "1. Checking backend..."
curl -s http://localhost:8000/api/health || echo "❌ Backend down"

# 2. Mock data
echo "2. Testing mock data..."
curl -s "http://localhost:8000/api/metrics/v2" | grep -q "total" && echo "✅ Mock data OK" || echo "❌ Mock data failed"

# 3. Cache
echo "3. Checking cache..."
redis-cli ping | grep -q "PONG" && echo "✅ Redis OK" || echo "❌ Redis down"

# 4. Config
echo "4. Validating config..."
cd backend && python -c "from config.settings import Config; print('✅ Config OK')" || echo "❌ Config invalid"

echo "=== Health Check Complete ==="
```

### **Load Testing**

```bash
# Teste de carga simples
for i in {1..50}; do
  curl -s http://localhost:8000/api/metrics/v2 > /dev/null &
done
wait
echo "Load test complete"
```

### **Integration Testing**

```bash
# Teste completo da API
echo "Testing all endpoints..."

endpoints=(
  "/api/"
  "/api/health"  
  "/api/metrics"
  "/api/metrics/v2"
  "/api/technicians/ranking"
)

for endpoint in "${endpoints[@]}"; do
  status=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8000$endpoint")
  if [ "$status" = "200" ]; then
    echo "✅ $endpoint"
  else
    echo "❌ $endpoint (HTTP $status)"
  fi
done
```

## 📋 Checklist de Deploy

### **Pré-deploy**
- [ ] Todos os testes passando
- [ ] Zero LSP diagnostics
- [ ] Configuração de produção validada
- [ ] Secrets configurados
- [ ] Cache funcionando
- [ ] Logs estruturados ativos

### **Deploy**
- [ ] Backup do sistema anterior
- [ ] Deploy do backend primeiro
- [ ] Verificar health checks
- [ ] Deploy do frontend
- [ ] Smoke tests completos
- [ ] Monitoramento ativo

### **Pós-deploy**
- [ ] Verificar métricas de performance
- [ ] Confirmar integração GLPI
- [ ] Validar dados em tempo real
- [ ] Monitor por 24h
- [ ] Rollback plan ready

## 🚑 Emergency Procedures

### **Sistema Completamente Down**

1. **Immediate Actions:**
```bash
# Restart all services
cd backend && python app.py &
cd frontend && npm run dev &
```

2. **Enable Mock Mode:**
```bash
echo "USE_MOCK_DATA=true" >> backend/.env
```

3. **Check Dependencies:**
```bash
redis-cli ping
curl http://localhost:8000/api/health
```

### **GLPI API Down**

1. **Switch to Mock Mode:**
```bash
# In .env
USE_MOCK_DATA=true
```

2. **Notify Users:**
- Dashboard will show simulated data
- Real data will resume when GLPI is back

3. **Monitor GLPI Status:**
```bash
# Check every 5 minutes
while true; do
  curl -s "http://seu-glpi.com/apirest.php" && break
  sleep 300
done
```

### **High Error Rate**

1. **Check Error Types:**
```bash
grep "ERROR" /tmp/logs/Backend_*.log | tail -20
```

2. **Common Fixes:**
- Restart backend
- Clear cache: `redis-cli flushall`
- Check GLPI connectivity
- Verify config

3. **Scale Down:**
- Reduce request frequency
- Increase cache timeouts
- Enable circuit breaker

---

## 📞 Contato para Suporte

**Para problemas não cobertos neste guia:**

1. **Collect Information:**
   - Error logs from `/tmp/logs/`
   - Configuration from `.env` (without secrets)
   - Steps to reproduce
   - Expected vs actual behavior

2. **Create Issue:**
   - Include all collected information
   - Mark severity level
   - Provide reproducer if possible

3. **Emergency Contact:**
   - For production down situations
   - Include system status and immediate impact

---

**Last Updated:** September 2025  
**Version:** 1.0  
**Compatibility:** GLPI Dashboard v2.0+