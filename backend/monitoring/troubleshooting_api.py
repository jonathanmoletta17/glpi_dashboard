# ===========================================
# API DE TROUBLESHOOTING LEGACY
# ===========================================

from flask import Blueprint, jsonify, request
from typing import Dict, Any
import logging
from .diagnostic_system import diagnostic_system
from .troubleshooting_guide import troubleshooting_guide
from datetime import datetime

# Blueprint para troubleshooting
troubleshooting_bp = Blueprint('troubleshooting', __name__, url_prefix='/api/troubleshooting')
logger = logging.getLogger(__name__)

@troubleshooting_bp.route('/diagnostic', methods=['GET'])
def run_diagnostic():
    """Executa diagnóstico completo do sistema"""
    try:
        logger.info("Executando diagnóstico completo via API")
        
        # Executar diagnóstico
        results = diagnostic_system.run_full_diagnostic()
        
        return jsonify({
            "success": True,
            "data": results,
            "message": "Diagnóstico executado com sucesso"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao executar diagnóstico: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Erro ao executar diagnóstico"
        }), 500

@troubleshooting_bp.route('/diagnostic/report', methods=['GET'])
def generate_diagnostic_report():
    """Gera relatório completo de diagnóstico com recomendações"""
    try:
        logger.info("Gerando relatório de diagnóstico")
        
        # Gerar relatório
        report = troubleshooting_guide.generate_diagnostic_report()
        
        return jsonify({
            "success": True,
            "data": report,
            "message": "Relatório gerado com sucesso"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Erro ao gerar relatório"
        }), 500

@troubleshooting_bp.route('/solutions', methods=['GET'])
def get_all_solutions():
    """Retorna todas as soluções de troubleshooting disponíveis"""
    try:
        solutions = []
        for solution in troubleshooting_guide.solutions.values():
            solutions.append({
                "id": solution.problem_id,
                "title": solution.title,
                "description": solution.description,
                "severity": solution.severity,
                "symptoms": solution.symptoms,
                "steps_count": len(solution.steps)
            })
        
        return jsonify({
            "success": True,
            "data": solutions,
            "message": f"Encontradas {len(solutions)} soluções"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar soluções: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Erro ao buscar soluções"
        }), 500

@troubleshooting_bp.route('/solutions/<problem_id>', methods=['GET'])
def get_solution_details(problem_id: str):
    """Retorna detalhes completos de uma solução específica"""
    try:
        solution = troubleshooting_guide.get_solution(problem_id)
        
        if not solution:
            return jsonify({
                "success": False,
                "message": f"Solução '{problem_id}' não encontrada"
            }), 404
        
        # Converter steps para formato JSON
        steps = []
        for step in solution.steps:
            steps.append({
                "step_number": step.step_number,
                "description": step.description,
                "command": step.command,
                "expected_result": step.expected_result,
                "troubleshooting_note": step.troubleshooting_note
            })
        
        solution_data = {
            "id": solution.problem_id,
            "title": solution.title,
            "description": solution.description,
            "severity": solution.severity,
            "symptoms": solution.symptoms,
            "root_causes": solution.root_causes,
            "steps": steps,
            "prevention": solution.prevention,
            "related_problems": solution.related_problems or []
        }
        
        return jsonify({
            "success": True,
            "data": solution_data,
            "message": "Solução encontrada"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar solução {problem_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Erro ao buscar solução"
        }), 500

@troubleshooting_bp.route('/search', methods=['GET'])
def search_solutions():
    """Busca soluções por sintoma"""
    try:
        symptom = request.args.get('symptom', '').strip()
        
        if not symptom:
            return jsonify({
                "success": False,
                "message": "Parâmetro 'symptom' é obrigatório"
            }), 400
        
        # Buscar soluções
        solutions = troubleshooting_guide.search_solutions(symptom)
        
        # Formatar resultados
        results = []
        for solution in solutions:
            results.append({
                "id": solution.problem_id,
                "title": solution.title,
                "description": solution.description,
                "severity": solution.severity,
                "matching_symptoms": [
                    s for s in solution.symptoms 
                    if symptom.lower() in s.lower()
                ]
            })
        
        return jsonify({
            "success": True,
            "data": results,
            "message": f"Encontradas {len(results)} soluções para '{symptom}'"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na busca: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Erro na busca"
        }), 500

@troubleshooting_bp.route('/emergency', methods=['GET'])
def get_emergency_procedures():
    """Retorna procedimentos de emergência"""
    try:
        procedures = troubleshooting_guide.get_emergency_procedures()
        
        return jsonify({
            "success": True,
            "data": procedures,
            "message": "Procedimentos de emergência carregados"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao carregar procedimentos: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Erro ao carregar procedimentos"
        }), 500

@troubleshooting_bp.route('/quick-fixes', methods=['GET'])
def get_quick_fixes():
    """Retorna correções rápidas para problemas comuns"""
    try:
        fixes = troubleshooting_guide.get_quick_fixes()
        
        return jsonify({
            "success": True,
            "data": fixes,
            "message": "Correções rápidas carregadas"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao carregar correções: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Erro ao carregar correções"
        }), 500

@troubleshooting_bp.route('/health-check', methods=['GET'])
def health_check():
    """Verifica saúde básica do sistema de troubleshooting"""
    try:
        # Verificações básicas
        checks = {
            "diagnostic_system": diagnostic_system is not None,
            "troubleshooting_guide": troubleshooting_guide is not None,
            "solutions_loaded": len(troubleshooting_guide.solutions) > 0,
            "timestamp": datetime.now().isoformat()
        }
        
        all_healthy = all(checks.values())
        
        return jsonify({
            "success": True,
            "healthy": all_healthy,
            "checks": checks,
            "message": "Sistema de troubleshooting operacional" if all_healthy else "Problemas detectados"
        }), 200 if all_healthy else 503
        
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        return jsonify({
            "success": False,
            "healthy": False,
            "error": str(e),
            "message": "Erro no health check"
        }), 500

@troubleshooting_bp.route('/test/<test_name>', methods=['POST'])
def run_specific_test(test_name: str):
    """Executa um teste específico do sistema de diagnóstico"""
    try:
        # Mapear nomes de testes para métodos
        test_methods = {
            'network': diagnostic_system._test_network_connectivity,
            'environment': diagnostic_system._test_environment_config,
            'glpi': diagnostic_system._test_glpi_connectivity,
            'legacy': diagnostic_system._test_legacy_services,
            'performance': diagnostic_system._test_system_performance,
            'dependencies': diagnostic_system._test_python_dependencies,
            'logs': diagnostic_system._test_logs_and_files,
            'cache': diagnostic_system._test_cache_and_memory
        }
        
        if test_name not in test_methods:
            return jsonify({
                "success": False,
                "message": f"Teste '{test_name}' não encontrado",
                "available_tests": list(test_methods.keys())
            }), 400
        
        # Executar teste específico
        result = test_methods[test_name]()
        
        # Converter resultado para dict
        result_data = {
            "test_name": result.test_name,
            "status": result.status,
            "message": result.message,
            "details": result.details,
            "solution": result.solution
        }
        
        return jsonify({
            "success": True,
            "data": result_data,
            "message": f"Teste '{test_name}' executado"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao executar teste {test_name}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": f"Erro ao executar teste '{test_name}'"
        }), 500

# Função para registrar o blueprint
def register_troubleshooting_routes(app):
    """Registra as rotas de troubleshooting na aplicação Flask"""
    app.register_blueprint(troubleshooting_bp)
    logger.info("Rotas de troubleshooting registradas")