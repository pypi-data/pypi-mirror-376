from __future__ import annotations

import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from ._cli import has_unknown_flags, print_help, wants_help

_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def configure(level_str: str | None = None, ctx: dict[str, Any] | None = None) -> int:
    key = "INFO" if level_str is None else str(level_str).upper()
    if key not in _LEVELS:
        raise ValueError(f"Invalid log level: {level_str}")
    level = _LEVELS[key]

    logging.basicConfig(level=level, force=True)
    logging.getLogger().setLevel(level)

    if isinstance(ctx, dict):
        ctx["log_level"] = key
    return level


# --- Typing helpers ---
JSONDict = dict[str, Any]


def as_dict(v: Any) -> JSONDict:
    if isinstance(v, dict):
        # Coerce keys to str for mypy compatibility
        return {str(k): v[k] for k in v}
    return {}


# Configuration from environment with defaults
env = os.getenv
LOG_FILE = env("COTERIE_LOG_FILE", "coterie.log")
LOG_LEVEL = env("COTERIE_LOG_LEVEL", "INFO").upper()
MAX_LOG_BYTES = int(env("COTERIE_LOG_MAX_BYTES", 5_000_000))  # 5MB
BACKUP_COUNT = int(env("COTERIE_LOG_BACKUP_COUNT", 10))
LOG_FORMAT = env("COTERIE_LOG_FORMAT", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Ensure log directory exists
log_path = Path(LOG_FILE)
log_path.parent.mkdir(parents=True, exist_ok=True)

# Set up rotating logger with enterprise configuration
logger = logging.getLogger("coterie")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Only add handler if not already present (prevents duplicate logs)
if not logger.handlers:
    # Rotating file handler for persistent logs
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_LOG_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )

    # Console handler for development
    console_handler = logging.StreamHandler()

    # Formatter with timestamp and context
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)

    # Only add console handler in development mode
    if env("COTERIE_DEV_MODE", "false").lower() == "true":
        logger.addHandler(console_handler)

# Performance metrics tracking
_metrics: JSONDict = {
    "start_time": time.time(),
    "log_counts": {"debug": 0, "info": 0, "warning": 0, "error": 0, "critical": 0},
    "subsystem_activity": {},
    "cache_stats": {"hits": 0, "misses": 0, "saves": 0},
    "api_calls": {"weather": 0, "geocoding": 0, "sms": 0, "email": 0},
}


def _update_metrics(level: str, subsystem: str | None = None) -> None:
    """Update internal metrics tracking"""
    log_counts = as_dict(_metrics.get("log_counts"))
    log_counts[level.lower()] = log_counts.get(level.lower(), 0) + 1
    _metrics["log_counts"] = log_counts

    if subsystem:
        subsys = as_dict(_metrics.get("subsystem_activity"))
        subsys[subsystem] = subsys.get(subsystem, 0) + 1
        _metrics["subsystem_activity"] = subsys


# Core logging functions with metrics
def debug(msg: str, subsystem: str | None = None) -> None:
    """Log debug message"""
    logger.debug(msg)
    _update_metrics("debug", subsystem)


def info(msg: str, subsystem: str | None = None) -> None:
    """Log info message"""
    logger.info(msg)
    _update_metrics("info", subsystem)


def warning(msg: str, subsystem: str | None = None) -> None:
    """Log warning message"""
    logger.warning(msg)
    _update_metrics("warning", subsystem)


def error(msg: str, subsystem: str | None = None) -> None:
    """Log error message"""
    logger.error(msg)
    _update_metrics("error", subsystem)


def critical(msg: str, subsystem: str | None = None) -> None:
    """Log critical message"""
    logger.critical(msg)
    _update_metrics("critical", subsystem)


def exception(msg: str, subsystem: str | None = None) -> None:
    """Log exception with traceback"""
    logger.exception(msg)
    _update_metrics("error", subsystem)


# Enterprise subsystem logging
def log_weather(msg: str, level: str = "info") -> None:
    """Log weather subsystem activity"""
    formatted_msg = f"[WEATHER] {msg}"
    getattr(logger, level.lower())(formatted_msg)
    _update_metrics(level, "weather")


def log_cluster(msg: str, level: str = "info") -> None:
    """Log clustering subsystem activity"""
    formatted_msg = f"[CLUSTER] {msg}"
    getattr(logger, level.lower())(formatted_msg)
    _update_metrics(level, "cluster")


def log_inventory(msg: str, level: str = "info") -> None:
    """Log inventory subsystem activity"""
    formatted_msg = f"[INVENTORY] {msg}"
    getattr(logger, level.lower())(formatted_msg)
    _update_metrics(level, "inventory")


def log_receipt(msg: str, level: str = "info") -> None:
    """Log receipt/MSDS subsystem activity"""
    formatted_msg = f"[RECEIPT] {msg}"
    getattr(logger, level.lower())(formatted_msg)
    _update_metrics(level, "receipt")


def log_crew(msg: str, level: str = "info") -> None:
    """Log crew management activity"""
    formatted_msg = f"[CREW] {msg}"
    getattr(logger, level.lower())(formatted_msg)
    _update_metrics(level, "crew")


def log_booking(msg: str, level: str = "info") -> None:
    """Log booking system activity"""
    formatted_msg = f"[BOOKING] {msg}"
    getattr(logger, level.lower())(formatted_msg)
    _update_metrics(level, "booking")


def log_dashboard(msg: str, level: str = "info") -> None:
    """Log dashboard activity"""
    formatted_msg = f"[DASHBOARD] {msg}"
    getattr(logger, level.lower())(formatted_msg)
    _update_metrics(level, "dashboard")


def log_security(msg: str, level: str = "warning") -> None:
    """Log security events"""
    formatted_msg = f"[SECURITY] {msg}"
    getattr(logger, level.lower())(formatted_msg)
    _update_metrics(level, "security")


