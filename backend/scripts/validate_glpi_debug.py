#!/usr/bin/env python3
"""
Script de Validação Completa GLPI - Debugging de Dados Zerados
Executa checklist sistemático para identificar problemas nos dados
"""

import os
import sys
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Adicionar o diretório backend ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_config
from services.legacy.glpi_service_facade import GLPIServiceFacade
from services.legacy.authentication_service import GLPIAuthenticationService

# Configurar logs detalhados
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('glpi_debug')

class GLPIDataValidator:
    """Validador completo de dados GLPI"""
    
    def __init__(self):
        self.settings = get_config()
        self.glpi_url = self.settings.GLPI_URL
        self.app_token = self.settings.GLPI_APP_TOKEN
        self.user_token = self.settings.GLPI_USER_TOKEN
        self.auth_service = GLPIAuthenticationService()
        self.glpi_facade = GLPIServiceFacade()
        self.session_token = None
        
    def validate_connectivity(self) -> bool:
        """1. Teste de conectividade básica"""
        print("\n🔍 1. TESTANDO CONECTIVIDADE GLPI...")
        
        try:
            response = requests.get(
                f"{self.glpi_url}",
                timeout=30,
                headers={'App-Token': self.app_token}
            )
            print(f"✅ Conectividade GLPI: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro de conectividade: {e}")
            logger.error(f"Connectivity error: {e}")
            return False
    
    def validate_authentication(self) -> bool:
        """2. Teste de autenticação"""
        print("\n🔐 2. TESTANDO AUTENTICAÇÃO...")
        
        try:
            auth_success = self.auth_service.authenticate()
            if auth_success:
                print("✅ Autenticação GLPI: OK")
                if hasattr(self.auth_service, 'session_token') and self.auth_service.session_token:
                    print(f"   Token: {self.auth_service.session_token[:20]}...")
                return True
            else:
                print("❌ Falha na autenticação - Token não obtido")
                return False
        except Exception as e:
            print(f"❌ Erro na autenticação: {e}")
            logger.error(f"Authentication error: {e}")
            return False
    
    def validate_basic_data(self) -> Dict[str, Any]:
        """3. Teste de dados básicos"""
        print("\n📊 3. VALIDANDO DADOS BÁSICOS...")
        
        results = {
            'tickets_available': False,
            'users_available': False,
            'ticket_count': 0,
            'user_count': 0
        }
        
        try:
            # Testar busca de tickets
            tickets_response = self.glpi_facade._make_authenticated_request(
                'GET', 
                '/Ticket',
                params={'range': '0-0'}  # Apenas 1 ticket para teste
            )
            
            if tickets_response and isinstance(tickets_response, list):
                results['tickets_available'] = len(tickets_response) > 0
                results['ticket_count'] = len(tickets_response)
                print(f"✅ Tickets disponíveis: {results['tickets_available']} (count: {results['ticket_count']})")
            else:
                print("❌ Nenhum ticket encontrado")
                logger.warning("No tickets found in response")
            
            # Testar busca de usuários
            users_response = self.glpi_facade._make_authenticated_request(
                'GET',
                '/User',
                params={'range': '0-0'}  # Apenas 1 usuário para teste
            )
            
            if users_response and isinstance(users_response, list):
                results['users_available'] = len(users_response) > 0
                results['user_count'] = len(users_response)
                print(f"✅ Usuários disponíveis: {results['users_available']} (count: {results['user_count']})")
            else:
                print("❌ Nenhum usuário encontrado")
                logger.warning("No users found in response")
                
        except Exception as e:
            print(f"❌ Erro ao validar dados básicos: {e}")
            logger.error(f"Basic data validation error: {e}")
        
        return results
    
    def validate_technician_ranking(self) -> List[Dict[str, Any]]:
        """4. Teste do endpoint problemático - Ranking de Técnicos"""
        print("\n👥 4. VALIDANDO RANKING DE TÉCNICOS...")
        
        try:
            # Definir período de teste (últimos 30 dias)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            logger.debug(f"Período de teste: {start_date} - {end_date}")
            
            # Buscar ranking usando o método corrigido
            ranking = self.glpi_facade.get_technician_ranking_with_filters(limit=10)
            
            if not ranking:
                print("❌ Nenhum técnico encontrado no ranking")
                logger.warning("No technicians found in ranking")
                return []
            
            print(f"📈 Total de técnicos no ranking: {len(ranking)}")
            
            # Analisar primeiros 5 técnicos
            issues_found = []
            
            for i, tech in enumerate(ranking[:5]):
                print(f"\n--- Técnico {i+1} ---")
                print(f"Nome: {tech.get('name', 'N/A')}")
                print(f"Tickets: {tech.get('ticket_count', 0)}")
                print(f"Resolvidos: {tech.get('resolved_count', 0)}")
                print(f"Score: {tech.get('performance_score', 'N/A')}")
                print(f"Fonte: {tech.get('data_source', 'unknown')}")
                
                # Identificar problemas
                if tech.get('ticket_count', 0) == 0:
                    issue = f"⚠️ PROBLEMA: Técnico {tech.get('name')} sem tickets!"
                    print(f"  {issue}")
                    issues_found.append(issue)
                    
                if tech.get('performance_score') is None:
                    issue = f"⚠️ PROBLEMA: Score nulo para {tech.get('name')}!"
                    print(f"  {issue}")
                    issues_found.append(issue)
                    
                if tech.get('data_source') == 'unknown':
                    issue = f"⚠️ PROBLEMA: Fonte desconhecida para {tech.get('name')}!"
                    print(f"  {issue}")
                    issues_found.append(issue)
            
            if issues_found:
                print(f"\n🚨 PROBLEMAS IDENTIFICADOS ({len(issues_found)}):")
                for issue in issues_found:
                    print(f"  - {issue}")
            else:
                print("\n✅ Nenhum problema crítico identificado no ranking")
            
            return ranking
            
        except Exception as e:
            print(f"❌ Erro ao validar ranking de técnicos: {e}")
            logger.error(f"Technician ranking validation error: {e}")
            return []
    
    def validate_performance_metrics(self) -> Dict[str, Any]:
        """5. Teste de métricas de performance"""
        print("\n📊 5. VALIDANDO MÉTRICAS DE PERFORMANCE...")
        
        try:
            # Definir período de teste
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Buscar métricas usando o método corrigido
            performance_result = self.glpi_facade.get_technician_performance()
            
            if not performance_result.get('success', False):
                print(f"❌ Erro ao obter métricas: {performance_result.get('error', 'Erro desconhecido')}")
                return {'total_records': 0, 'valid_records': 0, 'issues': ['Falha ao obter dados']}
            
            performance = performance_result.get('data', [])
            print(f"📈 Total de registros de performance: {len(performance)}")
            
            # Analisar métricas
            zero_tickets = 0
            null_scores = 0
            valid_records = 0
            
            for record in performance[:10]:  # Primeiros 10
                if record.get('total_tickets', 0) == 0:
                    zero_tickets += 1
                if record.get('performance_score') is None:
                    null_scores += 1
                if record.get('total_tickets', 0) > 0 and record.get('performance_score') is not None:
                    valid_records += 1
            
            print(f"📊 Análise das métricas:")
            print(f"  - Registros com zero tickets: {zero_tickets}")
            print(f"  - Registros com score nulo: {null_scores}")
            print(f"  - Registros válidos: {valid_records}")
            
            return {
                'total_records': len(performance),
                'zero_tickets': zero_tickets,
                'null_scores': null_scores,
                'valid_records': valid_records,
                'data': performance[:5]  # Primeiros 5 para análise
            }
            
        except Exception as e:
            print(f"❌ Erro ao validar métricas de performance: {e}")
            logger.error(f"Performance metrics validation error: {e}")
            return {}
    
    def run_complete_validation(self) -> Dict[str, Any]:
        """Executa validação completa seguindo o checklist"""
        print("🔍 INICIANDO VALIDAÇÃO COMPLETA GLPI...")
        print("=" * 50)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'connectivity': False,
            'authentication': False,
            'basic_data': {},
            'technician_ranking': [],
            'performance_metrics': {},
            'summary': {
                'total_issues': 0,
                'critical_issues': [],
                'recommendations': []
            }
        }
        
        # 1. Conectividade
        results['connectivity'] = self.validate_connectivity()
        if not results['connectivity']:
            results['summary']['critical_issues'].append("Falha na conectividade GLPI")
            return results
        
        # 2. Autenticação
        results['authentication'] = self.validate_authentication()
        if not results['authentication']:
            results['summary']['critical_issues'].append("Falha na autenticação GLPI")
            return results
        
        # 3. Dados básicos
        results['basic_data'] = self.validate_basic_data()
        
        # 4. Ranking de técnicos
        results['technician_ranking'] = self.validate_technician_ranking()
        
        # 5. Métricas de performance
        results['performance_metrics'] = self.validate_performance_metrics()
        
        # Gerar resumo
        self._generate_summary(results)
        
        return results
    
    def _generate_summary(self, results: Dict[str, Any]) -> None:
        """Gera resumo da validação"""
        print("\n" + "=" * 50)
        print("📋 RESUMO DA VALIDAÇÃO")
        print("=" * 50)
        
        # Status geral
        if results['connectivity'] and results['authentication']:
            print("✅ Status Geral: CONECTADO")
        else:
            print("❌ Status Geral: PROBLEMAS DE CONEXÃO")
        
        # Dados básicos
        basic = results.get('basic_data', {})
        if basic.get('tickets_available') and basic.get('users_available'):
            print("✅ Dados Básicos: DISPONÍVEIS")
        else:
            print("⚠️ Dados Básicos: PROBLEMAS DETECTADOS")
        
        # Ranking
        ranking_count = len(results.get('technician_ranking', []))
        if ranking_count > 0:
            print(f"✅ Ranking de Técnicos: {ranking_count} registros")
        else:
            print("❌ Ranking de Técnicos: VAZIO")
            results['summary']['critical_issues'].append("Ranking de técnicos vazio")
        
        # Performance
        perf = results.get('performance_metrics', {})
        if perf.get('total_records', 0) > 0:
            print(f"✅ Métricas de Performance: {perf['total_records']} registros")
            if perf.get('zero_tickets', 0) > 0:
                print(f"⚠️ Registros com zero tickets: {perf['zero_tickets']}")
        else:
            print("❌ Métricas de Performance: VAZIAS")
            results['summary']['critical_issues'].append("Métricas de performance vazias")
        
        # Recomendações
        recommendations = [
            "Verificar filtros de data nos endpoints",
            "Validar permissões de entidade no GLPI",
            "Conferir mapeamento de status de tickets",
            "Implementar logs detalhados em produção",
            "Monitorar cache para dados stale"
        ]
        
        print("\n🎯 RECOMENDAÇÕES:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        results['summary']['recommendations'] = recommendations
        results['summary']['total_issues'] = len(results['summary']['critical_issues'])

def main():
    """Função principal"""
    validator = GLPIDataValidator()
    
    try:
        results = validator.run_complete_validation()
        
        # Salvar resultados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"glpi_validation_results_{timestamp}.json"
        
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Resultados salvos em: {output_file}")
        
        return results['summary']['total_issues'] == 0
        
    except Exception as e:
        print(f"❌ Erro durante validação: {e}")
        logger.error(f"Validation error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)