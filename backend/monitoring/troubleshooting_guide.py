# ===========================================
# GUIA DE TROUBLESHOOTING LEGACY
# ===========================================

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from .diagnostic_system import diagnostic_system

@dataclass
class TroubleshootingStep:
    step_number: int
    description: str
    command: Optional[str] = None
    expected_result: Optional[str] = None
    troubleshooting_note: Optional[str] = None

@dataclass
class TroubleshootingSolution:
    problem_id: str
    title: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    symptoms: List[str]
    root_causes: List[str]
    steps: List[TroubleshootingStep]
    prevention: List[str]
    related_problems: List[str] = None

class TroubleshootingGuide:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.solutions = self._initialize_solutions()
    
    def _initialize_solutions(self) -> Dict[str, TroubleshootingSolution]:
        """Inicializa todas as soluções de troubleshooting"""
        solutions = {}
        
        # Problema 1: Erro de Autenticação GLPI
        solutions['glpi_auth_error'] = TroubleshootingSolution(
            problem_id='glpi_auth_error',
            title='Erro de Autenticação GLPI',
            description='Falhas na autenticação com a API do GLPI',
            severity='high',
            symptoms=[
                'HTTP 401 Unauthorized',
                'Invalid token error',
                'Authentication failed',
                'Session token not found',
                'App token invalid'
            ],
            root_causes=[
                'Tokens GLPI inválidos ou expirados',
                'Configuração incorreta no .env',
                'Usuário sem permissões adequadas',
                'API GLPI desabilitada',
                'Firewall bloqueando requisições'
            ],
            steps=[
                TroubleshootingStep(
                    step_number=1,
                    description='Verificar configuração dos tokens',
                    command='grep -E "GLPI_(USER|APP)_TOKEN" .env',
                    expected_result='Tokens devem estar presentes e não vazios',
                    troubleshooting_note='Se tokens estão vazios, configure no .env'
                ),
                TroubleshootingStep(
                    step_number=2,
                    description='Testar autenticação manual',
                    command='curl -X GET "$GLPI_URL/apirest.php/initSession" -H "App-Token: $GLPI_APP_TOKEN" -H "Authorization: user_token $GLPI_USER_TOKEN"',
                    expected_result='Retorno com session_token válido',
                    troubleshooting_note='Se falhar, verifique tokens no GLPI'
                ),
                TroubleshootingStep(
                    step_number=3,
                    description='Verificar permissões do usuário',
                    command='curl -X GET "$GLPI_URL/apirest.php/getMyProfiles" -H "Session-Token: $SESSION_TOKEN"',
                    expected_result='Lista de perfis do usuário',
                    troubleshooting_note='Usuário deve ter perfil com acesso à API'
                ),
                TroubleshootingStep(
                    step_number=4,
                    description='Verificar status da API GLPI',
                    command='curl -X GET "$GLPI_URL/apirest.php" -H "App-Token: $GLPI_APP_TOKEN"',
                    expected_result='Informações da API (versão, endpoints)',
                    troubleshooting_note='Se falhar, API pode estar desabilitada'
                )
            ],
            prevention=[
                'Implementar renovação automática de tokens',
                'Monitorar expiração de tokens',
                'Usar variáveis de ambiente seguras',
                'Documentar processo de geração de tokens'
            ],
            related_problems=['network_connectivity', 'glpi_unavailable']
        )
        
        # Problema 2: Conectividade de Rede
        solutions['network_connectivity'] = TroubleshootingSolution(
            problem_id='network_connectivity',
            title='Problemas de Conectividade de Rede',
            description='Falhas na comunicação de rede com serviços GLPI',
            severity='high',
            symptoms=[
                'Connection timeout',
                'Connection refused',
                'DNS resolution failed',
                'Network unreachable',
                'SSL certificate errors'
            ],
            root_causes=[
                'Firewall bloqueando conexões',
                'Proxy mal configurado',
                'DNS não resolvendo hostname',
                'Certificado SSL inválido',
                'Serviço GLPI offline'
            ],
            steps=[
                TroubleshootingStep(
                    step_number=1,
                    description='Testar conectividade básica',
                    command='ping $(echo $GLPI_URL | sed "s|https\\?://||" | cut -d"/" -f1)',
                    expected_result='Resposta de ping bem-sucedida',
                    troubleshooting_note='Se falhar, problema de rede ou DNS'
                ),
                TroubleshootingStep(
                    step_number=2,
                    description='Testar conectividade de porta',
                    command='telnet $(echo $GLPI_URL | sed "s|https\\?://||" | cut -d"/" -f1) 80',
                    expected_result='Conexão estabelecida',
                    troubleshooting_note='Teste porta 443 para HTTPS'
                ),
                TroubleshootingStep(
                    step_number=3,
                    description='Verificar resolução DNS',
                    command='nslookup $(echo $GLPI_URL | sed "s|https\\?://||" | cut -d"/" -f1)',
                    expected_result='IP válido retornado',
                    troubleshooting_note='Se falhar, problema de DNS'
                ),
                TroubleshootingStep(
                    step_number=4,
                    description='Testar certificado SSL',
                    command='openssl s_client -connect $(echo $GLPI_URL | sed "s|https\\?://||" | cut -d"/" -f1):443 -servername $(echo $GLPI_URL | sed "s|https\\?://||" | cut -d"/" -f1)',
                    expected_result='Certificado válido e conexão SSL',
                    troubleshooting_note='Verificar data de expiração'
                )
            ],
            prevention=[
                'Monitorar conectividade continuamente',
                'Configurar alertas de rede',
                'Manter certificados atualizados',
                'Documentar configurações de firewall'
            ]
        )
        
        # Problema 3: Performance Degradada
        solutions['performance_issues'] = TroubleshootingSolution(
            problem_id='performance_issues',
            title='Problemas de Performance',
            description='Lentidão ou degradação de performance do sistema',
            severity='medium',
            symptoms=[
                'Respostas lentas da API',
                'Timeouts frequentes',
                'Alto uso de CPU',
                'Alto uso de memória',
                'Queries lentas no banco'
            ],
            root_causes=[
                'Queries não otimizadas',
                'Cache insuficiente',
                'Recursos limitados do servidor',
                'Muitas requisições simultâneas',
                'Dados não indexados'
            ],
            steps=[
                TroubleshootingStep(
                    step_number=1,
                    description='Monitorar recursos do sistema',
                    command='htop',
                    expected_result='Identificar processos com alto uso de recursos',
                    troubleshooting_note='Observe CPU, memória e I/O'
                ),
                TroubleshootingStep(
                    step_number=2,
                    description='Analisar logs de performance',
                    command='grep -E "(slow|timeout|performance)" logs/app.log | tail -20',
                    expected_result='Identificar operações lentas',
                    troubleshooting_note='Procure por padrões de lentidão'
                ),
                TroubleshootingStep(
                    step_number=3,
                    description='Verificar cache hit rate',
                    command='curl http://localhost:5000/api/monitoring/legacy/metrics | jq ".cache"',
                    expected_result='Taxa de cache acima de 80%',
                    troubleshooting_note='Se baixa, otimizar estratégia de cache'
                ),
                TroubleshootingStep(
                    step_number=4,
                    description='Analisar queries do banco',
                    command='tail -f /var/log/mysql/slow.log',
                    expected_result='Identificar queries lentas',
                    troubleshooting_note='Otimizar queries identificadas'
                )
            ],
            prevention=[
                'Implementar monitoramento contínuo',
                'Otimizar queries regularmente',
                'Configurar cache adequadamente',
                'Planejar capacidade de recursos'
            ]
        )
        
        # Problema 4: Dados Inconsistentes
        solutions['data_inconsistency'] = TroubleshootingSolution(
            problem_id='data_inconsistency',
            title='Inconsistência de Dados',
            description='Dados incorretos ou inconsistentes entre sistemas',
            severity='medium',
            symptoms=[
                'Dados vazios ou nulos',
                'Valores incorretos',
                'Estrutura de dados inválida',
                'Discrepâncias entre sistemas',
                'Erros de validação'
            ],
            root_causes=[
                'Mapeamento incorreto de dados',
                'Transformações com bugs',
                'Mudanças na API GLPI',
                'Problemas de sincronização',
                'Validação insuficiente'
            ],
            steps=[
                TroubleshootingStep(
                    step_number=1,
                    description='Verificar estrutura de dados da API',
                    command='curl -X GET "$GLPI_URL/apirest.php/Ticket" -H "Session-Token: $SESSION_TOKEN" | jq "." | head -50',
                    expected_result='Estrutura de dados válida',
                    troubleshooting_note='Compare com estrutura esperada'
                ),
                TroubleshootingStep(
                    step_number=2,
                    description='Testar com dados mock',
                    command='USE_MOCK_DATA=true python -c "from backend.services.legacy.glpi_service_facade import GLPIServiceFacade; print(GLPIServiceFacade().get_tickets())"',
                    expected_result='Dados mock válidos',
                    troubleshooting_note='Se mock funciona, problema na API real'
                ),
                TroubleshootingStep(
                    step_number=3,
                    description='Validar transformações de dados',
                    command='python -c "from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter; adapter = LegacyServiceAdapter(); print(adapter.get_dashboard_metrics(\'test\'))"',
                    expected_result='Dados transformados corretamente',
                    troubleshooting_note='Verificar se transformação está correta'
                ),
                TroubleshootingStep(
                    step_number=4,
                    description='Comparar dados entre ambientes',
                    command='diff <(curl -s "$GLPI_URL_PROD/apirest.php/Ticket" | jq "sort") <(curl -s "$GLPI_URL_DEV/apirest.php/Ticket" | jq "sort")',
                    expected_result='Identificar diferenças entre ambientes',
                    troubleshooting_note='Verificar consistência entre ambientes'
                )
            ],
            prevention=[
                'Implementar validação rigorosa',
                'Monitorar mudanças na API',
                'Testes automatizados de dados',
                'Versionamento de esquemas'
            ]
        )
        
        # Problema 5: Serviço GLPI Indisponível
        solutions['glpi_unavailable'] = TroubleshootingSolution(
            problem_id='glpi_unavailable',
            title='Serviço GLPI Indisponível',
            description='GLPI completamente inacessível ou com falhas críticas',
            severity='critical',
            symptoms=[
                'HTTP 500/502/503 errors',
                'Service unavailable',
                'Database connection errors',
                'Apache/Nginx errors',
                'PHP fatal errors'
            ],
            root_causes=[
                'Servidor GLPI offline',
                'Banco de dados indisponível',
                'Problemas de configuração',
                'Recursos esgotados',
                'Falhas de hardware'
            ],
            steps=[
                TroubleshootingStep(
                    step_number=1,
                    description='Verificar status do servidor',
                    command='systemctl status apache2 mysql',
                    expected_result='Serviços rodando normalmente',
                    troubleshooting_note='Reiniciar serviços se necessário'
                ),
                TroubleshootingStep(
                    step_number=2,
                    description='Verificar logs do GLPI',
                    command='tail -f /var/log/apache2/error.log /var/www/glpi/files/_log/php-errors.log',
                    expected_result='Identificar erros específicos',
                    troubleshooting_note='Procurar por erros PHP ou Apache'
                ),
                TroubleshootingStep(
                    step_number=3,
                    description='Testar conectividade do banco',
                    command='mysql -u glpi -p -h localhost -e "SELECT 1"',
                    expected_result='Conexão bem-sucedida',
                    troubleshooting_note='Se falhar, problema no MySQL'
                ),
                TroubleshootingStep(
                    step_number=4,
                    description='Ativar modo de emergência',
                    command='echo "USE_MOCK_DATA=true" >> .env && systemctl restart glpi-dashboard',
                    expected_result='Sistema funcionando com dados mock',
                    troubleshooting_note='Modo temporário até resolver GLPI'
                )
            ],
            prevention=[
                'Monitoramento 24/7 do GLPI',
                'Backup automático regular',
                'Cluster de alta disponibilidade',
                'Plano de recuperação de desastres'
            ]
        )
        
        return solutions
    
    def get_solution(self, problem_id: str) -> Optional[TroubleshootingSolution]:
        """Retorna solução específica por ID"""
        return self.solutions.get(problem_id)
    
    def search_solutions(self, symptom: str) -> List[TroubleshootingSolution]:
        """Busca soluções por sintoma"""
        matching_solutions = []
        symptom_lower = symptom.lower()
        
        for solution in self.solutions.values():
            for solution_symptom in solution.symptoms:
                if symptom_lower in solution_symptom.lower():
                    matching_solutions.append(solution)
                    break
        
        return matching_solutions
    
    def get_emergency_procedures(self) -> Dict:
        """Retorna procedimentos de emergência"""
        return {
            "system_down": {
                "title": "Sistema Completamente Indisponível",
                "severity": "critical",
                "immediate_actions": [
                    "1. Ativar modo mock: USE_MOCK_DATA=true",
                    "2. Reiniciar todos os serviços",
                    "3. Verificar logs de erro críticos",
                    "4. Notificar equipe de suporte",
                    "5. Ativar plano de contingência"
                ],
                "recovery_steps": [
                    "1. Identificar causa raiz",
                    "2. Restaurar backup se necessário",
                    "3. Testar funcionalidades críticas",
                    "4. Gradualmente desativar modo mock",
                    "5. Monitorar estabilidade"
                ]
            },
            "performance_critical": {
                "title": "Performance Crítica",
                "severity": "high",
                "immediate_actions": [
                    "1. Ativar cache agressivo",
                    "2. Reduzir frequência de polling",
                    "3. Implementar rate limiting",
                    "4. Escalar recursos temporariamente",
                    "5. Monitorar métricas continuamente"
                ],
                "recovery_steps": [
                    "1. Analisar bottlenecks",
                    "2. Otimizar queries críticas",
                    "3. Implementar melhorias de cache",
                    "4. Planejar scaling permanente",
                    "5. Documentar lições aprendidas"
                ]
            },
            "data_corruption": {
                "title": "Corrupção de Dados",
                "severity": "high",
                "immediate_actions": [
                    "1. Parar sincronização de dados",
                    "2. Isolar dados corrompidos",
                    "3. Ativar backup de dados",
                    "4. Notificar usuários afetados",
                    "5. Iniciar investigação"
                ],
                "recovery_steps": [
                    "1. Identificar extensão da corrupção",
                    "2. Restaurar dados do backup",
                    "3. Validar integridade dos dados",
                    "4. Reativar sincronização gradualmente",
                    "5. Implementar validações adicionais"
                ]
            }
        }
    
    def generate_diagnostic_report(self) -> Dict:
        """Gera relatório de diagnóstico completo"""
        self.logger.info("Gerando relatório de diagnóstico")
        
        # Executar diagnóstico automático
        diagnostic_results = diagnostic_system.run_full_diagnostic()
        
        # Identificar problemas baseados nos resultados
        identified_problems = []
        for result in diagnostic_results['results']:
            if result['status'] == 'fail':
                # Mapear falhas para problemas conhecidos
                if 'glpi' in result['test_name'].lower():
                    if 'conectividade' in result['test_name'].lower():
                        identified_problems.append('network_connectivity')
                    elif 'autenticação' in result['message'].lower():
                        identified_problems.append('glpi_auth_error')
                    else:
                        identified_problems.append('glpi_unavailable')
                elif 'performance' in result['test_name'].lower():
                    identified_problems.append('performance_issues')
        
        # Gerar recomendações
        recommendations = []
        for problem_id in set(identified_problems):
            solution = self.get_solution(problem_id)
            if solution:
                recommendations.append({
                    "problem": solution.title,
                    "severity": solution.severity,
                    "first_steps": [step.description for step in solution.steps[:3]]
                })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "diagnostic_results": diagnostic_results,
            "identified_problems": identified_problems,
            "recommendations": recommendations,
            "emergency_contacts": {
                "support_team": "support@company.com",
                "on_call": "+55-11-99999-9999",
                "escalation": "manager@company.com"
            }
        }
    
    def get_quick_fixes(self) -> Dict:
        """Retorna correções rápidas para problemas comuns"""
        return {
            "restart_services": {
                "description": "Reiniciar todos os serviços",
                "commands": [
                    "systemctl restart apache2",
                    "systemctl restart mysql",
                    "systemctl restart glpi-dashboard"
                ],
                "risk": "low",
                "downtime": "2-5 minutes"
            },
            "clear_cache": {
                "description": "Limpar cache do sistema",
                "commands": [
                    "rm -rf /tmp/glpi-cache/*",
                    "redis-cli FLUSHALL",
                    "systemctl restart glpi-dashboard"
                ],
                "risk": "low",
                "downtime": "1-2 minutes"
            },
            "enable_mock_mode": {
                "description": "Ativar modo mock temporário",
                "commands": [
                    "echo 'USE_MOCK_DATA=true' >> .env",
                    "systemctl restart glpi-dashboard"
                ],
                "risk": "low",
                "downtime": "30 seconds"
            },
            "reset_tokens": {
                "description": "Regenerar tokens GLPI",
                "commands": [
                    "# Gerar novos tokens no GLPI",
                    "# Atualizar .env com novos tokens",
                    "systemctl restart glpi-dashboard"
                ],
                "risk": "medium",
                "downtime": "5-10 minutes"
            }
        }

# Instância global
troubleshooting_guide = TroubleshootingGuide()