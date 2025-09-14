#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Execução dos Testes de Baseline - Serviços Legacy GLPI

Script auxiliar para executar os testes de performance de forma controlada
com interface melhorada e opções de configuração.
"""

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Adicionar path do backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from legacy_performance_baseline import LegacyPerformanceBaseline
except ImportError as e:
    print(f"❌ Erro ao importar módulo de baseline: {e}")
    print("Certifique-se de que o arquivo legacy_performance_baseline.py está no mesmo diretório.")
    sys.exit(1)


def print_banner():
    """Exibe banner do programa."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🔬 GLPI Legacy Services - Performance Baseline Tool       ║
║                                                              ║
║    Estabelece baseline de performance para serviços legacy   ║
║    com testes isolados, individuais e de stress             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def check_prerequisites():
    """Verifica pré-requisitos para execução dos testes."""
    print("🔍 Verificando pré-requisitos...")
    
    # Verificar se estamos no diretório correto
    backend_path = Path(os.path.dirname(__file__)).parent
    services_path = backend_path / 'services' / 'legacy'
    
    if not services_path.exists():
        print(f"❌ Diretório de serviços legacy não encontrado: {services_path}")
        return False
    
    # Verificar arquivos essenciais
    required_files = [
        'glpi_service_facade.py',
        'authentication_service.py',
        'cache_service.py',
        'http_client_service.py',
        'metrics_service.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not (services_path / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Arquivos essenciais não encontrados: {', '.join(missing_files)}")
        return False
    
    # Verificar dependências Python
    try:
        import psutil
        import concurrent.futures
        print("✅ Dependências Python verificadas")
    except ImportError as e:
        print(f"❌ Dependência Python não encontrada: {e}")
        print("Execute: pip install psutil")
        return False
    
    print("✅ Todos os pré-requisitos atendidos")
    return True


def get_user_confirmation(test_type: str) -> bool:
    """Solicita confirmação do usuário para executar teste."""
    print(f"\n📋 Teste: {test_type}")
    response = input("Deseja executar este teste? (s/N): ").strip().lower()
    return response in ['s', 'sim', 'y', 'yes']


def run_interactive_mode():
    """Executa modo interativo com seleção de testes."""
    print("\n🎮 Modo Interativo - Selecione os testes a executar:")
    print("=" * 50)
    
    tests_config = {
        'isolated': {
            'name': 'Teste Isolado do GLPIServiceFacade',
            'description': 'Testa métodos principais individualmente',
            'duration': '~2-3 minutos'
        },
        'individual': {
            'name': 'Teste de Performance Individual',
            'description': 'Testa cada serviço separadamente',
            'duration': '~3-5 minutos'
        },
        'stress': {
            'name': 'Teste de Stress (100 requisições)',
            'description': 'Testa comportamento sob carga',
            'duration': '~5-10 minutos'
        }
    }
    
    selected_tests = []
    
    for test_key, test_info in tests_config.items():
        print(f"\n📊 {test_info['name']}")
        print(f"   📝 {test_info['description']}")
        print(f"   ⏱️ Duração estimada: {test_info['duration']}")
        
        if get_user_confirmation(test_info['name']):
            selected_tests.append(test_key)
    
    if not selected_tests:
        print("\n⚠️ Nenhum teste selecionado. Saindo...")
        return
    
    print(f"\n✅ Testes selecionados: {', '.join(selected_tests)}")
    print(f"⏱️ Duração total estimada: 5-15 minutos")
    
    if not get_user_confirmation("Iniciar execução"):
        print("\n❌ Execução cancelada pelo usuário.")
        return
    
    # Executar testes selecionados
    baseline = LegacyPerformanceBaseline()
    
    if not baseline.setup_facade():
        print("❌ Falha na inicialização do facade. Abortando.")
        return
    
    print("\n🚀 Iniciando execução dos testes selecionados...")
    start_time = time.time()
    
    try:
        if 'isolated' in selected_tests:
            print("\n" + "="*60)
            baseline.results['isolated_test'] = baseline.test_facade_isolated()
        
        if 'individual' in selected_tests:
            print("\n" + "="*60)
            baseline.results['individual_services'] = baseline.test_individual_services()
        
        if 'stress' in selected_tests:
            print("\n" + "="*60)
            baseline.results['stress_test'] = baseline.test_stress_concurrent()
        
        # Gerar relatório
        print("\n" + "="*60)
        report_path = baseline.generate_baseline_report()
        
        end_time = time.time()
        total_duration = round((end_time - start_time) / 60, 2)
        
        print("\n" + "="*60)
        print("✅ Testes concluídos com sucesso!")
        print(f"⏱️ Duração total: {total_duration} minutos")
        print(f"📊 Relatório: {report_path}")
        
        # Mostrar resumo rápido
        if 'isolated_test' in baseline.results:
            isolated = baseline.results['isolated_test']['overall_metrics']
            print(f"\n📈 Resumo Rápido:")
            print(f"   • Taxa de sucesso: {isolated.get('success_rate_percent', 0)}%")
            if 'response_time' in isolated:
                print(f"   • Tempo médio: {isolated['response_time']['avg_ms']:.1f}ms")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()


def run_full_mode():
    """Executa todos os testes automaticamente."""
    print("\n🤖 Modo Automático - Executando todos os testes...")
    print("⏱️ Duração estimada: 10-20 minutos")
    
    if not get_user_confirmation("Executar bateria completa"):
        print("\n❌ Execução cancelada pelo usuário.")
        return
    
    baseline = LegacyPerformanceBaseline()
    report_path = baseline.run_all_tests()
    
    if report_path:
        print(f"\n🎉 Bateria completa concluída!")
        print(f"📊 Relatório disponível em: {report_path}")
        
        # Abrir relatório automaticamente (opcional)
        try:
            import webbrowser
            if input("\nDeseja abrir o relatório no navegador? (s/N): ").strip().lower() in ['s', 'sim']:
                webbrowser.open(f'file://{os.path.abspath(report_path)}')
        except:
            pass
    else:
        print("\n❌ Falha na execução da bateria de testes.")


def run_quick_health_check():
    """Executa verificação rápida de saúde."""
    print("\n⚡ Verificação Rápida de Saúde...")
    print("⏱️ Duração estimada: 1-2 minutos")
    
    baseline = LegacyPerformanceBaseline()
    
    if not baseline.setup_facade():
        print("❌ Falha na inicialização. Sistema não está saudável.")
        return
    
    print("\n🔍 Testando operações básicas...")
    
    try:
        # Teste rápido de saúde
        start_time = time.time()
        
        # Testar autenticação
        auth_result = baseline.facade.authenticate()
        print(f"   {'✅' if auth_result else '❌'} Autenticação")
        
        # Testar operação básica
        health_result = baseline.facade.health_check()
        print(f"   {'✅' if health_result else '❌'} Health Check")
        
        # Testar cache
        cache_stats = baseline.facade.cache_service.get_cache_stats()
        print(f"   {'✅' if cache_stats else '❌'} Cache Service")
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        print(f"\n⏱️ Verificação concluída em {duration_ms:.1f}ms")
        
        if auth_result and health_result:
            print("\n✅ Sistema está operacional!")
            print("💡 Execute testes completos para baseline detalhado.")
        else:
            print("\n⚠️ Sistema apresenta problemas.")
            print("🔧 Verifique configurações e conectividade.")
            
    except Exception as e:
        print(f"\n❌ Erro na verificação: {e}")
        print("🔧 Sistema não está operacional.")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Executa testes de baseline de performance nos serviços legacy GLPI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python run_baseline_tests.py                    # Modo interativo
  python run_baseline_tests.py --full            # Executa todos os testes
  python run_baseline_tests.py --quick           # Verificação rápida
  python run_baseline_tests.py --check-only      # Apenas verifica pré-requisitos
"""
    )
    
    parser.add_argument(
        '--full', 
        action='store_true',
        help='Executa todos os testes automaticamente'
    )
    
    parser.add_argument(
        '--quick', 
        action='store_true',
        help='Executa apenas verificação rápida de saúde'
    )
    
    parser.add_argument(
        '--check-only', 
        action='store_true',
        help='Apenas verifica pré-requisitos sem executar testes'
    )
    
    parser.add_argument(
        '--no-banner', 
        action='store_true',
        help='Não exibe banner inicial'
    )
    
    args = parser.parse_args()
    
    # Exibir banner
    if not args.no_banner:
        print_banner()
    
    # Verificar pré-requisitos
    if not check_prerequisites():
        print("\n❌ Pré-requisitos não atendidos. Corrija os problemas e tente novamente.")
        sys.exit(1)
    
    if args.check_only:
        print("\n✅ Verificação de pré-requisitos concluída com sucesso.")
        return
    
    # Executar modo selecionado
    try:
        if args.full:
            run_full_mode()
        elif args.quick:
            run_quick_health_check()
        else:
            run_interactive_mode()
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Execução interrompida pelo usuário.")
        print("🔄 Execute novamente quando estiver pronto.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n👋 Obrigado por usar o Performance Baseline Tool!")


if __name__ == '__main__':
    main()