# ===========================================
# SISTEMA DE DIAGNÓSTICO LEGACY
# ===========================================

import subprocess
import psutil
import requests
import socket
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
from backend.config.settings import Config
from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter
from backend.services.legacy.glpi_service_facade import GLPIServiceFacade

@dataclass
class DiagnosticResult:
    test_name: str
    status: str  # 'pass', 'fail', 'warning'
    message: str
    details: Dict = None
    solution: str = None

class DiagnosticSystem:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.adapter = LegacyServiceAdapter()
        self.glpi_facade = GLPIServiceFacade()
    
    def run_full_diagnostic(self) -> Dict:
        """Executa diagnóstico completo do sistema"""
        self.logger.info("Iniciando diagnóstico completo")
        
        diagnostic_tests = [
            ("Conectividade de Rede", self._test_network_connectivity),
            ("Configuração de Ambiente", self._test_environment_config),
            ("Conectividade GLPI", self._test_glpi_connectivity),
            ("Serviços Legacy", self._test_legacy_services),
            ("Performance do Sistema", self._test_system_performance),
            ("Dependências Python", self._test_python_dependencies),
            ("Logs e Arquivos", self._test_logs_and_files),
            ("Cache e Memória", self._test_cache_and_memory)
        ]
        
        results = []
        overall_status = "pass"
        
        for test_name, test_func in diagnostic_tests:
            try:
                result = test_func()
                results.append(result)
                
                if result.status == "fail":
                    overall_status = "fail"
                elif result.status == "warning" and overall_status == "pass":
                    overall_status = "warning"
                    
            except Exception as e:
                results.append(DiagnosticResult(
                    test_name=test_name,
                    status="fail",
                    message=f"Erro ao executar teste: {str(e)}",
                    solution="Verifique os logs do sistema para mais detalhes"
                ))
                overall_status = "fail"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "total_tests": len(diagnostic_tests),
            "passed_tests": len([r for r in results if r.status == "pass"]),
            "failed_tests": len([r for r in results if r.status == "fail"]),
            "warning_tests": len([r for r in results if r.status == "warning"]),
            "results": [self._result_to_dict(r) for r in results]
        }
    
    def _test_network_connectivity(self) -> DiagnosticResult:
        """Testa conectividade de rede"""
        try:
            # Testar conectividade com GLPI
            glpi_url = self.config.GLPI_URL
            if not glpi_url:
                return DiagnosticResult(
                    test_name="Conectividade de Rede",
                    status="fail",
                    message="URL do GLPI não configurada",
                    solution="Configure GLPI_URL no arquivo .env"
                )
            
            # Extrair host da URL
            from urllib.parse import urlparse
            parsed_url = urlparse(glpi_url)
            host = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            
            # Testar conexão TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return DiagnosticResult(
                    test_name="Conectividade de Rede",
                    status="pass",
                    message=f"Conectividade com {host}:{port} OK",
                    details={"host": host, "port": port}
                )
            else:
                return DiagnosticResult(
                    test_name="Conectividade de Rede",
                    status="fail",
                    message=f"Não foi possível conectar com {host}:{port}",
                    details={"host": host, "port": port, "error_code": result},
                    solution="Verifique firewall, proxy ou conectividade de rede"
                )
                
        except Exception as e:
            return DiagnosticResult(
                test_name="Conectividade de Rede",
                status="fail",
                message=f"Erro no teste de rede: {str(e)}",
                solution="Verifique configuração de rede e URL do GLPI"
            )
    
    def _test_environment_config(self) -> DiagnosticResult:
        """Testa configuração do ambiente"""
        required_vars = [
            'GLPI_URL', 'GLPI_USER_TOKEN', 'GLPI_APP_TOKEN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(self.config, var, None):
                missing_vars.append(var)
        
        if missing_vars:
            return DiagnosticResult(
                test_name="Configuração de Ambiente",
                status="fail",
                message=f"Variáveis de ambiente faltando: {', '.join(missing_vars)}",
                details={"missing_variables": missing_vars},
                solution="Configure as variáveis faltando no arquivo .env"
            )
        
        # Verificar se USE_MOCK_DATA está configurado corretamente
        use_mock = getattr(self.config, 'USE_MOCK_DATA', True)
        if use_mock:
            return DiagnosticResult(
                test_name="Configuração de Ambiente",
                status="warning",
                message="Sistema configurado para usar dados mock",
                details={"use_mock_data": use_mock},
                solution="Para usar dados reais, configure USE_MOCK_DATA=false no .env"
            )
        
        return DiagnosticResult(
            test_name="Configuração de Ambiente",
            status="pass",
            message="Configuração de ambiente OK",
            details={"use_mock_data": use_mock}
        )
    
    def _test_glpi_connectivity(self) -> DiagnosticResult:
        """Testa conectividade com GLPI"""
        try:
            # Testar autenticação
            auth_result = self.glpi_facade.authenticate()
            
            if auth_result:
                return DiagnosticResult(
                    test_name="Conectividade GLPI",
                    status="pass",
                    message="Autenticação com GLPI bem-sucedida",
                    details={"session_token": "***" if auth_result else None}
                )
            else:
                return DiagnosticResult(
                    test_name="Conectividade GLPI",
                    status="fail",
                    message="Falha na autenticação com GLPI",
                    solution="Verifique GLPI_USER_TOKEN e GLPI_APP_TOKEN no .env"
                )
                
        except Exception as e:
            return DiagnosticResult(
                test_name="Conectividade GLPI",
                status="fail",
                message=f"Erro na conectividade GLPI: {str(e)}",
                solution="Verifique URL, tokens e conectividade de rede"
            )
    
    def _test_legacy_services(self) -> DiagnosticResult:
        """Testa serviços legacy"""
        try:
            # Testar método principal do adapter
            metrics = self.adapter.get_dashboard_metrics('diagnostic_test')
            
            if metrics and hasattr(metrics, 'total_tickets'):
                return DiagnosticResult(
                    test_name="Serviços Legacy",
                    status="pass",
                    message="Serviços legacy funcionando corretamente",
                    details={
                        "total_tickets": getattr(metrics, 'total_tickets', None),
                        "has_data": True
                    }
                )
            else:
                return DiagnosticResult(
                    test_name="Serviços Legacy",
                    status="fail",
                    message="Serviços legacy não retornaram dados válidos",
                    solution="Verifique implementação do LegacyServiceAdapter"
                )
                
        except Exception as e:
            return DiagnosticResult(
                test_name="Serviços Legacy",
                status="fail",
                message=f"Erro nos serviços legacy: {str(e)}",
                solution="Verifique logs e implementação dos serviços legacy"
            )
    
    def _test_system_performance(self) -> DiagnosticResult:
        """Testa performance do sistema"""
        try:
            # Métricas do sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            issues = []
            if cpu_percent > 80:
                issues.append(f"CPU alta: {cpu_percent}%")
            if memory.percent > 85:
                issues.append(f"Memória alta: {memory.percent}%")
            if disk.percent > 90:
                issues.append(f"Disco cheio: {disk.percent}%")
            
            if issues:
                return DiagnosticResult(
                    test_name="Performance do Sistema",
                    status="warning",
                    message=f"Problemas de performance: {', '.join(issues)}",
                    details={
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_percent": disk.percent
                    },
                    solution="Monitore recursos e considere otimizações"
                )
            
            return DiagnosticResult(
                test_name="Performance do Sistema",
                status="pass",
                message="Performance do sistema OK",
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent
                }
            )
            
        except Exception as e:
            return DiagnosticResult(
                test_name="Performance do Sistema",
                status="fail",
                message=f"Erro ao verificar performance: {str(e)}",
                solution="Verifique se psutil está instalado corretamente"
            )
    
    def _test_python_dependencies(self) -> DiagnosticResult:
        """Testa dependências Python"""
        try:
            required_packages = [
                'flask', 'requests', 'psutil', 'pydantic'
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                return DiagnosticResult(
                    test_name="Dependências Python",
                    status="fail",
                    message=f"Pacotes faltando: {', '.join(missing_packages)}",
                    details={"missing_packages": missing_packages},
                    solution="Execute: pip install -r requirements.txt"
                )
            
            return DiagnosticResult(
                test_name="Dependências Python",
                status="pass",
                message="Todas as dependências estão instaladas"
            )
            
        except Exception as e:
            return DiagnosticResult(
                test_name="Dependências Python",
                status="fail",
                message=f"Erro ao verificar dependências: {str(e)}",
                solution="Verifique instalação do Python e pip"
            )
    
    def _test_logs_and_files(self) -> DiagnosticResult:
        """Testa logs e arquivos do sistema"""
        try:
            import os
            
            # Verificar diretório de logs
            log_path = getattr(self.config, 'LOG_FILE_PATH', 'logs/app.log')
            log_dir = os.path.dirname(log_path)
            
            if not os.path.exists(log_dir):
                return DiagnosticResult(
                    test_name="Logs e Arquivos",
                    status="warning",
                    message=f"Diretório de logs não existe: {log_dir}",
                    solution=f"Crie o diretório: mkdir -p {log_dir}"
                )
            
            # Verificar permissões de escrita
            if not os.access(log_dir, os.W_OK):
                return DiagnosticResult(
                    test_name="Logs e Arquivos",
                    status="fail",
                    message=f"Sem permissão de escrita em: {log_dir}",
                    solution=f"Ajuste permissões: chmod 755 {log_dir}"
                )
            
            return DiagnosticResult(
                test_name="Logs e Arquivos",
                status="pass",
                message="Sistema de logs configurado corretamente",
                details={"log_directory": log_dir}
            )
            
        except Exception as e:
            return DiagnosticResult(
                test_name="Logs e Arquivos",
                status="fail",
                message=f"Erro ao verificar logs: {str(e)}",
                solution="Verifique configuração de logs no sistema"
            )
    
    def _test_cache_and_memory(self) -> DiagnosticResult:
        """Testa cache e uso de memória"""
        try:
            # Testar cache (se configurado)
            cache_issues = []
            
            # Verificar uso de memória da aplicação
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            if memory_mb > 500:  # Mais de 500MB
                cache_issues.append(f"Alto uso de memória: {memory_mb:.1f}MB")
            
            if cache_issues:
                return DiagnosticResult(
                    test_name="Cache e Memória",
                    status="warning",
                    message=f"Problemas detectados: {', '.join(cache_issues)}",
                    details={"memory_mb": memory_mb},
                    solution="Monitore uso de memória e considere otimizações"
                )
            
            return DiagnosticResult(
                test_name="Cache e Memória",
                status="pass",
                message="Cache e memória OK",
                details={"memory_mb": memory_mb}
            )
            
        except Exception as e:
            return DiagnosticResult(
                test_name="Cache e Memória",
                status="fail",
                message=f"Erro ao verificar cache: {str(e)}",
                solution="Verifique configuração de cache"
            )
    
    def _result_to_dict(self, result: DiagnosticResult) -> Dict:
        """Converte resultado para dicionário"""
        return {
            "test_name": result.test_name,
            "status": result.status,
            "message": result.message,
            "details": result.details,
            "solution": result.solution
        }
    
    def get_troubleshooting_guide(self) -> Dict:
        """Retorna guia de troubleshooting"""
        return {
            "common_issues": [
                {
                    "problem": "Erro de autenticação GLPI",
                    "symptoms": ["401 Unauthorized", "Invalid token", "Authentication failed"],
                    "solutions": [
                        "Verifique GLPI_USER_TOKEN no .env",
                        "Verifique GLPI_APP_TOKEN no .env",
                        "Confirme que os tokens estão válidos no GLPI",
                        "Teste conectividade: curl -H 'App-Token: TOKEN' URL/apirest.php"
                    ]
                },
                {
                    "problem": "Serviços legacy não respondem",
                    "symptoms": ["Timeout", "Connection refused", "Service unavailable"],
                    "solutions": [
                        "Verifique se o GLPI está rodando",
                        "Teste conectividade de rede",
                        "Verifique logs do GLPI",
                        "Reinicie os serviços: systemctl restart apache2"
                    ]
                },
                {
                    "problem": "Performance degradada",
                    "symptoms": ["Lentidão", "Timeouts", "Alto uso de CPU/memória"],
                    "solutions": [
                        "Monitore recursos do sistema",
                        "Otimize queries do banco de dados",
                        "Implemente cache mais agressivo",
                        "Considere scaling horizontal"
                    ]
                },
                {
                    "problem": "Dados inconsistentes",
                    "symptoms": ["Dados vazios", "Valores incorretos", "Estrutura inválida"],
                    "solutions": [
                        "Verifique mapeamento de dados no adapter",
                        "Valide estrutura de resposta da API GLPI",
                        "Teste com dados mock primeiro",
                        "Verifique logs de transformação de dados"
                    ]
                }
            ],
            "diagnostic_commands": [
                {
                    "description": "Testar conectividade GLPI",
                    "command": "curl -H 'App-Token: $GLPI_APP_TOKEN' -H 'Authorization: user_token $GLPI_USER_TOKEN' $GLPI_URL/apirest.php/initSession"
                },
                {
                    "description": "Verificar logs da aplicação",
                    "command": "tail -f logs/app.log | grep ERROR"
                },
                {
                    "description": "Monitorar recursos do sistema",
                    "command": "htop"
                },
                {
                    "description": "Testar endpoint de saúde",
                    "command": "curl http://localhost:5000/api/monitoring/legacy/health"
                }
            ],
            "emergency_procedures": [
                {
                    "scenario": "Sistema completamente indisponível",
                    "steps": [
                        "1. Ativar modo mock: USE_MOCK_DATA=true",
                        "2. Reiniciar aplicação",
                        "3. Verificar logs de erro",
                        "4. Testar conectividade GLPI",
                        "5. Restaurar backup se necessário"
                    ]
                },
                {
                    "scenario": "Performance crítica",
                    "steps": [
                        "1. Ativar cache agressivo",
                        "2. Reduzir frequência de polling",
                        "3. Implementar rate limiting",
                        "4. Monitorar recursos continuamente",
                        "5. Considerar scaling"
                    ]
                }
            ]
        }

# Instância global
diagnostic_system = DiagnosticSystem()