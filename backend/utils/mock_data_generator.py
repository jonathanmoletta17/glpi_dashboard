"""
Mock Data Generator - Gera dados mock realistas para desenvolvimento e testes da interface

Quando USE_MOCK_DATA=true no .env, o sistema usa estes dados ao invés de chamar a API GLPI real.
Isso permite validar a interface sem depender da conectividade com o GLPI.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random

from schemas.dashboard import (
    DashboardMetrics,
    LevelMetrics,
    NiveisMetrics,
    TendenciasMetrics,
    TechnicianRanking,
    NewTicket,
)


class MockDataGenerator:
    """Gera dados mock realistas para desenvolvimento"""

    def __init__(self):
        self.technician_names = [
            "João Silva",
            "Maria Santos",
            "Pedro Oliveira",
            "Ana Costa",
            "Carlos Ferreira",
            "Lucia Almeida",
            "Rafael Souza",
            "Fernanda Lima",
            "Gabriel Mendes",
            "Juliana Rocha",
            "Bruno Cardoso",
            "Patricia Dias",
        ]

        self.categories = [
            "Hardware",
            "Software",
            "Rede",
            "Impressora",
            "Sistema",
            "Email",
            "Telefone",
            "Acesso",
            "Backup",
            "Segurança",
        ]

        self.priorities = ["Muito baixa", "Baixa", "Média", "Alta", "Muito alta"]

        self.statuses = ["Novo", "Atribuído", "Planejado", "Pendente", "Resolvido", "Fechado"]

    def generate_dashboard_metrics(self, filters: Optional[Dict[str, Any]] = None) -> DashboardMetrics:
        """Gera métricas mock para o dashboard baseadas nos dados reais esperados"""

        # Dados baseados na realidade do GLPI: N3 > N2 > N1 > N4, total 10.000+ tickets
        # N3 é o nível com mais tickets
        n3_metrics = LevelMetrics(
            novos=random.randint(200, 300),
            pendentes=random.randint(400, 600),
            progresso=random.randint(150, 250),
            resolvidos=random.randint(2000, 3000),
        )

        # N2 é o segundo maior
        n2_metrics = LevelMetrics(
            novos=random.randint(150, 250),
            pendentes=random.randint(300, 500),
            progresso=random.randint(100, 200),
            resolvidos=random.randint(1500, 2500),
        )

        # N1 é o terceiro
        n1_metrics = LevelMetrics(
            novos=random.randint(100, 200),
            pendentes=random.randint(200, 400),
            progresso=random.randint(80, 150),
            resolvidos=random.randint(800, 1500),
        )

        # N4 tem menos de 100 tickets
        n4_metrics = LevelMetrics(
            novos=random.randint(5, 15),
            pendentes=random.randint(10, 25),
            progresso=random.randint(5, 15),
            resolvidos=random.randint(30, 80),
        )

        niveis = NiveisMetrics(n1=n1_metrics, n2=n2_metrics, n3=n3_metrics, n4=n4_metrics)

        # Calcular totais
        total_novos = n1_metrics.novos + n2_metrics.novos + n3_metrics.novos + n4_metrics.novos
        total_pendentes = n1_metrics.pendentes + n2_metrics.pendentes + n3_metrics.pendentes + n4_metrics.pendentes
        total_progresso = n1_metrics.progresso + n2_metrics.progresso + n3_metrics.progresso + n4_metrics.progresso
        total_resolvidos = n1_metrics.resolvidos + n2_metrics.resolvidos + n3_metrics.resolvidos + n4_metrics.resolvidos
        total_geral = total_novos + total_pendentes + total_progresso + total_resolvidos

        # Tendências simuladas (variação percentual)
        tendencias = TendenciasMetrics(
            novos=f"+{random.randint(5, 15)}%",
            pendentes=f"-{random.randint(2, 8)}%",
            progresso=f"+{random.randint(10, 25)}%",
            resolvidos=f"+{random.randint(15, 35)}%",
        )

        return DashboardMetrics(
            novos=total_novos,
            pendentes=total_pendentes,
            progresso=total_progresso,
            resolvidos=total_resolvidos,
            total=total_geral,
            niveis=niveis,
            tendencias=tendencias,
            timestamp=datetime.now(),
        )

    def generate_technician_ranking(self, limit: int = 10) -> List[TechnicianRanking]:
        """Gera ranking mock de técnicos baseado nos dados reais"""

        # Técnicos reais do GLPI com seus níveis e performance
        real_technicians = [
            {"name": "Anderson", "level": "N3", "ticket_count": random.randint(800, 1200), "performance_score": 4.8},
            {"name": "Silvio", "level": "N3", "ticket_count": random.randint(600, 900), "performance_score": 4.6},
            {"name": "Jorge", "level": "N3", "ticket_count": random.randint(500, 800), "performance_score": 4.5},
            {"name": "Pablo", "level": "N3", "ticket_count": random.randint(400, 700), "performance_score": 4.4},
            {"name": "Miguel", "level": "N3", "ticket_count": random.randint(300, 600), "performance_score": 4.3},
            {"name": "João Dias", "level": "N2", "ticket_count": 1, "performance_score": 3.5},
        ]

        technicians = []

        # Adicionar técnicos reais
        for i, tech in enumerate(real_technicians):
            technicians.append(
                TechnicianRanking(
                    id=i + 1,
                    name=tech["name"],
                    ticket_count=tech["ticket_count"],
                    level=tech["level"],
                    performance_score=tech["performance_score"]
                )
            )

        # Adicionar técnicos adicionais se necessário
        if limit > len(real_technicians):
            additional_techs = [
                "Carlos Silva", "Ana Costa", "Pedro Santos", "Maria Oliveira", "Rafael Lima"
            ]

            for i in range(len(real_technicians), min(limit, len(real_technicians) + len(additional_techs))):
                name = additional_techs[i - len(real_technicians)]
                level = random.choice(["N1", "N2", "N3"])
                if level == "N1":
                    ticket_count = random.randint(50, 100)
                    performance_score = random.uniform(3.8, 4.5)
                elif level == "N2":
                    ticket_count = random.randint(20, 50)
                    performance_score = random.uniform(4.0, 4.7)
                else:  # N3
                    ticket_count = random.randint(10, 30)
                    performance_score = random.uniform(4.2, 4.8)

                technicians.append(
                    TechnicianRanking(
                        id=i + 1,
                        name=name,
                        ticket_count=ticket_count,
                        level=level,
                        performance_score=round(performance_score, 2)
                    )
                )

        # Ordenar por ticket_count (ranking) - Anderson deve ser o primeiro
        technicians.sort(key=lambda x: x.ticket_count, reverse=True)

        return technicians

    def generate_new_tickets(self, limit: int = 20) -> List[NewTicket]:
        """Gera lista mock de tickets novos baseada nos dados reais"""

        tickets = []
        base_date = datetime.now()

        # Ticket real "teste dashboard" sempre incluído
        if limit > 0:
            ticket_teste = NewTicket(
                id="TESTE001",
                title="Teste Dashboard GLPI",
                description="Ticket de teste para validação do dashboard GLPI - verificar exibição de dados",
                date=(base_date - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                requester="admin@empresa.com",
                priority="Média",
                status="Novo",
            )
            tickets.append(ticket_teste)

        # Gerar tickets adicionais
        for i in range(1, limit):
            # Datas recentes (últimas 24-48 horas)
            hours_ago = random.randint(1, 48)
            ticket_date = base_date - timedelta(hours=hours_ago)

            ticket = NewTicket(
                id=str(10000 + i),
                title=self._generate_ticket_title(),
                description=self._generate_ticket_description(),
                date=ticket_date.strftime("%Y-%m-%d %H:%M:%S"),
                requester=f"usuario{i + 1}@empresa.com",
                priority=random.choice(self.priorities),
                status="Novo",
            )

            tickets.append(ticket)

        return tickets

    def generate_system_status(self) -> Dict[str, Any]:
        """Gera status mock do sistema"""

        return {
            "status": "healthy",
            "glpi_connection": "connected",
            "cache_status": "operational",
            "last_sync": datetime.now().isoformat(),
            "total_tickets": random.randint(2500, 3500),
            "active_technicians": random.randint(45, 60),
            "response_time_avg": round(random.uniform(150, 300), 2),
            "uptime_hours": random.randint(168, 720),  # Entre 1 semana e 1 mês
        }

    def _generate_ticket_title(self) -> str:
        """Gera títulos realistas para tickets"""

        templates = [
            f"Problema com {random.choice(self.categories).lower()}",
            f"Solicitação de {random.choice(['acesso', 'instalação', 'configuração', 'suporte'])}",
            f"Erro em {random.choice(['sistema', 'aplicação', 'equipamento'])}",
            f"Falha de {random.choice(['conexão', 'impressão', 'login', 'backup'])}",
            f"Dúvida sobre {random.choice(['funcionamento', 'procedimento', 'acesso'])}",
        ]

        return random.choice(templates)

    def _generate_ticket_description(self) -> str:
        """Gera descrições realistas para tickets"""

        descriptions = [
            "Usuário reporta intermitência no funcionamento. Necessário investigação técnica.",
            "Sistema apresentando lentidão significativa durante operações rotineiras.",
            "Erro recorrente impedindo conclusão das atividades. Urgente análise.",
            "Equipamento não responde adequadamente. Possível problema de hardware.",
            "Dificuldade de acesso após atualização recente. Verificar configurações.",
            "Funcionalidade indisponível causando impacto nas operações diárias.",
        ]

        return random.choice(descriptions)


# Instância global para uso em toda aplicação
mock_generator = MockDataGenerator()


def get_mock_dashboard_metrics(filters: Optional[Dict[str, Any]] = None) -> DashboardMetrics:
    """Retorna métricas mock do dashboard"""
    return mock_generator.generate_dashboard_metrics(filters)


def get_mock_technician_ranking(limit: int = 10) -> List[TechnicianRanking]:
    """Retorna ranking mock de técnicos"""
    return mock_generator.generate_technician_ranking(limit)


def get_mock_new_tickets(limit: int = 20) -> List[NewTicket]:
    """Retorna tickets novos mock"""
    return mock_generator.generate_new_tickets(limit)


def get_mock_system_status() -> Dict[str, Any]:
    """Retorna status mock do sistema"""
    return mock_generator.generate_system_status()
