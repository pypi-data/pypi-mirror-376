"""Operations hardening command for system monitoring and resilience."""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

from ..services.ops_monitor import collect_metrics, get_system_status
from ..services.resilience_manager import backup_manager, system_recovery
from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "ops_hardening"
USAGE = f"{COMMAND} [--monitor|--backup|--health|--repair|--alerts|--help]"


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    """
    Operations hardening tools for system monitoring and resilience.

    Commands:
      ops_hardening --monitor         Show real-time system monitoring
      ops_hardening --backup          Create system backup
      ops_hardening --health          Check comprehensive system health
      ops_hardening --repair          Attempt automatic system repairs
      ops_hardening --alerts          Show recent system alerts
      ops_hardening --status          Show overall ops status

    Examples:
      ops_hardening --monitor
      ops_hardening --backup manual
      ops_hardening --health
      ops_hardening --repair
    """

    if argv is None:
        argv = []

    if wants_help(argv):
        print_help(
            "ops_hardening",
            "Operations hardening command for system monitoring and resilience.",
            USAGE,
        )
        return 0

    if has_unknown_flags(
        argv, {"--monitor", "--backup", "--health", "--repair", "--alerts", "--status"}
    ):
        print("❌ Unknown flag found")
        print(f"Usage: {USAGE}")
        return 0

    if not argv:
        print_help(
            "ops_hardening",
            "Operations hardening command for system monitoring and resilience.",
            USAGE,
        )
        return 0

    try:
        if "--monitor" in argv:
            return _show_monitoring_dashboard()
        elif "--backup" in argv:
            backup_type = "manual"
            if len(argv) > argv.index("--backup") + 1:
                backup_type = argv[argv.index("--backup") + 1]
            return _create_backup(backup_type)
        elif "--health" in argv:
            return _check_system_health()
        elif "--repair" in argv:
            return _auto_repair_system()
        elif "--alerts" in argv:
            return _show_system_alerts()
            import logging

            logger = logging.getLogger(__name__)
        elif "--status" in argv:
            return _show_ops_status()
        else:
            print_help(
                "ops_hardening",
                "Operations hardening command for system monitoring and resilience.",
                USAGE,
            )
            return 0

    except Exception as e:
        print(f"❌ Ops hardening error: {e}")
        return 1


