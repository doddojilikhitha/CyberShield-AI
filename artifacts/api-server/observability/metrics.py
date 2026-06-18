import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Simple in-memory metrics store as a fallback/real-time cache
_metrics_cache: Dict[str, Any] = {
    "total_runs": 0,
    "error_count": 0,
    "agent_runtimes_ms": {},
    "total_tokens_used": 0,
    "start_time": time.time(),
}


class SystemMetricsManager:
    @staticmethod
    def record_agent_run(
        agent_name: str, duration_ms: int, success: bool = True, tokens_used: int = 0
    ):
        """Record telemetry data for an agent run."""
        _metrics_cache["total_runs"] += 1
        if not success:
            _metrics_cache["error_count"] += 1

        _metrics_cache["total_tokens_used"] += tokens_used

        runtimes = _metrics_cache["agent_runtimes_ms"]
        if agent_name not in runtimes:
            runtimes[agent_name] = []
        runtimes[agent_name].append(duration_ms)

        logger.info(
            f"Telemetry: Agent '{agent_name}' finished in {duration_ms}ms (Success: {success}, Tokens: {tokens_used})"
        )

    @staticmethod
    def get_telemetry_report() -> Dict[str, Any]:
        """Compile a structural report of system metrics."""
        uptime = int(time.time() - _metrics_cache["start_time"])

        avg_runtimes = {}
        for agent, times in _metrics_cache["agent_runtimes_ms"].items():
            avg_runtimes[agent] = round(sum(times) / len(times), 2) if times else 0.0

        return {
            "uptime_seconds": uptime,
            "total_runs": _metrics_cache["total_runs"],
            "error_count": _metrics_cache["error_count"],
            "total_tokens_used": _metrics_cache["total_tokens_used"],
            "average_agent_runtimes_ms": avg_runtimes,
            "error_rate": (
                round(_metrics_cache["error_count"] / _metrics_cache["total_runs"], 4)
                if _metrics_cache["total_runs"] > 0
                else 0.0
            ),
        }
