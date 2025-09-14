# 🚀 Guia de Configuração do GLPI Dashboard

## 📋 Resumo do Problema Identificado

O dashboard GLPI não consegue exibir dados reais porque:
1. **Configurações do GLPI não estão definidas** (URLs e tokens)
2. **Conectividade com o servidor GLPI não foi estabelecida**
3. **Tokens de autenticação não foram configurados**

## ✅ Status Atual da Configuração

### Arquivo .env Configurado ✓
- ✅ Estrutura básica criada
- ✅ `USE_MOCK_DATA=false` (configurado para dados reais)
- ✅ Todas as variáveis necessárias definidas
- ⚠️ **Valores placeholder precisam ser substituídos**

### Integração Supabase/Vercel ✓
- ✅ **Confirmado**: A integração com Supabase/Vercel **NÃO afeta** a conectividade GLPI
- ✅ O problema é **específico da configuração GLPI**

## 🔧 Próximos Passos Obrigatórios

### 1. 🌐 Configurar URL do GLPI

Edite o arquivo `.env` e substitua:
```env
# ANTES (placeholder)
GLPI_URL=http://your-glpi-server/glpi/apirest.php

# DEPOIS (seu servidor real)
GLPI_URL=http://seu-servidor-glpi.com/apirest.php
```

### 2. 🔑 Obter e Configurar Tokens do GLPI

#### Passo 2.1: Ativar API REST no GLPI
1. Acesse seu GLPI como administrador
2. Vá em: **Configuração > Geral > API**
3. Ative a opção **"Ativar API REST"**
4. Salve as configurações

#### Passo 2.2: Gerar App Token
1. Ainda em **Configuração > Geral > API**
2. Na seção **"Clientes da API"**
3. Clique em **"Adicionar"**
4. Preencha:
   - **Nome**: `GLPI Dashboard`
   - **Ativo**: Sim
   - **IPv4 address range**: `0.0.0.0/0` (ou seu IP específico)
5. **Copie o App Token gerado**

#### Passo 2.3: Gerar User Token
1. Acesse seu **perfil de usuário** no GLPI
2. Vá na aba **"Tokens de API"**
3. Clique em **"Adicionar"**
4. Preencha:
   - **Nome**: `Dashboard Token`
   - **Ativo**: Sim
5. **Copie o User Token gerado**

#### Passo 2.4: Atualizar .env com os Tokens
```env
# Substitua pelos tokens reais obtidos
GLPI_USER_TOKEN=seu_user_token_real_aqui
GLPI_APP_TOKEN=seu_app_token_real_aqui
```

### 3. 🌐 Verificar Conectividade

#### Teste 1: Verificar URL no Navegador
1. Abra seu navegador
2. Acesse: `http://seu-servidor-glpi.com/glpi/apirest.php`
3. Deve retornar uma resposta JSON (não erro 404)

#### Teste 2: Verificar Firewall/Proxy
- Confirme que não há bloqueios de firewall
- Verifique configurações de proxy se aplicável
- Teste conectividade de rede

### 4. 🧪 Testar Configuração

Após configurar URL e tokens, execute:
```bash
cd backend
python fix_env_and_test.py
```

**Resultado esperado:**
- ✅ Conectividade GLPI: OK
- ✅ Autenticação: OK
- ✅ Dados reais disponíveis

## 🚀 Executar o Dashboard

Após configuração completa:

### Backend
```bash
cd backend
python app.py
```

### Frontend
```bash
cd frontend
npm start
```

## 🔍 Troubleshooting

### Erro: "GLPI não acessível"
- ✅ Verificar URL do GLPI
- ✅ Confirmar que o servidor está online
- ✅ Testar conectividade de rede

### Erro: "Falha na autenticação"
- ✅ Verificar App Token
- ✅ Verificar User Token
- ✅ Confirmar que API REST está ativa
- ✅ Verificar permissões do usuário

### Erro: "Dados não carregam"
- ✅ Confirmar `USE_MOCK_DATA=false`
- ✅ Verificar logs do backend
- ✅ Testar endpoints da API manualmente

## 📞 Suporte

Se ainda houver problemas:
1. Execute o diagnóstico: `python diagnose_glpi_connection.py`
2. Verifique os logs em: `logs/app.log`
3. Consulte a documentação oficial do GLPI API

---

**✨ Após seguir este guia, seu GLPI Dashboard estará funcionando com dados reais!**