def log_notification(msg: str, level: str = "info") -> None:
    """Log notification system activity"""
    formatted_msg = f"[NOTIFY] {msg}"
    getattr(logger, level.lower())(formatted_msg)
    _update_metrics(level, "notification")


def log_optimization(msg: str, level: str = "info") -> None:
    """Log schedule optimization activity"""
    formatted_msg = f"[OPTIMIZE] {msg}"
    getattr(logger, level.lower())(formatted_msg)
    _update_metrics(level, "optimization")


# Cache and API activity logging
def log_cache_hit(system: str, key: str) -> None:
    """Log cache hit"""
    debug(f"[CACHE] HIT {system}: {key[:50]}...")
    _metrics["cache_stats"]["hits"] += 1


def log_cache_miss(system: str, key: str) -> None:
    """Log cache miss"""
    debug(f"[CACHE] MISS {system}: {key[:50]}...")
    _metrics["cache_stats"]["misses"] += 1


def log_cache_save(system: str, entries: int) -> None:
    """Log cache save operation"""
    debug(f"[CACHE] SAVE {system}: {entries} entries")
    _metrics["cache_stats"]["saves"] += 1


def log_api_call(service: str, endpoint: str, status: str = "success") -> None:
    """Log API call activity"""
    info(f"[API] {service.upper()} call to {endpoint}: {status}")
    _metrics["api_calls"][service.lower()] = _metrics["api_calls"].get(service.lower(), 0) + 1


def log_business_event(event: str, details: JSONDict) -> None:
    """Log business events with structured data"""
    details_str = json.dumps(details, default=str)
    info(f"[BUSINESS] {event}: {details_str}")


def log_performance(operation: str, duration: float, details: JSONDict | None = None) -> None:
    """Log performance metrics"""
    details_str = json.dumps(details, default=str) if details else ""
    info(f"[PERF] {operation} completed in {duration:.3f}s {details_str}")


# System health and metrics
def get_log_stats() -> JSONDict:
    """Get comprehensive logging statistics"""
    uptime = time.time() - _metrics["start_time"]

    return {
        "uptime_seconds": uptime,
        "uptime_formatted": f"{uptime / 3600:.1f} hours",
        "log_counts": as_dict(_metrics.get("log_counts")).copy(),
        "subsystem_activity": as_dict(_metrics.get("subsystem_activity")).copy(),
        "cache_stats": as_dict(_metrics.get("cache_stats")).copy(),
        "api_calls": as_dict(_metrics.get("api_calls")).copy(),
        "log_file": LOG_FILE,
        "log_level": LOG_LEVEL,
        "handlers": len(logger.handlers),
        "log_file_size": os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0,
    }


def log_system_health() -> None:
    """Log system health metrics"""
    stats = get_log_stats()

    total_logs = sum(stats["log_counts"].values())
    cache_hit_rate = (
        stats["cache_stats"]["hits"]
        / max(1, stats["cache_stats"]["hits"] + stats["cache_stats"]["misses"])
    ) * 100

    health_msg = (
        f"System Health: {stats['uptime_formatted']} uptime, "
        f"{total_logs} log entries, "
        f"{cache_hit_rate:.1f}% cache hit rate"
    )

    info(f"[HEALTH] {health_msg}")


# Command interface for log management


COMMAND = "logger_config"
DESCRIPTION = "Enterprise logging management system."
USAGE = f"{COMMAND} [--stats|--health|--level <LEVEL>|--clear|--tail <N>|--help]"


def run(argv: list[str] | None = None) -> int:
    argv = argv or []
    known_flags = {
        "--help",
        "-h",
        "--stats",
        "--health",
        "--level",
        "--clear",
        "--tail",
    }
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if not argv:
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    # CLI options handling
    if "--stats" in argv:
        stats = get_log_stats()
        print(json.dumps(stats, indent=2, default=str))
        return 0

    if "--health" in argv:
        log_system_health()
        print("[✅] System health logged")
        return 0

    if "--level" in argv:
        try:
            level_idx = argv.index("--level")
            if level_idx + 1 < len(argv):
                new_level = argv[level_idx + 1].upper()
                if new_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                    logger.setLevel(getattr(logging, new_level))
                    info(f"Log level changed to {new_level}")
                    print(f"[✅] Log level set to {new_level}")
                else:
                    print("[❌] Invalid log level. Use: DEBUG, INFO, WARNING, ERROR, CRITICAL")
            else:
                print("[❌] Log level argument required")
        except ValueError:
            print("[❌] Invalid --level argument")
        return 0

    if "--clear" in argv:
        global _metrics
        _metrics = {
            "start_time": time.time(),
            "log_counts": {
                "debug": 0,
                "info": 0,
                "warning": 0,
                "error": 0,
                "critical": 0,
            },
            "subsystem_activity": {},
            "cache_stats": {"hits": 0, "misses": 0, "saves": 0},
            "api_calls": {"weather": 0, "geocoding": 0, "sms": 0, "email": 0},
        }
        print("[✅] Log metrics cleared")
        return 0

    if "--tail" in argv:
        try:
            tail_idx = argv.index("--tail")
            if tail_idx + 1 < len(argv):
                n = int(argv[tail_idx + 1])
                with open(LOG_FILE) as f:
                    lines = f.readlines()
                for line in lines[-n:]:
                    print(line.rstrip())
            else:
                print("[❌] Tail argument required")
        except Exception:
            print("[❌] Error reading log tail")
        return 0

    print("[stub] logger_config command executed.")
    return 0


# Initialize logging on import
info("Coterie Enterprise Logging System initialized")
log_system_health()

if __name__ == "__main__":
    # Test the logging system
    run(["--stats"])