def _show_monitoring_dashboard() -> int:
    """Show real-time system monitoring dashboard."""
    print("\n🔍 SYSTEM MONITORING DASHBOARD")
    print("=" * 60)

    try:
        # Collect current metrics
        print("📊 Collecting system metrics...")
        metrics = collect_metrics()

        print(f"\n⚡ SYSTEM RESOURCES (as of {metrics.timestamp.strftime('%H:%M:%S')})")
        print("-" * 40)
        print(f"CPU Usage:    {metrics.cpu_percent:6.1f}%")
        print(f"Disk Usage:   {metrics.disk_usage_percent:6.1f}%")
        print(
            f"Load Average: {metrics.load_average[0]:.2f}, {metrics.load_average[1]:.2f}, {metrics.load_average[2]:.2f}"
        )

        # Network I/O
        net_io = metrics.network_io
        print("\n🌐 NETWORK I/O")
        print(f"Bytes Sent:     {net_io.get('bytes_sent', 0):,}")
        print(f"Bytes Received: {net_io.get('bytes_recv', 0):,}")

        # Service health checks
        status = get_system_status()
        print("\n🏥 SERVICE HEALTH")
        print("-" * 40)
        service_health = status.get("service_health", {})
        if service_health:
            for service, health in service_health.items():
                status_emoji = (
                    "✅"
                    if health["status"] == "healthy"
                    else "⚠️" if health["status"] == "degraded" else "❌"
                )
                print(
                    f"{status_emoji} {service:15} {health['status']:10} ({health.get('avg_response_time', 0):.2f}s avg)"
                )
        else:
            print("No service health checks available")

        # Alert summary
        alert_summary = status.get("alert_summary", {})
        if any(alert_summary.values()):
            print("\n🚨 ALERTS (24h)")
            print("-" * 40)
            for level, count in alert_summary.items():
                if count > 0:
                    emoji = (
                        "🔴"
                        if level == "critical"
                        else "🟡" if level == "warning" else "🔵"
                    )
                    print(f"{emoji} {level.upper():10} {count:3} alerts")

        print(
            f"\n✅ Monitoring dashboard updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return 0

    except Exception as e:
        print(f"❌ Failed to show monitoring dashboard: {e}")
        return 1


def _create_backup(backup_type: str = "manual") -> int:
    """Create a system backup."""
    print(f"\n💾 CREATING {backup_type.upper()} BACKUP")
    print("=" * 50)

    try:
        print("📦 Starting backup process...")
        result = backup_manager.create_backup(backup_type)

        if result["success"]:
            print("✅ Backup created successfully!")
            print(f"📅 Timestamp: {result['timestamp']}")
            print(f"📁 Files backed up: {len(result['files_backed_up'])}")
            print(f"📊 Total size: {result['total_size_bytes']:,} bytes")

            if result["files_skipped"]:
                print(f"⚠️  Files skipped: {len(result['files_skipped'])}")
                for skipped in result["files_skipped"]:
                    print(f"   - {skipped}")

            # Show backup list
            backups = backup_manager.list_backups()
            print(f"\n📋 BACKUP HISTORY ({len(backups)} total)")
            print("-" * 50)
            for backup in backups[-5:]:  # Show last 5
                created = datetime.fromisoformat(backup["created"]).strftime(
                    "%m/%d %H:%M"
                )
                size_mb = backup["size_bytes"] / (1024 * 1024)
                print(f"📦 {backup['name']:25} {created} ({size_mb:.1f}MB)")

        else:
            print(f"❌ Backup failed: {result.get('error', 'Unknown error')}")
            return 1

        return 0

    except Exception as e:
        print(f"❌ Backup creation failed: {e}")
        return 1


def _check_system_health() -> int:
    """Check comprehensive system health."""
    print("\n🏥 SYSTEM HEALTH CHECK")
    print("=" * 50)

    try:
        print("🔍 Running comprehensive health checks...")
        health = system_recovery.check_system_health()

        # Overall status
        status_emoji = (
            "✅"
            if health["overall_status"] == "healthy"
            else "⚠️" if health["overall_status"] == "degraded" else "❌"
        )
        print(f"\n{status_emoji} OVERALL STATUS: {health['overall_status'].upper()}")

        # Detailed checks
        print("\n📋 DETAILED CHECKS")
        print("-" * 30)

        checks = health.get("checks", {})

        # Critical files check
        critical_files = checks.get("critical_files", {})
        if critical_files["healthy"]:
            print("✅ Critical files: All present and valid")
        else:
            print("❌ Critical files: Issues detected")
            if critical_files.get("missing_files"):
                print(f"   Missing: {', '.join(critical_files['missing_files'])}")
            if critical_files.get("corrupted_files"):
                print(f"   Corrupted: {', '.join(critical_files['corrupted_files'])}")

        # Disk space check
        disk_space = checks.get("disk_space", {})
        if disk_space["healthy"]:
            print(f"✅ Disk space: {disk_space.get('used_percent', 0):.1f}% used")
        else:
            print(
                f"❌ Disk space: {disk_space.get('used_percent', 0):.1f}% used (critical)"
            )

        # Recent errors check
        recent_errors = checks.get("recent_errors", {})
        if recent_errors["healthy"]:
            print(
                f"✅ Recent errors: {recent_errors.get('error_count', 0)} in 24h (acceptable)"
            )
        else:
            print(
                f"❌ Recent errors: {recent_errors.get('error_count', 0)} in 24h (high)"
            )

        # Backup health check
        backup_health = checks.get("backup_health", {})
        if backup_health["healthy"]:
            age_hours = backup_health.get("latest_backup_age_hours", 0)
            print(f"✅ Backup health: Latest backup {age_hours:.1f}h ago")
        else:
            print("❌ Backup health: No recent backups found")

        # Recommendations
        recommendations = health.get("recommendations", [])
        if recommendations:
            print("\n💡 RECOMMENDATIONS")
            print("-" * 20)
            for rec in recommendations:
                print(f"• {rec}")

        return 0 if health["overall_status"] == "healthy" else 1

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return 1


def _auto_repair_system() -> int:
    """Attempt automatic system repairs."""
    print("\n🔧 AUTOMATIC SYSTEM REPAIR")
    print("=" * 50)

    try:
        print("🛠️  Starting auto-repair process...")
        result = system_recovery.auto_repair()

        if result["success"]:
            actions_taken = result.get("actions_taken", [])
            actions_failed = result.get("actions_failed", [])

            if actions_taken:
                print(f"✅ REPAIRS COMPLETED ({len(actions_taken)})")
                for action in actions_taken:
                    print(f"   ✓ {action}")

            if actions_failed:
                print(f"\n❌ REPAIRS FAILED ({len(actions_failed)})")
                for action in actions_failed:
                    print(f"   ✗ {action}")

            if not actions_taken and not actions_failed:
                print("ℹ️  No repairs needed - system is healthy")

        else:
            print(f"❌ Auto-repair failed: {result.get('error', 'Unknown error')}")
            return 1

        return 0

    except Exception as e:
        print(f"❌ Auto-repair failed: {e}")
        return 1


def _show_system_alerts() -> int:
    """Show recent system alerts."""
    print("\n🚨 SYSTEM ALERTS")
    print("=" * 40)

    try:
        # Check if alerts directory exists
        alerts_dir = Path("alerts")
        if not alerts_dir.exists():
            print("ℹ️  No alerts directory found - no alerts to display")
            return 0

        # Load recent alerts from files
        alerts = []
        for alert_file in sorted(alerts_dir.glob("alert_*.jsonl")):
            try:
                with open(alert_file) as f:
                    for line in f:
                        alert_data = json.loads(line.strip())
                        alerts.append(alert_data)
            except Exception as e:
                logger.debug("Skipping corrupted alert file: %s", e)
                continue

        if not alerts:
            print("✅ No recent alerts found")
            return 0

        # Sort by timestamp and show recent ones
        alerts.sort(key=lambda a: a["timestamp"], reverse=True)
        recent_alerts = alerts[:20]  # Show last 20

        # Group by level
        by_level = {}
        for alert in recent_alerts:
            level = alert["level"]
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(alert)

        # Display alerts by level
        level_order = ["critical", "warning", "info"]
        level_emojis = {"critical": "🔴", "warning": "🟡", "info": "🔵"}

        for level in level_order:
            if level in by_level:
                alerts_for_level = by_level[level]
                emoji = level_emojis.get(level, "⚪")
                print(f"\n{emoji} {level.upper()} ALERTS ({len(alerts_for_level)})")
                print("-" * 30)

                for alert in alerts_for_level[:5]:  # Show top 5 per level
                    timestamp = datetime.fromisoformat(alert["timestamp"]).strftime(
                        "%m/%d %H:%M"
                    )
                    service = alert["service"]
                    message = alert["message"]
                    resolved = "✓" if alert.get("resolved", False) else " "
                    print(f"  {resolved} {timestamp} [{service:12}] {message}")

        print(f"\n📊 Total alerts shown: {len(recent_alerts)} (last 24h)")
        return 0

    except Exception as e:
        print(f"❌ Failed to show alerts: {e}")
        return 1


def _show_ops_status() -> int:
    """Show overall ops status summary."""
    print("\n🎯 OPS STATUS SUMMARY")
    print("=" * 50)

    try:
        # Get comprehensive status
        status = get_system_status()

        print(
            f"📅 Status as of: {datetime.fromisoformat(status['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(
            f"🔧 Monitoring: {'✅ Enabled' if status['monitoring_enabled'] else '❌ Disabled'}"
        )

        # System metrics summary
        metrics = status.get("system_metrics", {})
        print("\n📊 SYSTEM RESOURCES")
        print(f"   CPU:    {metrics.get('cpu_percent', 0):.1f}%")
        print(f"   Memory: {metrics.get('memory_percent', 0):.1f}%")
        print(f"   Disk:   {metrics.get('disk_usage_percent', 0):.1f}%")

        # Service health summary
        service_health = status.get("service_health", {})
        if service_health:
            healthy_count = sum(
                1 for s in service_health.values() if s["status"] == "healthy"
            )
            total_count = len(service_health)
            print(f"\n🏥 SERVICE HEALTH: {healthy_count}/{total_count} healthy")
        else:
            print("\n🏥 SERVICE HEALTH: No services monitored")

        # Alert summary
        alert_summary = status.get("alert_summary", {})
        total_alerts = status.get("total_alerts", 0)
        if total_alerts > 0:
            print(f"\n🚨 ALERTS (24h): {total_alerts} total")
            for level, count in alert_summary.items():
                if count > 0:
                    print(f"   {level}: {count}")
        else:
            print("\n🚨 ALERTS: ✅ No recent alerts")

        # Circuit breaker summary
        circuit_breakers = status.get("circuit_breaker_summary", {})
        if circuit_breakers:
            open_breakers = [
                service
                for service, state in circuit_breakers.items()
                if state == "open"
            ]
            if open_breakers:
                print(f"\n⚡ CIRCUIT BREAKERS: ⚠️  {len(open_breakers)} open")
                for service in open_breakers:
                    print(f"   {service}: OPEN")
            else:
                print("\n⚡ CIRCUIT BREAKERS: ✅ All closed")

        # Quick health recommendation
        print("\n💡 OVERALL STATUS")
        if total_alerts == 0 and (
            not circuit_breakers
            or not any(state == "open" for state in circuit_breakers.values())
        ):
            print("✅ System is operating normally")
        elif total_alerts < 5:
            print("⚠️  System has minor issues - monitor closely")
        else:
            print("❌ System requires attention - investigate alerts")

        return 0

    except Exception as e:
        print(f"❌ Failed to show ops status: {e}")
        return 1
