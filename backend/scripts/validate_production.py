#!/usr/bin/env python3
"""
Script de validação pré-deploy para migração legacy
"""

import os
import sys
import requests
import time
from datetime import datetime

def validate_environment():
    """Valida variáveis de ambiente críticas"""
    print("🔍 Validando variáveis de ambiente...")
    
    required_vars = [
        'USE_LEGACY_SERVICES',
        'USE_MOCK_DATA', 
        'GLPI_URL',
        'GLPI_USER_TOKEN',
        'GLPI_APP_TOKEN',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variáveis ausentes: {', '.join(missing_vars)}")
        return False
    
    # Validar configurações críticas
    if os.environ.get('USE_LEGACY_SERVICES', '').lower() != 'true':
        print("❌ USE_LEGACY_SERVICES deve ser 'true' em produção")
        return False
    
    if os.environ.get('USE_MOCK_DATA', '').lower() != 'false':
        print("❌ USE_MOCK_DATA deve ser 'false' em produção")
        return False
    
    print("✅ Variáveis de ambiente validadas")
    return True

def validate_glpi_connectivity():
    """Valida conectividade com GLPI"""
    print("🔍 Validando conectividade GLPI...")
    
    glpi_url = os.environ.get('GLPI_URL')
    user_token = os.environ.get('GLPI_USER_TOKEN')
    app_token = os.environ.get('GLPI_APP_TOKEN')
    
    try:
        # Testar autenticação
        auth_url = f"{glpi_url}/initSession"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'user_token {user_token}',
            'App-Token': app_token
        }
        
        response = requests.get(auth_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            session_token = response.json().get('session_token')
            if session_token:
                print("✅ Autenticação GLPI bem-sucedida")
                
                # Testar busca de dados
                test_url = f"{glpi_url}/Ticket"
                test_headers = headers.copy()
                test_headers['Session-Token'] = session_token
                
                test_response = requests.get(
                    test_url, 
                    headers=test_headers, 
                    params={'range': '0-4'},
                    timeout=10
                )
                
                if test_response.status_code in [200, 206]:
                    data = test_response.json()
                    if isinstance(data, list) and len(data) > 0:
                        print(f"✅ Dados GLPI acessíveis ({len(data)} tickets encontrados)")
                        return True
                    else:
                        print("⚠️ GLPI acessível mas sem dados")
                        return False
                else:
                    print(f"❌ Erro ao buscar dados GLPI: {test_response.status_code}")
                    return False
            else:
                print("❌ Token de sessão não recebido")
                return False
        else:
            print(f"❌ Falha na autenticação GLPI: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conectividade GLPI: {e}")
        return False

def validate_legacy_services():
    """Valida serviços legacy"""
    print("🔍 Validando serviços legacy...")
    
    try:
        # Importar e testar LegacyServiceAdapter
        sys.path.append('/app/backend')
        from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter
        
        adapter = LegacyServiceAdapter()
        
        # Testar método principal
        start_time = time.time()
        metrics = adapter.get_dashboard_metrics('validation_test')
        response_time = time.time() - start_time
        
        if metrics and hasattr(metrics, 'total_tickets'):
            print(f"✅ Serviços legacy funcionais (tempo: {response_time:.3f}s)")
            print(f"   Total de tickets: {getattr(metrics, 'total_tickets', 'N/A')}")
            return True
        else:
            print("❌ Serviços legacy retornaram dados inválidos")
            return False
            
    except ImportError as e:
        print(f"❌ Erro ao importar LegacyServiceAdapter: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro nos serviços legacy: {e}")
        return False

def validate_application_startup():
    """Valida inicialização da aplicação"""
    print("🔍 Validando inicialização da aplicação...")
    
    try:
        # Testar import da aplicação
        sys.path.append('/app/backend')
        from backend.app import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            # Testar endpoint de saúde
            response = client.get('/api/health')
            if response.status_code == 200:
                print("✅ Aplicação inicializa corretamente")
                return True
            else:
                print(f"❌ Endpoint de saúde falhou: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        return False

def main():
    """Executa todas as validações"""
    print("🚀 Iniciando validação pré-deploy...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)
    
    validations = [
        ("Ambiente", validate_environment),
        ("GLPI", validate_glpi_connectivity),
        ("Serviços Legacy", validate_legacy_services),
        ("Aplicação", validate_application_startup)
    ]
    
    results = []
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, result))
            print()
        except Exception as e:
            print(f"❌ Erro crítico em {name}: {e}")
            results.append((name, False))
            print()
    
    print("=" * 50)
    print("📊 RESUMO DA VALIDAÇÃO:")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("🎉 TODAS AS VALIDAÇÕES PASSARAM - DEPLOY AUTORIZADO")
        sys.exit(0)
    else:
        print("🚨 VALIDAÇÕES FALHARAM - DEPLOY BLOQUEADO")
        sys.exit(1)

if __name__ == "__main__":
    main()