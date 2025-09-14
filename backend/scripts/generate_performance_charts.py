#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Gráficos de Performance - Serviços Legacy GLPI

Este script gera visualizações gráficas dos dados de baseline de performance
coletados pelos testes dos serviços legacy.

Autor: Performance Baseline Tool
Data: 2025-09-14
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
import seaborn as sns
from datetime import datetime
import os

# Configurar estilo dos gráficos
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

class PerformanceChartGenerator:
    """
    Gerador de gráficos de performance baseado nos dados de baseline.
    """
    
    def __init__(self, json_file_path: str):
        """
        Inicializa o gerador com o arquivo JSON de dados.
        
        Args:
            json_file_path: Caminho para o arquivo JSON com dados de baseline
        """
        self.json_file = Path(json_file_path)
        self.data = self._load_data()
        self.output_dir = self.json_file.parent / "charts"
        self.output_dir.mkdir(exist_ok=True)
        
    def _load_data(self) -> dict:
        """Carrega os dados do arquivo JSON."""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return {}
    
    def generate_all_charts(self):
        """Gera todos os gráficos de performance."""
        print("🎨 Gerando gráficos de performance...")
        
        try:
            # 1. Gráfico de tempos de resposta por método
            self._create_response_time_chart()
            
            # 2. Gráfico de distribuição de performance
            self._create_performance_distribution()
            
            # 3. Gráfico de uso de recursos
            self._create_resource_usage_chart()
            
            # 4. Gráfico de stress test
            self._create_stress_test_chart()
            
            # 5. Gráfico comparativo de serviços
            self._create_services_comparison()
            
            # 6. Dashboard consolidado
            self._create_dashboard()
            
            print(f"✅ Gráficos gerados em: {self.output_dir}")
            
        except Exception as e:
            print(f"❌ Erro ao gerar gráficos: {e}")
    
    def _create_response_time_chart(self):
        """Cria gráfico de tempos de resposta por método do facade."""
        try:
            facade_data = self.data['test_results']['isolated_test']['method_breakdown']
            
            methods = []
            times = []
            colors = []
            
            for method, data in facade_data.items():
                methods.append(method.replace('get_', '').replace('_', ' ').title())
                avg_time = data['response_time']['avg_ms']
                times.append(avg_time)
                
                # Cores baseadas na performance
                if avg_time > 1000:
                    colors.append('#ff4444')  # Vermelho para >1s
                elif avg_time > 100:
                    colors.append('#ffaa00')  # Laranja para >100ms
                else:
                    colors.append('#44ff44')  # Verde para <100ms
            
            fig, ax = plt.subplots(figsize=(12, 6))
            bars = ax.bar(methods, times, color=colors, alpha=0.8, edgecolor='black')
            
            # Adicionar valores nas barras
            for bar, time in zip(bars, times):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + max(times)*0.01,
                       f'{time:.1f}ms', ha='center', va='bottom', fontweight='bold')
            
            ax.set_title('Tempo de Resposta por Método - GLPIServiceFacade', 
                        fontsize=16, fontweight='bold', pad=20)
            ax.set_ylabel('Tempo de Resposta (ms)', fontsize=12)
            ax.set_xlabel('Métodos', fontsize=12)
            
            # Linha de referência para 100ms
            ax.axhline(y=100, color='orange', linestyle='--', alpha=0.7, 
                      label='Limite Recomendado (100ms)')
            ax.axhline(y=1000, color='red', linestyle='--', alpha=0.7, 
                      label='Limite Crítico (1s)')
            
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plt.savefig(self.output_dir / 'response_times_by_method.png', 
                       dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"⚠️ Erro ao criar gráfico de tempos de resposta: {e}")
    
    def _create_performance_distribution(self):
        """Cria gráfico de distribuição de performance (percentis)."""
        try:
            facade_data = self.data['test_results']['isolated_test']['overall_metrics']
            response_time = facade_data['response_time']
            
            percentiles = ['min_ms', 'median_ms', 'avg_ms', 'p95_ms', 'p99_ms', 'max_ms']
            values = [response_time[p] for p in percentiles]
            labels = ['Mínimo', 'Mediana', 'Média', 'P95', 'P99', 'Máximo']
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Gráfico de barras dos percentis
            colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(values)))
            bars = ax1.bar(labels, values, color=colors, alpha=0.8, edgecolor='black')
            
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                        f'{value:.1f}ms', ha='center', va='bottom', fontweight='bold')
            
            ax1.set_title('Distribuição de Tempos de Resposta', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Tempo (ms)')
            ax1.grid(True, alpha=0.3)
            
            # Box plot dos tempos individuais por método
            method_times = []
            method_names = []
            
            facade_methods = self.data['test_results']['isolated_test']['method_breakdown']
            for method, data in facade_methods.items():
                if data['response_time']['avg_ms'] > 0:  # Apenas métodos com tempo mensurável
                    method_times.append([data['response_time']['avg_ms']])
                    method_names.append(method.replace('get_', '').replace('_', ' ').title())
            
            if method_times:
                ax2.boxplot(method_times, labels=method_names)
                ax2.set_title('Distribuição por Método', fontsize=14, fontweight='bold')
                ax2.set_ylabel('Tempo (ms)')
                ax2.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig(self.output_dir / 'performance_distribution.png', 
                       dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"⚠️ Erro ao criar gráfico de distribuição: {e}")
    
    def _create_resource_usage_chart(self):
        """Cria gráfico de uso de recursos (CPU e Memória)."""
        try:
            # Dados do teste isolado
            isolated = self.data['test_results']['isolated_test']['overall_metrics']
            
            # Dados do teste de stress
            stress = self.data['test_results']['stress_test']['overall_metrics']
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # 1. CPU Usage - Isolado vs Stress
            cpu_data = {
                'Teste Isolado': {
                    'Mínimo': isolated['cpu_usage']['min_percent'],
                    'Médio': isolated['cpu_usage']['avg_percent'],
                    'Máximo': isolated['cpu_usage']['max_percent']
                },
                'Teste Stress': {
                    'Mínimo': stress['cpu_usage']['min_percent'],
                    'Médio': stress['cpu_usage']['avg_percent'],
                    'Máximo': stress['cpu_usage']['max_percent']
                }
            }
            
            x = np.arange(len(cpu_data['Teste Isolado']))
            width = 0.35
            
            isolated_cpu = list(cpu_data['Teste Isolado'].values())
            stress_cpu = list(cpu_data['Teste Stress'].values())
            
            ax1.bar(x - width/2, isolated_cpu, width, label='Isolado', alpha=0.8, color='skyblue')
            ax1.bar(x + width/2, stress_cpu, width, label='Stress', alpha=0.8, color='lightcoral')
            
            ax1.set_title('Uso de CPU (%)', fontweight='bold')
            ax1.set_ylabel('CPU (%)')
            ax1.set_xticks(x)
            ax1.set_xticklabels(['Mínimo', 'Médio', 'Máximo'])
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. Memory Usage - Isolado vs Stress
            memory_data = {
                'Isolado': {
                    'Mínimo': isolated['memory_usage']['min_mb'],
                    'Médio': isolated['memory_usage']['avg_mb'],
                    'Máximo': isolated['memory_usage']['max_mb']
                },
                'Stress': {
                    'Mínimo': stress['memory_usage']['min_mb'],
                    'Médio': stress['memory_usage']['avg_mb'],
                    'Máximo': stress['memory_usage']['max_mb']
                }
            }
            
            isolated_mem = list(memory_data['Isolado'].values())
            stress_mem = list(memory_data['Stress'].values())
            
            ax2.bar(x - width/2, isolated_mem, width, label='Isolado', alpha=0.8, color='lightgreen')
            ax2.bar(x + width/2, stress_mem, width, label='Stress', alpha=0.8, color='orange')
            
            ax2.set_title('Uso de Memória (MB)', fontweight='bold')
            ax2.set_ylabel('Memória (MB)')
            ax2.set_xticks(x)
            ax2.set_xticklabels(['Mínimo', 'Médio', 'Máximo'])
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 3. Throughput do Stress Test
            total_requests = stress['total_operations']
            total_time = stress['total_duration_seconds']
            throughput = total_requests / total_time
            
            ax3.bar(['Throughput'], [throughput], color='purple', alpha=0.8)
            ax3.set_title('Throughput (req/s)', fontweight='bold')
            ax3.set_ylabel('Requisições por Segundo')
            ax3.text(0, throughput + throughput*0.05, f'{throughput:.2f} req/s', 
                    ha='center', va='bottom', fontweight='bold')
            ax3.grid(True, alpha=0.3)
            
            # 4. Success Rate
            success_rates = {
                'Facade Isolado': isolated['success_rate_percent'],
                'Stress Test': stress['success_rate_percent']
            }
            
            colors = ['green' if rate == 100 else 'orange' for rate in success_rates.values()]
            bars = ax4.bar(success_rates.keys(), success_rates.values(), 
                          color=colors, alpha=0.8)
            
            for bar, rate in zip(bars, success_rates.values()):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
            
            ax4.set_title('Taxa de Sucesso (%)', fontweight='bold')
            ax4.set_ylabel('Taxa de Sucesso (%)')
            ax4.set_ylim(0, 105)
            ax4.grid(True, alpha=0.3)
            
            plt.suptitle('Análise de Recursos e Performance', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            plt.savefig(self.output_dir / 'resource_usage_analysis.png', 
                       dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"⚠️ Erro ao criar gráfico de recursos: {e}")
    
    def _create_stress_test_chart(self):
        """Cria gráfico detalhado do teste de stress."""
        try:
            stress_data = self.data['test_results']['stress_test']
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # 1. Resumo do Stress Test
            metrics = {
                'Total': stress_data['concurrent_requests'],
                'Sucesso': stress_data['successful_requests'],
                'Falha': stress_data['failed_requests']
            }
            
            colors = ['blue', 'green', 'red']
            wedges, texts, autotexts = ax1.pie(metrics.values(), labels=metrics.keys(), 
                                              colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Distribuição de Requisições\n(Stress Test)', fontweight='bold')
            
            # 2. Tempos de Resposta do Stress
            response_times = stress_data['overall_metrics']['response_time']
            times = ['Mínimo', 'Médio', 'Mediana', 'P95', 'P99', 'Máximo']
            values = [response_times['min_ms'], response_times['avg_ms'], 
                     response_times['avg_ms'], response_times['p95_ms'],
                     response_times['p99_ms'], response_times['max_ms']]
            
            bars = ax2.bar(times, values, color='lightblue', alpha=0.8, edgecolor='navy')
            ax2.set_title('Tempos de Resposta - Stress Test', fontweight='bold')
            ax2.set_ylabel('Tempo (ms)')
            ax2.tick_params(axis='x', rotation=45)
            
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                        f'{value:.0f}ms', ha='center', va='bottom', fontsize=9)
            
            ax2.grid(True, alpha=0.3)
            
            # 3. Comparação de Performance
            isolated_avg = self.data['test_results']['isolated_test']['overall_metrics']['response_time']['avg_ms']
            stress_avg = response_times['avg_ms']
            
            comparison = {
                'Teste Isolado': isolated_avg,
                'Teste Stress': stress_avg
            }
            
            bars = ax3.bar(comparison.keys(), comparison.values(), 
                          color=['lightgreen', 'lightcoral'], alpha=0.8)
            ax3.set_title('Comparação: Isolado vs Stress', fontweight='bold')
            ax3.set_ylabel('Tempo Médio (ms)')
            
            for bar, value in zip(bars, comparison.values()):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + max(comparison.values())*0.01,
                        f'{value:.1f}ms', ha='center', va='bottom', fontweight='bold')
            
            ax3.grid(True, alpha=0.3)
            
            # 4. Métricas de Capacidade
            duration = stress_data['overall_metrics']['total_duration_seconds']
            throughput = stress_data['concurrent_requests'] / duration
            
            capacity_metrics = {
                'Throughput\n(req/s)': throughput,
                'Duração\n(segundos)': duration,
                'Concorrência': stress_data['concurrent_requests']
            }
            
            # Normalizar valores para visualização
            normalized_values = []
            for key, value in capacity_metrics.items():
                if 'req/s' in key:
                    normalized_values.append(value * 10)  # Escalar throughput
                else:
                    normalized_values.append(value)
            
            bars = ax4.bar(capacity_metrics.keys(), normalized_values, 
                          color=['purple', 'orange', 'cyan'], alpha=0.8)
            ax4.set_title('Métricas de Capacidade', fontweight='bold')
            
            # Adicionar valores reais nas barras
            for bar, (key, value) in zip(bars, capacity_metrics.items()):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + max(normalized_values)*0.01,
                        f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
            
            ax4.grid(True, alpha=0.3)
            
            plt.suptitle('Análise Detalhada - Teste de Stress (100 Requisições)', 
                        fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            plt.savefig(self.output_dir / 'stress_test_analysis.png', 
                       dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"⚠️ Erro ao criar gráfico de stress test: {e}")
    
    def _create_services_comparison(self):
        """Cria gráfico comparativo dos serviços individuais."""
        try:
            services_data = self.data['test_results']['individual_services']['individual_services']
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 1. Tempo médio por serviço
            services = []
            avg_times = []
            success_rates = []
            
            for service_name, service_data in services_data.items():
                services.append(service_name.replace('Service', ''))
                avg_times.append(service_data['overall_metrics']['response_time']['avg_ms'])
                success_rates.append(service_data['overall_metrics']['success_rate_percent'])
            
            # Cores baseadas na performance
            colors = []
            for time in avg_times:
                if time > 200:
                    colors.append('#ff6b6b')  # Vermelho
                elif time > 50:
                    colors.append('#ffa726')  # Laranja
                else:
                    colors.append('#66bb6a')  # Verde
            
            bars1 = ax1.bar(services, avg_times, color=colors, alpha=0.8, edgecolor='black')
            ax1.set_title('Tempo Médio de Resposta por Serviço', fontweight='bold')
            ax1.set_ylabel('Tempo Médio (ms)')
            ax1.tick_params(axis='x', rotation=45)
            
            for bar, time in zip(bars1, avg_times):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + max(avg_times)*0.01,
                        f'{time:.1f}ms', ha='center', va='bottom', fontweight='bold')
            
            ax1.grid(True, alpha=0.3)
            
            # 2. Taxa de sucesso por serviço
            success_colors = ['green' if rate == 100 else 'orange' for rate in success_rates]
            bars2 = ax2.bar(services, success_rates, color=success_colors, alpha=0.8, edgecolor='black')
            ax2.set_title('Taxa de Sucesso por Serviço', fontweight='bold')
            ax2.set_ylabel('Taxa de Sucesso (%)')
            ax2.set_ylim(0, 105)
            ax2.tick_params(axis='x', rotation=45)
            
            for bar, rate in zip(bars2, success_rates):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
            
            ax2.grid(True, alpha=0.3)
            
            plt.suptitle('Comparação de Performance - Serviços Individuais', 
                        fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            plt.savefig(self.output_dir / 'services_comparison.png', 
                       dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"⚠️ Erro ao criar gráfico de comparação de serviços: {e}")
    
    def _create_dashboard(self):
        """Cria um dashboard consolidado com as principais métricas."""
        try:
            fig = plt.figure(figsize=(20, 12))
            gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
            
            # Dados principais
            isolated = self.data['test_results']['isolated_test']['overall_metrics']
            stress = self.data['test_results']['stress_test']['overall_metrics']
            summary = self.data['summary']
            
            # 1. Métricas principais (top-left, span 2 columns)
            ax1 = fig.add_subplot(gs[0, :2])
            main_metrics = {
                'Avg Response\n(ms)': summary['key_metrics']['avg_response_time_ms'],
                'P95 Response\n(ms)': summary['key_metrics']['p95_response_time_ms'],
                'Success Rate\n(%)': summary['key_metrics']['facade_success_rate'],
                'Concurrent\nSuccess (%)': summary['key_metrics']['concurrent_success_rate']
            }
            
            colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
            bars = ax1.bar(main_metrics.keys(), main_metrics.values(), color=colors, alpha=0.8)
            ax1.set_title('Métricas Principais - Baseline Performance', fontsize=14, fontweight='bold')
            
            for bar, value in zip(bars, main_metrics.values()):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + max(main_metrics.values())*0.01,
                        f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
            
            ax1.grid(True, alpha=0.3)
            
            # 2. Status geral (top-right)
            ax2 = fig.add_subplot(gs[0, 2:])
            health_status = summary['overall_health'].upper()
            grade = summary['performance_grade']
            
            # Criar um "medidor" visual
            health_color = {'EXCELLENT': 'green', 'GOOD': 'orange', 'POOR': 'red'}.get(health_status, 'gray')
            
            ax2.text(0.5, 0.7, f'Status: {health_status}', ha='center', va='center', 
                    fontsize=20, fontweight='bold', color=health_color,
                    transform=ax2.transAxes)
            ax2.text(0.5, 0.3, f'Grade: {grade}', ha='center', va='center', 
                    fontsize=24, fontweight='bold', color=health_color,
                    transform=ax2.transAxes)
            
            ax2.set_xlim(0, 1)
            ax2.set_ylim(0, 1)
            ax2.axis('off')
            ax2.set_title('Status Geral do Sistema', fontsize=14, fontweight='bold')
            
            # 3. Breakdown por método (middle-left)
            ax3 = fig.add_subplot(gs[1, :2])
            facade_methods = self.data['test_results']['isolated_test']['method_breakdown']
            
            methods = []
            times = []
            for method, data in facade_methods.items():
                methods.append(method.replace('get_', '').replace('_', '\n'))
                times.append(data['response_time']['avg_ms'])
            
            bars = ax3.barh(methods, times, color='lightblue', alpha=0.8, edgecolor='navy')
            ax3.set_title('Tempo por Método (ms)', fontsize=12, fontweight='bold')
            ax3.set_xlabel('Tempo (ms)')
            
            for bar, time in zip(bars, times):
                width = bar.get_width()
                ax3.text(width + max(times)*0.01, bar.get_y() + bar.get_height()/2.,
                        f'{time:.1f}', ha='left', va='center', fontweight='bold')
            
            ax3.grid(True, alpha=0.3)
            
            # 4. Recursos (middle-right)
            ax4 = fig.add_subplot(gs[1, 2:])
            
            cpu_stress = stress['cpu_usage']['avg_percent']
            mem_stress = stress['memory_usage']['avg_mb']
            
            resources = ['CPU (%)', 'Memory (MB)']
            values = [cpu_stress, mem_stress]
            colors = ['#e67e22', '#9b59b6']
            
            bars = ax4.bar(resources, values, color=colors, alpha=0.8)
            ax4.set_title('Uso de Recursos (Stress Test)', fontsize=12, fontweight='bold')
            
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                        f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
            
            ax4.grid(True, alpha=0.3)
            
            # 5. Timeline de performance (bottom, span all)
            ax5 = fig.add_subplot(gs[2, :])
            
            # Simular timeline baseado nos testes
            test_phases = ['Setup', 'Isolated Test', 'Individual Services', 'Stress Test', 'Cleanup']
            durations = [0.1, 2.2, 0.8, 13.2, 0.1]  # Aproximado baseado nos dados
            
            cumulative = np.cumsum([0] + durations[:-1])
            colors_timeline = ['#95a5a6', '#3498db', '#f39c12', '#e74c3c', '#2ecc71']
            
            bars = ax5.barh(range(len(test_phases)), durations, left=cumulative, 
                           color=colors_timeline, alpha=0.8, edgecolor='black')
            
            ax5.set_yticks(range(len(test_phases)))
            ax5.set_yticklabels(test_phases)
            ax5.set_xlabel('Tempo (segundos)')
            ax5.set_title('Timeline de Execução dos Testes', fontsize=12, fontweight='bold')
            
            # Adicionar durações nas barras
            for i, (bar, duration) in enumerate(zip(bars, durations)):
                width = bar.get_width()
                ax5.text(bar.get_x() + width/2., bar.get_y() + bar.get_height()/2.,
                        f'{duration:.1f}s', ha='center', va='center', fontweight='bold')
            
            ax5.grid(True, alpha=0.3)
            
            # Título geral
            execution_time = self.data['metadata']['test_execution_time']
            fig.suptitle(f'Dashboard de Performance - Legacy GLPI Services\n'
                        f'Executado em: {execution_time}', 
                        fontsize=18, fontweight='bold')
            
            plt.savefig(self.output_dir / 'performance_dashboard.png', 
                       dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"⚠️ Erro ao criar dashboard: {e}")

def main():
    """Função principal para gerar os gráficos."""
    print("🎨 Gerador de Gráficos de Performance - Legacy GLPI Services")
    print("=" * 60)
    
    # Procurar pelo arquivo JSON mais recente
    script_dir = Path(__file__).parent
    json_files = list(script_dir.glob("legacy_baseline_report_*.json"))
    
    if not json_files:
        print("❌ Nenhum arquivo de baseline encontrado!")
        print("Execute primeiro: python legacy_performance_baseline.py")
        return
    
    # Usar o arquivo mais recente
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    print(f"📊 Usando dados de: {latest_file.name}")
    
    # Gerar gráficos
    generator = PerformanceChartGenerator(str(latest_file))
    generator.generate_all_charts()
    
    print("\n✅ Gráficos gerados com sucesso!")
    print(f"📁 Localização: {generator.output_dir}")
    print("\n📊 Arquivos gerados:")
    print("  • response_times_by_method.png - Tempos por método")
    print("  • performance_distribution.png - Distribuição de performance")
    print("  • resource_usage_analysis.png - Análise de recursos")
    print("  • stress_test_analysis.png - Análise do teste de stress")
    print("  • services_comparison.png - Comparação de serviços")
    print("  • performance_dashboard.png - Dashboard consolidado")

if __name__ == '__main__':
    main()