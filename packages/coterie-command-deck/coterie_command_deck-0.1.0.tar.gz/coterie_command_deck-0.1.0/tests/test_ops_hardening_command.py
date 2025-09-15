"""Test ops hardening command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.coterie_agents.commands.ops_hardening import run


class TestOpsHardeningCommand:
    """Test ops hardening command functionality."""

    def test_help_flag(self):
        """Test help flag shows help and exits successfully."""
        result = run(["--help"])
        assert result == 0

    def test_empty_args_shows_help(self):
        """Test that empty args shows help."""
        result = run([])
        assert result == 0

    def test_unknown_flag_handling(self):
        """Test handling of unknown flags."""
        result = run(["--unknown-flag"])
        assert result == 0

    @patch("src.coterie_agents.commands.ops_hardening.collect_metrics")
    @patch("src.coterie_agents.commands.ops_hardening.get_system_status")
    def test_monitor_dashboard(self, mock_get_status, mock_collect_metrics):
        """Test monitoring dashboard display."""
        # Mock metrics
        mock_metrics = MagicMock()
        mock_metrics.timestamp.strftime.return_value = "12:34:56"
        mock_metrics.cpu_percent = 25.0
        mock_metrics.memory_percent = 45.0
        mock_metrics.disk_usage_percent = 60.0
        mock_metrics.load_average = (1.0, 1.5, 2.0)
        mock_metrics.network_io = {"bytes_sent": 1000, "bytes_recv": 2000}

        mock_collect_metrics.return_value = mock_metrics

        # Mock status
        mock_status = {
            "service_health": {"test_service": {"status": "healthy", "avg_response_time": 0.5}},
            "alert_summary": {"warning": 2},
        }
        mock_get_status.return_value = mock_status

        result = run(["--monitor"])
        assert result == 0

    @patch("src.coterie_agents.commands.ops_hardening.backup_manager")
    def test_create_backup(self, mock_backup_manager):
        """Test backup creation."""
        # Mock successful backup
        mock_backup_result = {
            "success": True,
            "timestamp": "2025-01-13T12:00:00",
            "files_backed_up": ["file1.json", "file2.json"],
            "files_skipped": [],
            "total_size_bytes": 1024,
        }
        mock_backup_manager.create_backup.return_value = mock_backup_result
        mock_backup_manager.list_backups.return_value = [
            {
                "name": "manual_20250113_120000",
                "created": "2025-01-13T12:00:00",
                "size_bytes": 1024,
            }
        ]

        result = run(["--backup"])
        assert result == 0
        mock_backup_manager.create_backup.assert_called_once_with("manual")

    @patch("src.coterie_agents.commands.ops_hardening.backup_manager")
    def test_create_backup_with_type(self, mock_backup_manager):
        """Test backup creation with specific type."""
        mock_backup_result = {
            "success": True,
            "timestamp": "2025-01-13T12:00:00",
            "files_backed_up": ["file1.json"],
            "files_skipped": [],
            "total_size_bytes": 512,
        }
        mock_backup_manager.create_backup.return_value = mock_backup_result
        mock_backup_manager.list_backups.return_value = []

        result = run(["--backup", "emergency"])
        assert result == 0
        mock_backup_manager.create_backup.assert_called_once_with("emergency")

    @patch("src.coterie_agents.commands.ops_hardening.system_recovery")
    def test_health_check_healthy(self, mock_system_recovery):
        """Test health check when system is healthy."""
        mock_health = {
            "overall_status": "healthy",
            "checks": {
                "critical_files": {"healthy": True},
                "disk_space": {"healthy": True, "used_percent": 50.0},
                "recent_errors": {"healthy": True, "error_count": 2},
                "backup_health": {"healthy": True, "latest_backup_age_hours": 12.0},
            },
            "recommendations": [],
        }
        mock_system_recovery.check_system_health.return_value = mock_health

        result = run(["--health"])
        assert result == 0

    @patch("src.coterie_agents.commands.ops_hardening.system_recovery")
    def test_health_check_unhealthy(self, mock_system_recovery):
        """Test health check when system is unhealthy."""
        mock_health = {
            "overall_status": "unhealthy",
            "checks": {
                "critical_files": {
                    "healthy": False,
                    "missing_files": ["important.json"],
                    "corrupted_files": ["damaged.json"],
                },
                "disk_space": {"healthy": False, "used_percent": 95.0},
                "recent_errors": {"healthy": False, "error_count": 50},
                "backup_health": {"healthy": False},
            },
            "recommendations": ["Check disk space", "Run backup"],
        }
        mock_system_recovery.check_system_health.return_value = mock_health

        result = run(["--health"])
        assert result == 1  # Should return error code for unhealthy system

    @patch("src.coterie_agents.commands.ops_hardening.system_recovery")
    def test_auto_repair_success(self, mock_system_recovery):
        """Test successful auto-repair."""
        mock_repair_result = {
            "success": True,
            "actions_taken": [
                "Restored corrupted.json from backup",
                "Cleaned up 5 temp files",
            ],
            "actions_failed": [],
        }
        mock_system_recovery.auto_repair.return_value = mock_repair_result

        result = run(["--repair"])
        assert result == 0

    @patch("src.coterie_agents.commands.ops_hardening.system_recovery")
    def test_auto_repair_with_failures(self, mock_system_recovery):
        """Test auto-repair with some failures."""
        mock_repair_result = {
            "success": True,
            "actions_taken": ["Cleaned up temp files"],
            "actions_failed": ["Could not repair database.json"],
        }
        mock_system_recovery.auto_repair.return_value = mock_repair_result

        result = run(["--repair"])
        assert result == 0

    def test_show_alerts_no_directory(self):
        """Test alert display when no alerts directory exists."""
        with patch("src.coterie_agents.commands.ops_hardening.Path") as mock_path:
            alerts_dir = MagicMock()
            alerts_dir.exists.return_value = False
            mock_path.return_value = alerts_dir

            result = run(["--alerts"])
            assert result == 0

    def test_show_alerts_with_alerts(self):
        """Test alert display with actual alerts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            alerts_dir = Path(temp_dir) / "alerts"
            alerts_dir.mkdir()

            # Create test alert file
            alert_file = alerts_dir / "alert_20250113.jsonl"
            test_alerts = [
                {
                    "timestamp": "2025-01-13T12:00:00",
                    "level": "critical",
                    "service": "database",
                    "message": "Connection failed",
                    "resolved": False,
                },
                {
                    "timestamp": "2025-01-13T11:30:00",
                    "level": "warning",
                    "service": "api",
                    "message": "High response time",
                    "resolved": False,
                },
            ]

            with open(alert_file, "w") as f:
                for alert in test_alerts:
                    f.write(json.dumps(alert) + "\n")

            with patch("src.coterie_agents.commands.ops_hardening.Path") as mock_path:
                mock_path.return_value = alerts_dir

                result = run(["--alerts"])
                assert result == 0

    @patch("src.coterie_agents.commands.ops_hardening.get_system_status")
    def test_ops_status_summary(self, mock_get_status):
        """Test ops status summary display."""
        mock_status = {
            "timestamp": "2025-01-13T12:00:00",
            "monitoring_enabled": True,
            "system_metrics": {
                "cpu_percent": 25.0,
                "memory_percent": 60.0,
                "disk_usage_percent": 75.0,
            },
            "service_health": {
                "api": {"status": "healthy"},
                "database": {"status": "degraded"},
            },
            "alert_summary": {"warning": 3, "critical": 1},
            "total_alerts": 4,
            "circuit_breaker_summary": {
                "external_api": "closed",
                "payment_service": "open",
            },
        }
        mock_get_status.return_value = mock_status

        result = run(["--status"])
        assert result == 0

    def test_invalid_command_shows_help(self):
        """Test that invalid commands show help."""
        result = run(["--invalid"])
        assert result == 0

    @patch("src.coterie_agents.commands.ops_hardening.collect_metrics")
    def test_monitor_with_exception(self, mock_collect_metrics):
        """Test monitoring dashboard with exception handling."""
        mock_collect_metrics.side_effect = Exception("Metrics collection failed")

        result = run(["--monitor"])
        assert result == 1

    @patch("src.coterie_agents.commands.ops_hardening.backup_manager")
    def test_backup_failure(self, mock_backup_manager):
        """Test backup creation failure."""
        mock_backup_result = {"success": False, "error": "Disk full"}
        mock_backup_manager.create_backup.return_value = mock_backup_result

        result = run(["--backup"])
        assert result == 1
