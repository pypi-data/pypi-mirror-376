"""
Ops hardening: System monitoring and health check service.

This service provides comprehensive system monitoring capabilities including:
- Service health checks
- Resource monitoring
- Performance metrics
- Alerting on system issues
- Circuit breaker patterns for external services
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from ..commands.logger_config import error, info, warning
from ..utils.errors import NetworkError, TemporaryError


class ServiceStatus(Enum):
    """Service health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class HealthCheck:
    """Individual health check result."""

    service: str
    status: ServiceStatus
    message: str
    response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System resource metrics."""

    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    load_average: tuple[float, float, float]
    network_io: dict[str, int]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Alert:
    """System alert."""

    level: AlertLevel
    service: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """Circuit breaker for service reliability."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = "closed"  # closed, open, half-open

    def can_execute(self) -> bool:
        """Check if service call can be executed."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if (
                self.last_failure_time
                and (datetime.now() - self.last_failure_time).seconds > self.recovery_timeout
            ):
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True

    def record_success(self) -> None:
        """Record successful service call."""
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self) -> None:
        """Record failed service call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            info(f"Circuit breaker opened due to {self.failure_count} failures")


class OpsMonitor:
    """Comprehensive operations monitoring service."""

    def __init__(self):
        self.health_checks: dict[str, HealthCheck] = {}
        self.system_metrics: deque[SystemMetrics] = deque(maxlen=100)
        self.alerts: list[Alert] = []
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.performance_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=50))

        # Monitoring configuration
        self.enabled = os.getenv("OPS_MONITORING_ENABLED", "true").lower() == "true"
        self.alert_thresholds = {
            "cpu_percent": float(os.getenv("ALERT_CPU_THRESHOLD", "80")),
            "memory_percent": float(os.getenv("ALERT_MEMORY_THRESHOLD", "85")),
            "disk_usage_percent": float(os.getenv("ALERT_DISK_THRESHOLD", "90")),
            "response_time": float(os.getenv("ALERT_RESPONSE_TIME_THRESHOLD", "5.0")),
        }

        # Alert directory
        self.alerts_dir = Path("alerts")
        self.alerts_dir.mkdir(exist_ok=True)

    def check_service_health(self, service_name: str, check_func: callable) -> HealthCheck:
        """Perform health check on a service."""
        if not self.enabled:
            return HealthCheck(service_name, ServiceStatus.UNKNOWN, "Monitoring disabled")

        start_time = time.time()

        try:
            # Check circuit breaker
            circuit_breaker = self.circuit_breakers.get(service_name)
            if circuit_breaker and not circuit_breaker.can_execute():
                return HealthCheck(
                    service_name,
                    ServiceStatus.UNHEALTHY,
                    "Circuit breaker open",
                    metadata={"circuit_breaker_state": circuit_breaker.state},
                )

            # Perform the actual health check
            result = check_func()
            response_time = time.time() - start_time

            # Determine status based on response time
            if response_time > self.alert_thresholds["response_time"]:
                status = ServiceStatus.DEGRADED
                message = f"Slow response: {response_time:.2f}s"
            else:
                status = ServiceStatus.HEALTHY
                message = "Service responding normally"

            # Record success in circuit breaker
            if circuit_breaker:
                circuit_breaker.record_success()

            health_check = HealthCheck(
                service_name,
                status,
                message,
                response_time,
                metadata={"result": result},
            )

        except Exception as e:
            response_time = time.time() - start_time

            # Record failure in circuit breaker
            if service_name not in self.circuit_breakers:
                self.circuit_breakers[service_name] = CircuitBreaker()
            self.circuit_breakers[service_name].record_failure()

            # Determine error type for alerting
            if isinstance(e, NetworkError | ConnectionError):
                status = ServiceStatus.UNHEALTHY
                message = f"Network error: {str(e)}"
            elif isinstance(e, TemporaryError):
                status = ServiceStatus.DEGRADED
                message = f"Temporary issue: {str(e)}"
            else:
                status = ServiceStatus.UNHEALTHY
                message = f"Service error: {str(e)}"

            health_check = HealthCheck(
                service_name,
                status,
                message,
                response_time,
                metadata={"error": str(e), "error_type": type(e).__name__},
            )

        # Store health check result
        self.health_checks[service_name] = health_check
        self.performance_history[service_name].append(response_time)

        # Generate alerts if needed
        if health_check.status in [ServiceStatus.DEGRADED, ServiceStatus.UNHEALTHY]:
            self._generate_alert(health_check)

        return health_check

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics."""
        if not self.enabled:
            return SystemMetrics(0, 0, 0, (0, 0, 0), {})

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage (current directory)
            disk = psutil.disk_usage(".")
            disk_usage_percent = (disk.used / disk.total) * 100

            # Load average (Unix-like systems)
            try:
                load_avg = os.getloadavg()
            except (OSError, AttributeError):
                load_avg = (0.0, 0.0, 0.0)  # Windows fallback

            # Network I/O
            network_io = {}
            try:
                net_io = psutil.net_io_counters()
                network_io = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                }
            except Exception:
                network_io = {
                    "bytes_sent": 0,
                    "bytes_recv": 0,
                    "packets_sent": 0,
                    "packets_recv": 0,
                }

            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                load_average=load_avg,
                network_io=network_io,
            )

            # Store metrics
            self.system_metrics.append(metrics)

            # Check for resource alerts
            self._check_resource_alerts(metrics)

            return metrics

        except Exception as e:
            error(f"Failed to collect system metrics: {e}", "ops_monitor")
            return SystemMetrics(0, 0, 0, (0, 0, 0), {})

    def _generate_alert(self, health_check: HealthCheck) -> None:
        """Generate alert based on health check result."""
        # Determine alert level
        if health_check.status == ServiceStatus.UNHEALTHY:
            level = AlertLevel.CRITICAL
        elif health_check.status == ServiceStatus.DEGRADED:
            level = AlertLevel.WARNING
        else:
            return  # No alert needed

        alert = Alert(
            level=level,
            service=health_check.service,
            message=f"{health_check.service}: {health_check.message}",
            metadata={
                "response_time": health_check.response_time,
                "health_check_metadata": health_check.metadata,
            },
        )

        self.alerts.append(alert)
        self._log_alert(alert)
        self._save_alert(alert)

    def _check_resource_alerts(self, metrics: SystemMetrics) -> None:
        """Check system metrics against alert thresholds."""
        alerts_to_generate = []

        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts_to_generate.append(
                Alert(
                    level=AlertLevel.WARNING,
                    service="system_cpu",
                    message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                    metadata={"cpu_percent": metrics.cpu_percent},
                )
            )

        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts_to_generate.append(
                Alert(
                    level=AlertLevel.CRITICAL,
                    service="system_memory",
                    message=f"High memory usage: {metrics.memory_percent:.1f}%",
                    metadata={"memory_percent": metrics.memory_percent},
                )
            )

        if metrics.disk_usage_percent > self.alert_thresholds["disk_usage_percent"]:
            alerts_to_generate.append(
                Alert(
                    level=AlertLevel.CRITICAL,
                    service="system_disk",
                    message=f"High disk usage: {metrics.disk_usage_percent:.1f}%",
                    metadata={"disk_usage_percent": metrics.disk_usage_percent},
                )
            )

        for alert in alerts_to_generate:
            self.alerts.append(alert)
            self._log_alert(alert)
            self._save_alert(alert)

    def _log_alert(self, alert: Alert) -> None:
        """Log alert to system logger."""
        if alert.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
            error(f"[ALERT-{alert.level.value.upper()}] {alert.message}", "ops_monitor")
        elif alert.level == AlertLevel.WARNING:
            warning(f"[ALERT-{alert.level.value.upper()}] {alert.message}", "ops_monitor")
        else:
            info(f"[ALERT-{alert.level.value.upper()}] {alert.message}", "ops_monitor")

    def _save_alert(self, alert: Alert) -> None:
        """Save alert to file for external processing."""
        alert_file = self.alerts_dir / f"alert_{alert.timestamp.strftime('%Y%m%d')}.jsonl"

        alert_data = {
            "timestamp": alert.timestamp.isoformat(),
            "level": alert.level.value,
            "service": alert.service,
            "message": alert.message,
            "metadata": alert.metadata,
            "resolved": alert.resolved,
        }

        try:
            with open(alert_file, "a") as f:
                f.write(json.dumps(alert_data) + "\n")
        except Exception as e:
            error(f"Failed to save alert: {e}", "ops_monitor")

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status report."""
        current_metrics = self.collect_system_metrics() if self.system_metrics else None

        # Calculate service availability
        service_availability = {}
        for service, health_check in self.health_checks.items():
            recent_checks = self.performance_history.get(service, deque())
            if recent_checks:
                avg_response_time = sum(recent_checks) / len(recent_checks)
                service_availability[service] = {
                    "status": health_check.status.value,
                    "last_check": health_check.timestamp.isoformat(),
                    "avg_response_time": avg_response_time,
                    "circuit_breaker_state": getattr(
                        self.circuit_breakers.get(service), "state", "closed"
                    ),
                }

        # Count recent alerts by level
        recent_alerts = [
            a
            for a in self.alerts
            if not a.resolved and (datetime.now() - a.timestamp) < timedelta(hours=24)
        ]
        alert_counts = defaultdict(int)
        for alert in recent_alerts:
            alert_counts[alert.level.value] += 1

        return {
            "timestamp": datetime.now().isoformat(),
            "monitoring_enabled": self.enabled,
            "system_metrics": {
                "cpu_percent": current_metrics.cpu_percent if current_metrics else 0,
                "memory_percent": (current_metrics.memory_percent if current_metrics else 0),
                "disk_usage_percent": (
                    current_metrics.disk_usage_percent if current_metrics else 0
                ),
                "load_average": (current_metrics.load_average if current_metrics else (0, 0, 0)),
            },
            "service_health": service_availability,
            "alert_summary": dict(alert_counts),
            "total_alerts": len(recent_alerts),
            "circuit_breaker_summary": {
                service: breaker.state for service, breaker in self.circuit_breakers.items()
            },
        }

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        # In a real implementation, you'd have alert IDs
        # For now, resolve alerts by service name
        resolved_count = 0
        for alert in self.alerts:
            if alert.service == alert_id and not alert.resolved:
                alert.resolved = True
                resolved_count += 1
                info(
                    f"Resolved alert for {alert.service}: {alert.message}",
                    "ops_monitor",
                )

        return resolved_count > 0


# Global ops monitor instance
ops_monitor = OpsMonitor()


def check_service_health(service_name: str, check_func: callable) -> HealthCheck:
    """Convenience function to check service health."""
    return ops_monitor.check_service_health(service_name, check_func)


def get_system_status() -> dict[str, Any]:
    """Convenience function to get system status."""
    return ops_monitor.get_system_status()


def collect_metrics() -> SystemMetrics:
    """Convenience function to collect system metrics."""
    return ops_monitor.collect_system_metrics()
