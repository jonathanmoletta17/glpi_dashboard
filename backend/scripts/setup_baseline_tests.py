#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Setup para Testes de Baseline - Serviços Legacy GLPI

Configura o ambiente e instala dependências necessárias para
executar os testes de performance de baseline.
"""

import os
import subprocess
import sys
from pathlib import Path


def print_banner():
    """Exibe banner do setup."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🔧 GLPI Legacy Services - Baseline Tests Setup           ║
║                                                              ║
║    Configura ambiente para testes de performance            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def check_python_version():
    """Verifica versão do Python."""
    print("🐍 Verificando versão do Python...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} não suportado")
        print("✅ Requerido: Python 3.8 ou superior")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True


def check_pip():
    """Verifica se pip está disponível."""
    print("📦 Verificando pip...")
    
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip não encontrado")
        print("💡 Instale pip: python -m ensurepip --upgrade")
        return False


def install_dependencies():
    """Instala dependências necessárias."""
    print("\n📚 Instalando dependências...")
    
    requirements_file = Path(__file__).parent / 'requirements_baseline.txt'
    
    if not requirements_file.exists():
        print(f"❌ Arquivo de requisitos não encontrado: {requirements_file}")
        return False
    
    try:
        print(f"📥 Instalando a partir de: {requirements_file}")
        
        # Instalar dependências
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ], capture_output=True, text=True, check=True)
        
        print("✅ Dependências instaladas com sucesso")
        
        # Mostrar pacotes instalados
        if result.stdout:
            print("\n📋 Saída da instalação:")
            for line in result.stdout.split('\n')[-10:]:  # Últimas 10 linhas
                if line.strip():
                    print(f"   {line}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na instalação: {e}")
        if e.stderr:
            print(f"💬 Detalhes: {e.stderr}")
        return False


def verify_installation():
    """Verifica se as dependências foram instaladas corretamente."""
    print("\n🔍 Verificando instalação...")
    
    required_packages = [
        'psutil',
        'numpy', 
        'matplotlib',
        'pandas',
        'tabulate'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\n⚠️ Pacotes com falha: {', '.join(failed_imports)}")
        print("💡 Tente reinstalar: pip install " + ' '.join(failed_imports))
        return False
    
    print("\n✅ Todas as dependências verificadas com sucesso")
    return True


def check_project_structure():
    """Verifica estrutura do projeto."""
    print("\n🏗️ Verificando estrutura do projeto...")
    
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    services_dir = backend_dir / 'services' / 'legacy'
    
    # Verificar diretórios
    directories = {
        'Backend': backend_dir,
        'Services': backend_dir / 'services',
        'Legacy Services': services_dir
    }
    
    for name, path in directories.items():
        if path.exists():
            print(f"   ✅ {name}: {path}")
        else:
            print(f"   ❌ {name}: {path} (não encontrado)")
            return False
    
    # Verificar arquivos essenciais
    essential_files = [
        'glpi_service_facade.py',
        'authentication_service.py',
        'cache_service.py',
        'http_client_service.py'
    ]
    
    print("\n📁 Verificando arquivos essenciais:")
    missing_files = []
    
    for file in essential_files:
        file_path = services_dir / file
        if file_path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️ Arquivos não encontrados: {', '.join(missing_files)}")
        print("💡 Certifique-se de estar no diretório correto do projeto")
        return False
    
    return True


def create_test_config():
    """Cria arquivo de configuração para os testes."""
    print("\n⚙️ Criando configuração de testes...")
    
    config_content = """
# Configuração para Testes de Baseline - Serviços Legacy GLPI
# Este arquivo pode ser modificado para ajustar parâmetros dos testes

[DEFAULT]
# Configurações gerais
test_timeout_seconds = 300
max_retries = 3
log_level = INFO

[isolated_test]
# Teste isolado do GLPIServiceFacade
enabled = true
methods_to_test = get_dashboard_metrics,get_ticket_count,get_metrics_by_level,get_general_metrics,health_check
expected_ticket_count_min = 10000

[individual_test]
# Testes individuais por serviço
enabled = true
test_cache_hit_rate = true
test_http_latency = true
test_authentication = true

[stress_test]
# Teste de stress
enabled = true
concurrent_requests = 100
max_workers = 20
failure_threshold_percent = 10
response_time_threshold_ms = 5000
cpu_threshold_percent = 80
memory_threshold_mb = 500

[reporting]
# Configurações de relatório
generate_json = true
generate_markdown = true
include_graphs = false
open_report_automatically = false

[thresholds]
# Limites para classificação de performance
excellent_success_rate = 95
good_success_rate = 90
fair_success_rate = 80
excellent_response_time_ms = 1000
good_response_time_ms = 2000
fair_response_time_ms = 5000
"""
    
    config_path = Path(__file__).parent / 'baseline_config.ini'
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ Configuração criada: {config_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar configuração: {e}")
        return False


def show_next_steps():
    """Mostra próximos passos após setup."""
    print("\n" + "="*60)
    print("🎉 Setup concluído com sucesso!")
    print("\n📋 Próximos passos:")
    print("\n1. 🚀 Executar testes:")
    print("   python run_baseline_tests.py")
    print("\n2. ⚡ Verificação rápida:")
    print("   python run_baseline_tests.py --quick")
    print("\n3. 🤖 Bateria completa:")
    print("   python run_baseline_tests.py --full")
    print("\n4. 📊 Configurar testes:")
    print("   Edite: baseline_config.ini")
    print("\n💡 Dicas:")
    print("   • Execute primeiro --quick para verificar conectividade")
    print("   • Use modo interativo para testes seletivos")
    print("   • Bateria completa pode levar 10-20 minutos")
    print("\n" + "="*60)


def main():
    """Função principal do setup."""
    print_banner()
    
    print("🔧 Iniciando configuração do ambiente...\n")
    
    # Verificações básicas
    if not check_python_version():
        sys.exit(1)
    
    if not check_pip():
        sys.exit(1)
    
    if not check_project_structure():
        print("\n❌ Estrutura do projeto inválida")
        print("💡 Execute este script a partir do diretório: backend/scripts/")
        sys.exit(1)
    
    # Instalação
    print("\n" + "="*50)
    if not install_dependencies():
        print("\n❌ Falha na instalação das dependências")
        sys.exit(1)
    
    # Verificação
    if not verify_installation():
        print("\n❌ Falha na verificação das dependências")
        sys.exit(1)
    
    # Configuração
    if not create_test_config():
        print("\n⚠️ Falha ao criar configuração (não crítico)")
    
    # Sucesso
    show_next_steps()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado durante setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)