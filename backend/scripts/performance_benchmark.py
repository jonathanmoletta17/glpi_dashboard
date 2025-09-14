#!/usr/bin/env python3
"""
Performance Benchmark Script - Legacy vs New Architecture
Compares performance between legacy GLPIService and new Clean Architecture
"""

import asyncio
import json
import statistics
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import psutil
import requests
from urllib.parse import urljoin

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PerformanceBenchmark:
    """Comprehensive performance benchmark for GLPI Dashboard architecture comparison."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", iterations: int = 10):
        self.base_url = base_url.rstrip("/")
        self.iterations = iterations
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "iterations": iterations,
            "legacy_results": {},
            "new_architecture_results": {},
            "comparison": {},
            "memory_usage": {},
            "cache_analysis": {},
        }

    def measure_memory_usage(self) -> Dict[str, float]:
        """Measure current memory usage of the process."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,  # MB
                "vms_mb": memory_info.vms / 1024 / 1024,  # MB
                "percent": process.memory_percent(),
            }
        except Exception as e:
            print(f"Warning: Could not measure memory usage: {e}")
            return {"rss_mb": 0, "vms_mb": 0, "percent": 0}

    def make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request and measure performance."""
        url = urljoin(f"{self.base_url}/api/", endpoint)

        start_memory = self.measure_memory_usage()
        start_time = time.time()

        try:
            response = requests.get(url, params=params or {}, timeout=30)
            end_time = time.time()
            end_memory = self.measure_memory_usage()

            response_time = (end_time - start_time) * 1000  # ms

            result = {
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "response_size_bytes": len(response.content),
                "memory_before_mb": start_memory["rss_mb"],
                "memory_after_mb": end_memory["rss_mb"],
                "memory_delta_mb": end_memory["rss_mb"] - start_memory["rss_mb"],
                "success": response.status_code == 200,
            }

            if response.status_code == 200:
                try:
                    data = response.json()
                    result["cached"] = data.get("cached", False)
                    result["response_data_size"] = len(str(data))
                except Exception as parse_error:
                    result["cached"] = False
                    result["response_data_size"] = len(response.content)
                    result["json_parse_error"] = str(parse_error)
            else:
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                result["cached"] = False
                result["response_data_size"] = 0

            return result

        except Exception as e:
            end_time = time.time()
            return {
                "status_code": 0,
                "response_time_ms": (end_time - start_time) * 1000,
                "response_size_bytes": 0,
                "memory_before_mb": start_memory["rss_mb"],
                "memory_after_mb": start_memory["rss_mb"],
                "memory_delta_mb": 0,
                "success": False,
                "error": str(e),
                "cached": False,
                "response_data_size": 0,
            }

    def benchmark_endpoint(self, endpoint: str, params: Optional[Dict] = None, name: str = "") -> Dict[str, Any]:
        """Benchmark a single endpoint with multiple iterations."""
        print(f"\n🔍 Benchmarking {name or endpoint}...")

        results = []
        cache_hits = 0

        # Clear potential cache first with a dummy request
        self.make_request(endpoint, {"cache_buster": str(time.time())})
        time.sleep(0.1)

        for i in range(self.iterations):
            print(f"  Iteration {i+1}/{self.iterations}", end=" ")
            result = self.make_request(endpoint, params)
            results.append(result)

            if result["cached"]:
                cache_hits += 1
                print("(cached)")
            elif result["success"]:
                print("✓")
            else:
                print(f"✗ {result.get('error', 'Failed')}")

            # Small delay between requests
            time.sleep(0.05)

        # Calculate statistics
        successful_results = [r for r in results if r["success"]]

        if not successful_results:
            return {"endpoint": endpoint, "name": name, "success_rate": 0, "error": "All requests failed", "results": results}

        response_times = [r["response_time_ms"] for r in successful_results]
        memory_deltas = [r["memory_delta_mb"] for r in successful_results]
        response_sizes = [r["response_size_bytes"] for r in successful_results]

        analysis = {
            "endpoint": endpoint,
            "name": name,
            "success_rate": len(successful_results) / len(results),
            "total_requests": len(results),
            "successful_requests": len(successful_results),
            "cache_hit_rate": cache_hits / len(results),
            "cache_hits": cache_hits,
            # Response time statistics
            "response_time": {
                "min_ms": min(response_times),
                "max_ms": max(response_times),
                "mean_ms": statistics.mean(response_times),
                "median_ms": statistics.median(response_times),
                "stdev_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                "p95_ms": self._percentile(response_times, 95),
                "p99_ms": self._percentile(response_times, 99),
            },
            # Memory usage statistics
            "memory_usage": {
                "mean_delta_mb": statistics.mean(memory_deltas),
                "max_delta_mb": max(memory_deltas),
                "total_delta_mb": sum(memory_deltas),
            },
            # Response size statistics
            "response_size": {
                "mean_bytes": statistics.mean(response_sizes),
                "max_bytes": max(response_sizes),
                "min_bytes": min(response_sizes),
            },
            # Throughput (requests per second)
            "throughput_rps": len(successful_results) / (sum(response_times) / 1000) if response_times else 0,
            "raw_results": results,
        }

        return analysis

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (percentile / 100)
        f = int(k)
        c = k - f
        if f == len(sorted_data) - 1:
            return sorted_data[f]
        return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c

    def run_metrics_comparison(self) -> None:
        """Compare legacy vs new architecture metrics endpoints using demo data."""
        print("🚀 Starting GLPI Dashboard Performance Benchmark (Demo Mode)")
        print(f"Base URL: {self.base_url}")
        print(f"Iterations per test: {self.iterations}")
        print("=" * 60)

        # Test parameters for both endpoints
        test_params = {
            "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
        }

        print(f"Test parameters: {test_params}")
        print("Using demo endpoints with mock data for consistent benchmarking")

        # Benchmark legacy demo metrics endpoint
        legacy_results = self.benchmark_endpoint(
            "demo/metrics/legacy", test_params, "Legacy Architecture Demo (/api/demo/metrics/legacy)"
        )
        self.results["legacy_results"]["metrics"] = legacy_results

        # Small pause between tests
        time.sleep(0.5)

        # Benchmark new architecture demo metrics endpoint
        new_results = self.benchmark_endpoint("demo/metrics/new", test_params, "New Architecture Demo (/api/demo/metrics/new)")
        self.results["new_architecture_results"]["metrics"] = new_results

        # Calculate comparison
        self._calculate_comparison(legacy_results, new_results)

    def run_comprehensive_benchmark(self) -> None:
        """Run comprehensive benchmark of all available endpoints."""
        print("🔬 Running Comprehensive Architecture Benchmark")

        test_cases = [
            {
                "endpoint": "demo/metrics/legacy",
                "params": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
                "name": "Legacy Metrics",
            },
            {
                "endpoint": "demo/metrics/new",
                "params": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
                "name": "New Metrics",
            },
            {"endpoint": "demo/technicians/ranking/legacy", "params": {"limit": 50}, "name": "Legacy Technician Ranking"},
            {"endpoint": "demo/technicians/ranking/new", "params": {"limit": 50}, "name": "New Technician Ranking"},
            {"endpoint": "demo/status", "params": {}, "name": "Demo Status"},
        ]

        for test_case in test_cases:
            results = self.benchmark_endpoint(test_case["endpoint"], test_case["params"], test_case["name"])

            # Store results in appropriate category
            if "Legacy" in test_case["name"]:
                self.results["legacy_results"][test_case["endpoint"]] = results
            else:
                self.results["new_architecture_results"][test_case["endpoint"]] = results

    def _calculate_comparison(self, legacy: Dict, new: Dict) -> None:
        """Calculate performance comparison between legacy and new architecture."""
        if not legacy.get("response_time") or not new.get("response_time"):
            return

        comparison = {
            "response_time_improvement": {
                "legacy_mean_ms": legacy["response_time"]["mean_ms"],
                "new_mean_ms": new["response_time"]["mean_ms"],
                "improvement_percent": (
                    (legacy["response_time"]["mean_ms"] - new["response_time"]["mean_ms"]) / legacy["response_time"]["mean_ms"]
                )
                * 100,
                "improvement_factor": legacy["response_time"]["mean_ms"] / new["response_time"]["mean_ms"],
            },
            "memory_usage_comparison": {
                "legacy_mean_delta_mb": legacy["memory_usage"]["mean_delta_mb"],
                "new_mean_delta_mb": new["memory_usage"]["mean_delta_mb"],
                "memory_improvement_mb": legacy["memory_usage"]["mean_delta_mb"] - new["memory_usage"]["mean_delta_mb"],
            },
            "cache_effectiveness": {
                "legacy_cache_hit_rate": legacy["cache_hit_rate"],
                "new_cache_hit_rate": new["cache_hit_rate"],
                "cache_improvement": new["cache_hit_rate"] - legacy["cache_hit_rate"],
            },
            "throughput_comparison": {
                "legacy_rps": legacy["throughput_rps"],
                "new_rps": new["throughput_rps"],
                "throughput_improvement_percent": (
                    (new["throughput_rps"] - legacy["throughput_rps"]) / legacy["throughput_rps"]
                )
                * 100
                if legacy["throughput_rps"] > 0
                else 0,
            },
        }

        self.results["comparison"] = comparison

    def print_results(self) -> None:
        """Print formatted benchmark results."""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)

        if "comparison" in self.results and self.results["comparison"]:
            comp = self.results["comparison"]

            print("\n🏆 OVERALL PERFORMANCE COMPARISON:")
            print("-" * 50)

            rt = comp.get("response_time_improvement", {})
            if rt:
                print(f"⏱️  Response Time:")
                print(f"   Legacy:     {rt.get('legacy_mean_ms', 0):.2f} ms")
                print(f"   New:        {rt.get('new_mean_ms', 0):.2f} ms")
                improvement = rt.get("improvement_percent", 0)
                if improvement > 0:
                    print(f"   ✅ Improvement: {improvement:.1f}% faster")
                else:
                    print(f"   ❌ Regression: {abs(improvement):.1f}% slower")

            mem = comp.get("memory_usage_comparison", {})
            if mem:
                print(f"\n💾 Memory Usage:")
                print(f"   Legacy:     {mem.get('legacy_mean_delta_mb', 0):.3f} MB")
                print(f"   New:        {mem.get('new_mean_delta_mb', 0):.3f} MB")
                improvement = mem.get("memory_improvement_mb", 0)
                if improvement > 0:
                    print(f"   ✅ Improvement: {improvement:.3f} MB less")
                else:
                    print(f"   ❌ Regression: {abs(improvement):.3f} MB more")

            cache = comp.get("cache_effectiveness", {})
            if cache:
                print(f"\n📦 Cache Effectiveness:")
                print(f"   Legacy:     {cache.get('legacy_cache_hit_rate', 0):.1%}")
                print(f"   New:        {cache.get('new_cache_hit_rate', 0):.1%}")
                improvement = cache.get("cache_improvement", 0)
                if improvement > 0:
                    print(f"   ✅ Improvement: +{improvement:.1%} hit rate")
                else:
                    print(f"   ❌ Regression: {improvement:.1%} hit rate")

            throughput = comp.get("throughput_comparison", {})
            if throughput:
                print(f"\n🚀 Throughput:")
                print(f"   Legacy:     {throughput.get('legacy_rps', 0):.1f} req/s")
                print(f"   New:        {throughput.get('new_rps', 0):.1f} req/s")
                improvement = throughput.get("throughput_improvement_percent", 0)
                if improvement > 0:
                    print(f"   ✅ Improvement: {improvement:.1f}% faster")
                else:
                    print(f"   ❌ Regression: {abs(improvement):.1f}% slower")

        print("\n📈 DETAILED STATISTICS:")
        print("-" * 50)

        for category, endpoints in [
            ("Legacy Results", self.results.get("legacy_results", {})),
            ("New Architecture Results", self.results.get("new_architecture_results", {})),
        ]:
            if endpoints:
                print(f"\n{category}:")
                for endpoint_name, data in endpoints.items():
                    if data.get("response_time"):
                        rt = data["response_time"]
                        print(f"  {data.get('name', endpoint_name)}:")
                        print(f"    Success Rate: {data.get('success_rate', 0):.1%}")
                        print(f"    Mean: {rt['mean_ms']:.2f}ms | P95: {rt['p95_ms']:.2f}ms | P99: {rt['p99_ms']:.2f}ms")
                        print(f"    Cache Hit Rate: {data.get('cache_hit_rate', 0):.1%}")
                        print(f"    Throughput: {data.get('throughput_rps', 0):.1f} req/s")

    def save_results(self, filename: Optional[str] = None) -> str:
        """Save benchmark results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_benchmark_{timestamp}.json"

        filepath = os.path.join(os.path.dirname(__file__), filename)

        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Results saved to: {filepath}")
        return filepath


def main():
    """Main benchmark execution."""
    import argparse

    parser = argparse.ArgumentParser(description="GLPI Dashboard Performance Benchmark")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL for API")
    parser.add_argument("--iterations", type=int, default=10, help="Number of iterations per test")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive benchmark")
    parser.add_argument("--output", help="Output filename for results")

    args = parser.parse_args()

    benchmark = PerformanceBenchmark(args.url, args.iterations)

    try:
        if args.comprehensive:
            benchmark.run_comprehensive_benchmark()
        else:
            benchmark.run_metrics_comparison()

        benchmark.print_results()
        benchmark.save_results(args.output)

        print("\n✅ Benchmark completed successfully!")

    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
