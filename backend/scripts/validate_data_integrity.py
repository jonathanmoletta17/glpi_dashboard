#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador de Integridade de Dados - Serviços Legacy GLPI

Este script valida a integridade dos dados dos tickets GLPI,
confirmando a contagem de 10.240 tickets mencionada nos requisitos.

Autor: Performance Baseline Tool
Data: 2025-09-14
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Adicionar o diretório raiz ao path para imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from services.legacy import GLPIServiceFacade
    from config.settings import active_config
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("Certifique-se de que está executando do diretório backend/")
    sys.exit(1)

class DataIntegrityValidator:
    """
    Validador de integridade dos dados GLPI.
    """
    
    def __init__(self):
        """
        Inicializa o validador.
        """
        self.facade = None
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'total_tickets_found': 0,
            'expected_tickets': 10240,
            'integrity_check': False,
            'validation_details': {},
            'errors': []
        }
    
    def initialize_facade(self) -> bool:
        """
        Inicializa o GLPIServiceFacade.
        
        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            print("🔧 Inicializando GLPIServiceFacade...")
            self.facade = GLPIServiceFacade()
            print("✅ GLPIServiceFacade inicializado com sucesso")
            return True
        except Exception as e:
            error_msg = f"Erro ao inicializar GLPIServiceFacade: {e}"
            print(f"❌ {error_msg}")
            self.validation_results['errors'].append(error_msg)
            return False
    
    def validate_tickets_count(self) -> bool:
        """
        Valida a contagem total de tickets.
        
        Returns:
            bool: True se a contagem estiver correta
        """
        try:
            print("📊 Validando contagem de tickets...")
            
            # Tentar obter contagem de tickets através do facade
            tickets_data = self.facade.get_ticket_count()
            
            if tickets_data and isinstance(tickets_data, dict):
                # Verificar diferentes possíveis estruturas de retorno
                total_count = 0
                if 'total_count' in tickets_data:
                    total_count = tickets_data['total_count']
                elif 'totalcount' in tickets_data:
                    total_count = tickets_data['totalcount']
                elif 'count' in tickets_data:
                    total_count = tickets_data['count']
                elif isinstance(tickets_data.get('data'), list):
                    total_count = len(tickets_data['data'])
                
                self.validation_results['total_tickets_found'] = total_count
                self.validation_results['validation_details'] = {
                    'total_count_reported': total_count,
                    'expected_count': 10240,
                    'count_matches_expected': total_count == 10240,
                    'data_structure_valid': True,
                    'raw_response_keys': list(tickets_data.keys()) if isinstance(tickets_data, dict) else []
                }
                
                print(f"📈 Total de tickets encontrados: {total_count}")
                print(f"🎯 Esperado: {self.validation_results['expected_tickets']}")
                print(f"📋 Estrutura de resposta: {list(tickets_data.keys()) if isinstance(tickets_data, dict) else 'N/A'}")
                
                if total_count == 10240:
                    print("✅ Contagem de tickets VALIDADA - 10.240 tickets confirmados")
                    self.validation_results['integrity_check'] = True
                    return True
                elif total_count > 0:
                    print(f"⚠️ Contagem divergente: encontrados {total_count}, esperados 10.240")
                    print("ℹ️ Sistema funcional, mas contagem não corresponde aos requisitos")
                    return False
                else:
                    print("❌ Nenhum ticket encontrado")
                    return False
            else:
                error_msg = f"Dados de tickets inválidos ou não encontrados: {type(tickets_data)}"
                print(f"❌ {error_msg}")
                self.validation_results['errors'].append(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Erro ao validar contagem de tickets: {e}"
            print(f"❌ {error_msg}")
            self.validation_results['errors'].append(error_msg)
            return False
    
    def validate_data_structure(self) -> bool:
        """
        Valida a estrutura dos dados retornados através das métricas do dashboard.
        
        Returns:
            bool: True se a estrutura estiver válida
        """
        try:
            print("🔍 Validando estrutura dos dados...")
            
            # Obter métricas do dashboard para validar estrutura
            dashboard_data = self.facade.get_dashboard_metrics()
            
            if not dashboard_data or not isinstance(dashboard_data, dict):
                error_msg = "Dados do dashboard não encontrados ou estrutura inválida"
                print(f"❌ {error_msg}")
                self.validation_results['errors'].append(error_msg)
                return False
            
            structure_validation = {
                'dashboard_data_available': True,
                'dashboard_keys': list(dashboard_data.keys()),
                'has_metrics': len(dashboard_data) > 0,
                'structure_valid': True
            }
            
            # Validar se existem métricas essenciais
            expected_metrics = ['total_tickets', 'open_tickets', 'closed_tickets']
            metrics_found = []
            
            for metric in expected_metrics:
                if metric in dashboard_data:
                    metrics_found.append(metric)
            
            structure_validation['expected_metrics_found'] = metrics_found
            structure_validation['metrics_coverage'] = len(metrics_found) / len(expected_metrics)
            
            self.validation_results['validation_details']['structure_validation'] = structure_validation
            
            print(f"✅ Estrutura de dados validada")
            print(f"📊 Métricas encontradas: {metrics_found}")
            print(f"📈 Cobertura de métricas: {structure_validation['metrics_coverage']:.1%}")
            
            return True
            
        except Exception as e:
            error_msg = f"Erro ao validar estrutura de dados: {e}"
            print(f"❌ {error_msg}")
            self.validation_results['errors'].append(error_msg)
            return False
    
    def validate_dashboard_metrics(self) -> bool:
        """
        Valida as métricas do dashboard.
        
        Returns:
            bool: True se as métricas estiverem válidas
        """
        try:
            print("📊 Validando métricas do dashboard...")
            
            metrics = self.facade.get_dashboard_metrics()
            
            if metrics:
                metrics_validation = {
                    'metrics_available': True,
                    'metrics_structure': type(metrics).__name__,
                    'metrics_content': str(metrics)[:200] + '...' if len(str(metrics)) > 200 else str(metrics)
                }
                
                self.validation_results['validation_details']['metrics_validation'] = metrics_validation
                
                print("✅ Métricas do dashboard validadas")
                return True
            else:
                print("⚠️ Métricas do dashboard não disponíveis")
                return False
                
        except Exception as e:
            error_msg = f"Erro ao validar métricas do dashboard: {e}"
            print(f"❌ {error_msg}")
            self.validation_results['errors'].append(error_msg)
            return False
    
    def run_full_validation(self) -> dict:
        """
        Executa validação completa de integridade.
        
        Returns:
            dict: Resultados da validação
        """
        print("🔍 Iniciando Validação de Integridade de Dados")
        print("=" * 50)
        
        # 1. Inicializar facade
        if not self.initialize_facade():
            return self.validation_results
        
        # 2. Validar contagem de tickets
        tickets_valid = self.validate_tickets_count()
        
        # 3. Validar estrutura de dados
        structure_valid = self.validate_data_structure()
        
        # 4. Validar métricas do dashboard
        metrics_valid = self.validate_dashboard_metrics()
        
        # Resultado final
        overall_valid = tickets_valid and structure_valid and metrics_valid
        
        self.validation_results['overall_validation'] = {
            'tickets_count_valid': tickets_valid,
            'data_structure_valid': structure_valid,
            'metrics_valid': metrics_valid,
            'overall_success': overall_valid
        }
        
        print("\n" + "=" * 50)
        if overall_valid:
            print("✅ VALIDAÇÃO COMPLETA: Todos os testes passaram")
            print(f"✅ CONFIRMADO: {self.validation_results['total_tickets_found']} tickets validados")
        else:
            print("❌ VALIDAÇÃO FALHOU: Alguns testes não passaram")
        
        return self.validation_results
    
    def save_validation_report(self) -> str:
        """
        Salva o relatório de validação em arquivo JSON.
        
        Returns:
            str: Caminho do arquivo salvo
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_integrity_validation_{timestamp}.json"
            filepath = Path(__file__).parent / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Relatório de validação salvo: {filename}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Erro ao salvar relatório: {e}")
            return ""

def main():
    """
    Função principal para executar a validação.
    """
    print("🔍 Validador de Integridade de Dados - Legacy GLPI Services")
    print("=" * 60)
    
    validator = DataIntegrityValidator()
    results = validator.run_full_validation()
    
    # Salvar relatório
    report_path = validator.save_validation_report()
    
    # Resumo final
    print("\n📋 RESUMO DA VALIDAÇÃO:")
    print(f"   • Total de tickets: {results['total_tickets_found']}")
    print(f"   • Esperado: {results['expected_tickets']}")
    print(f"   • Integridade: {'✅ VÁLIDA' if results['integrity_check'] else '❌ INVÁLIDA'}")
    
    if results['errors']:
        print(f"   • Erros encontrados: {len(results['errors'])}")
        for error in results['errors']:
            print(f"     - {error}")
    
    print(f"\n📄 Relatório detalhado: {report_path}")
    
    # Código de saída
    exit_code = 0 if results['integrity_check'] else 1
    sys.exit(exit_code)

if __name__ == '__main__':
    main()