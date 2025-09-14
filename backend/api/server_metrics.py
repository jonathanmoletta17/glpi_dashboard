"""
Server-side metrics endpoints for performance monitoring
Provides real server metrics instead of client-side measurements
"""

import psutil
import time
import os
from datetime import datetime
from typing import Dict, Any
from flask import Blueprint, jsonify

metrics_bp = Blueprint("metrics", __name__, url_prefix="/api/metrics")

# Global metrics collection
_server_metrics = {
    "start_time": time.time(),
    "request_count": 0,
    "total_response_time": 0.0,
    "peak_memory_mb": 0.0,
    "peak_cpu_percent": 0.0,
}


def update_server_metrics(response_time: float):
    """Update server-side metrics."""
    global _server_metrics

    _server_metrics["request_count"] += 1
    _server_metrics["total_response_time"] += response_time

    # Update peak metrics
    try:
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()

        _server_metrics["peak_memory_mb"] = max(_server_metrics["peak_memory_mb"], memory_mb)
        _server_metrics["peak_cpu_percent"] = max(_server_metrics["peak_cpu_percent"], cpu_percent)
    except:
        pass


@metrics_bp.route("/server/stats")
def get_server_stats():
    """Get comprehensive server-side performance statistics."""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        # Calculate uptime
        uptime_seconds = time.time() - _server_metrics["start_time"]

        # Calculate average response time
        avg_response_time = (
            _server_metrics["total_response_time"] / _server_metrics["request_count"]
            if _server_metrics["request_count"] > 0
            else 0
        )

        stats = {
            "server_info": {
                "pid": os.getpid(),
                "uptime_seconds": uptime_seconds,
                "uptime_formatted": f"{uptime_seconds/3600:.1f}h",
            },
            "memory": {
                "current_rss_mb": memory_info.rss / 1024 / 1024,
                "current_vms_mb": memory_info.vms / 1024 / 1024,
                "peak_memory_mb": _server_metrics["peak_memory_mb"],
                "memory_percent": process.memory_percent(),
            },
            "cpu": {
                "current_percent": process.cpu_percent(),
                "peak_cpu_percent": _server_metrics["peak_cpu_percent"],
                "num_threads": process.num_threads(),
            },
            "requests": {
                "total_count": _server_metrics["request_count"],
                "avg_response_time_ms": avg_response_time * 1000,
                "total_response_time_seconds": _server_metrics["total_response_time"],
                "requests_per_second": _server_metrics["request_count"] / uptime_seconds if uptime_seconds > 0 else 0,
            },
            "system": {
                "cpu_count": psutil.cpu_count(),
                "available_memory_mb": psutil.virtual_memory().available / 1024 / 1024,
                "total_memory_mb": psutil.virtual_memory().total / 1024 / 1024,
                "memory_usage_percent": psutil.virtual_memory().percent,
            },
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify(stats)

    except Exception as e:
        return (
            jsonify(
                {
                    "error": f"Failed to get server stats: {str(e)}",
                    "basic_stats": {
                        "request_count": _server_metrics["request_count"],
                        "uptime_seconds": time.time() - _server_metrics["start_time"],
                    },
                }
            ),
            500,
        )


@metrics_bp.route("/server/reset")
def reset_server_metrics():
    """Reset server metrics counters."""
    global _server_metrics

    _server_metrics = {
        "start_time": time.time(),
        "request_count": 0,
        "total_response_time": 0.0,
        "peak_memory_mb": 0.0,
        "peak_cpu_percent": 0.0,
    }

    return jsonify({"message": "Server metrics reset successfully", "reset_time": datetime.now().isoformat()})


# Middleware to track metrics
def track_request_metrics(app):
    """Add request tracking middleware to Flask app."""

    @app.before_request
    def before_request():
        from flask import g

        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        from flask import g

        if hasattr(g, "start_time"):
            response_time = time.time() - g.start_time
            update_server_metrics(response_time)

        return response

    return app
