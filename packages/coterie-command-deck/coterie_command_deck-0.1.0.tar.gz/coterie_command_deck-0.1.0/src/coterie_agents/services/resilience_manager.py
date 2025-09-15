"""
Ops hardening: Resilience and backup management service.

This service provides:
- Automated backup management
- System recovery capabilities
- Data integrity checks
import logging
logger = logging.getLogger(__name__)
- Recovery procedures
- Disaster recovery automation
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from ..commands.logger_config import error, info, warning


class BackupManager:
    """Manages system backups and recovery operations."""

    def __init__(self):
        self.backup_root = Path.home() / ".coterie" / "backups"
        self.backup_root.mkdir(parents=True, exist_ok=True)

        # Critical files that must be backed up
        self.critical_files = [
            "crew_status.json",
            "bookings.json",
            "inventory.json",
            "users.json",
            "command_log.jsonl",
            "coterie.log",
        ]

        self.enabled = True
        self.retention_days = 30
        self.max_backup_size_mb = 500

    def create_backup(self, backup_type: str = "scheduled") -> dict[str, Any]:
        """Create a comprehensive system backup."""
        if not self.enabled:
            return {"success": False, "message": "Backup disabled"}

        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / f"{backup_type}_{backup_timestamp}"
        backup_dir.mkdir(exist_ok=True)

        backup_info = {
            "timestamp": datetime.now().isoformat(),
            "type": backup_type,
            "files_backed_up": [],
            "files_skipped": [],
            "total_size_bytes": 0,
            "checksums": {},
            "success": True,
        }

        try:
            # Backup critical files
            for file_path in self.critical_files:
                source_path = Path(file_path)
                if source_path.exists():
                    dest_path = backup_dir / source_path.name
                    shutil.copy2(source_path, dest_path)

                    # Calculate checksum for integrity verification
                    checksum = self._calculate_checksum(dest_path)
                    backup_info["checksums"][source_path.name] = checksum
                    backup_info["files_backed_up"].append(str(source_path))
                    backup_info["total_size_bytes"] += dest_path.stat().st_size
                else:
                    backup_info["files_skipped"].append(str(source_path))

            # Backup logs directory
            logs_dir = Path("logs")
            if logs_dir.exists():
                backup_logs_dir = backup_dir / "logs"
                shutil.copytree(logs_dir, backup_logs_dir, ignore=shutil.ignore_patterns("*.tmp"))

                # Calculate total logs size
                for log_file in backup_logs_dir.rglob("*"):
                    if log_file.is_file():
                        backup_info["total_size_bytes"] += log_file.stat().st_size

            # Save backup metadata
            backup_info_file = backup_dir / "backup_info.json"
            with open(backup_info_file, "w") as f:
                json.dump(backup_info, f, indent=2)

            # Cleanup old backups
            self._cleanup_old_backups()

            info(
                f"Backup created successfully: {backup_dir.name} ({backup_info['total_size_bytes']} bytes)"
            )
            return backup_info

        except Exception as e:
            error(f"Backup creation failed: {e}")
            backup_info["success"] = False
            backup_info["error"] = str(e)
            return backup_info

    def restore_backup(
        self, backup_name: str, files_to_restore: list[str] | None = None
    ) -> dict[str, Any]:
        """Restore files from a backup."""
        backup_dir = self.backup_root / backup_name
        if not backup_dir.exists():
            return {"success": False, "message": f"Backup {backup_name} not found"}

        restore_info = {
            "timestamp": datetime.now().isoformat(),
            "backup_name": backup_name,
            "files_restored": [],
            "files_failed": [],
            "success": True,
        }

        try:
            # Load backup metadata if available
            backup_info_file = backup_dir / "backup_info.json"
            checksums = {}
            if backup_info_file.exists():
                with open(backup_info_file) as f:
                    backup_info = json.load(f)
                    checksums = backup_info.get("checksums", {})

            # Determine files to restore
            if files_to_restore is None:
                files_to_restore = [
                    f.name
                    for f in backup_dir.iterdir()
                    if f.is_file() and f.name != "backup_info.json"
                ]

            # Restore each file
            for filename in files_to_restore:
                source_path = backup_dir / filename
                dest_path = Path(filename)

                if not source_path.exists():
                    restore_info["files_failed"].append(f"{filename}: source not found")
                    continue

                # Create backup of existing file
                if dest_path.exists():
                    backup_existing = dest_path.with_suffix(f"{dest_path.suffix}.backup")
                    shutil.copy2(dest_path, backup_existing)

                # Restore the file
                shutil.copy2(source_path, dest_path)

                # Verify checksum if available
                if filename in checksums:
                    restored_checksum = self._calculate_checksum(dest_path)
                    if restored_checksum != checksums[filename]:
                        warning(f"Checksum mismatch for {filename}: backup may be corrupted")

                restore_info["files_restored"].append(filename)

            info(f"Restore completed: {len(restore_info['files_restored'])} files restored")
            return restore_info

        except Exception as e:
            error(f"Restore failed: {e}")
            restore_info["success"] = False
            restore_info["error"] = str(e)
            return restore_info

    def verify_backup_integrity(self, backup_name: str) -> dict[str, Any]:
        """Verify the integrity of a backup."""
        backup_dir = self.backup_root / backup_name
        if not backup_dir.exists():
            return {"success": False, "message": f"Backup {backup_name} not found"}

        verification_info = {
            "timestamp": datetime.now().isoformat(),
            "backup_name": backup_name,
            "files_verified": [],
            "files_corrupted": [],
            "files_missing": [],
            "success": True,
        }

        try:
            # Load backup metadata
            backup_info_file = backup_dir / "backup_info.json"
            if not backup_info_file.exists():
                return {"success": False, "message": "Backup metadata not found"}

            with open(backup_info_file) as f:
                backup_info = json.load(f)

            original_checksums = backup_info.get("checksums", {})

            # Verify each file
            for filename, expected_checksum in original_checksums.items():
                file_path = backup_dir / filename

                if not file_path.exists():
                    verification_info["files_missing"].append(filename)
                    continue

                actual_checksum = self._calculate_checksum(file_path)
                if actual_checksum == expected_checksum:
                    verification_info["files_verified"].append(filename)
                else:
                    verification_info["files_corrupted"].append(filename)

            # Determine overall success
            if verification_info["files_corrupted"] or verification_info["files_missing"]:
                verification_info["success"] = False

            return verification_info

        except Exception as e:
            error(f"Backup verification failed: {e}")
            verification_info["success"] = False
            verification_info["error"] = str(e)
            return verification_info

    def list_backups(self) -> list[dict[str, Any]]:
        """List all available backups."""
        backups = []

        try:
            for backup_dir in sorted(self.backup_root.iterdir()):
                if not backup_dir.is_dir():
                    continue

                backup_info = {
                    "name": backup_dir.name,
                    "created": datetime.fromtimestamp(backup_dir.stat().st_ctime).isoformat(),
                    "size_bytes": sum(
                        f.stat().st_size for f in backup_dir.rglob("*") if f.is_file()
                    ),
                    "file_count": len(list(backup_dir.rglob("*"))),
                }

                # Load additional info if available
                backup_info_file = backup_dir / "backup_info.json"
                if backup_info_file.exists():
                    try:
                        with open(backup_info_file) as f:
                            detailed_info = json.load(f)
                            backup_info.update(
                                {
                                    "type": detailed_info.get("type", "unknown"),
                                    "files_backed_up": len(
                                        detailed_info.get("files_backed_up", [])
                                    ),
                                    "success": detailed_info.get("success", True),
                                }
                            )
                    except Exception as e:
                        # Use basic info if detailed info is corrupted
                        warning(f"Could not load backup metadata for {backup_dir.name}: {e}")

                backups.append(backup_info)

        except Exception as e:
            error(f"Failed to list backups: {e}")

        return backups

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _cleanup_old_backups(self) -> None:
        """Remove backups older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        try:
            for backup_dir in self.backup_root.iterdir():
                if not backup_dir.is_dir():
                    continue

                created_time = datetime.fromtimestamp(backup_dir.stat().st_ctime)
                if created_time < cutoff_date:
                    shutil.rmtree(backup_dir)
                    info(f"Cleaned up old backup: {backup_dir.name}")

        except Exception as e:
            error(f"Backup cleanup failed: {e}")


class SystemRecovery:
    """Handles system recovery operations."""

    def __init__(self):
        self.backup_manager = BackupManager()

    def check_system_health(self) -> dict[str, Any]:
        """Comprehensive system health check."""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {},
            "recommendations": [],
        }

        # Check critical files
        critical_files_status = self._check_critical_files()
        health_status["checks"]["critical_files"] = critical_files_status

        # Check disk space
        disk_status = self._check_disk_space()
        health_status["checks"]["disk_space"] = disk_status

        # Check logs for errors
        log_status = self._check_recent_errors()
        health_status["checks"]["recent_errors"] = log_status

        # Check backup status
        backup_status = self._check_backup_health()
        health_status["checks"]["backup_health"] = backup_status

        # Determine overall status
        failing_checks = [
            check for check in health_status["checks"].values() if not check.get("healthy", True)
        ]

        if failing_checks:
            health_status["overall_status"] = "degraded" if len(failing_checks) < 3 else "unhealthy"

        return health_status

    def auto_repair(self) -> dict[str, Any]:
        """Attempt automatic system repairs."""
        repair_results = {
            "timestamp": datetime.now().isoformat(),
            "actions_taken": [],
            "actions_failed": [],
            "success": True,
        }

        try:
            # Repair corrupted JSON files
            for file_path in ["crew_status.json", "bookings.json", "inventory.json"]:
                if Path(file_path).exists():
                    try:
                        with open(file_path) as f:
                            json.load(f)  # Test if valid JSON
                    except json.JSONDecodeError:
                        # Try to restore from backup
                        if self._restore_from_latest_backup(file_path):
                            repair_results["actions_taken"].append(
                                f"Restored {file_path} from backup"
                            )
                        else:
                            repair_results["actions_failed"].append(f"Could not repair {file_path}")

            # Clean up temp files
            temp_files_removed = self._cleanup_temp_files()
            if temp_files_removed > 0:
                repair_results["actions_taken"].append(
                    f"Cleaned up {temp_files_removed} temp files"
                )

            # Rotate large log files
            rotated_logs = self._rotate_large_logs()
            if rotated_logs:
                repair_results["actions_taken"].append(f"Rotated logs: {', '.join(rotated_logs)}")

        except Exception as e:
            error(f"Auto-repair failed: {e}")
            repair_results["success"] = False
            repair_results["error"] = str(e)

        return repair_results

    def _check_critical_files(self) -> dict[str, Any]:
        """Check if critical files exist and are valid."""
        status = {"healthy": True, "missing_files": [], "corrupted_files": []}

        for file_path in self.backup_manager.critical_files:
            path = Path(file_path)

            if not path.exists():
                status["missing_files"].append(file_path)
                status["healthy"] = False
                continue

            # Check JSON files for validity
            if file_path.endswith(".json"):
                try:
                    with open(path) as f:
                        json.load(f)
                except json.JSONDecodeError:
                    status["corrupted_files"].append(file_path)
                    status["healthy"] = False

        return status

    def _check_disk_space(self) -> dict[str, Any]:
        """Check available disk space."""
        try:
            disk_usage = shutil.disk_usage(".")
            used_percent = (disk_usage.used / disk_usage.total) * 100

            return {
                "healthy": used_percent < 90,
                "used_percent": used_percent,
                "free_bytes": disk_usage.free,
                "total_bytes": disk_usage.total,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _check_recent_errors(self) -> dict[str, Any]:
        """Check for recent errors in logs."""
        log_file = Path("coterie.log")
        if not log_file.exists():
            return {"healthy": True, "error_count": 0}

        try:
            error_count = 0

            with open(log_file) as f:
                for line in f:
                    if "ERROR" in line or "CRITICAL" in line:
                        # Basic timestamp parsing - could be improved
                        error_count += 1

            return {
                "healthy": error_count < 10,
                "error_count": error_count,
                "threshold": 10,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _check_backup_health(self) -> dict[str, Any]:
        """Check backup system health."""
        backups = self.backup_manager.list_backups()

        if not backups:
            return {"healthy": False, "message": "No backups found"}

        # Check if latest backup is recent
        latest_backup = max(backups, key=lambda b: b["created"])
        latest_time = datetime.fromisoformat(latest_backup["created"])
        age_hours = (datetime.now() - latest_time).total_seconds() / 3600

        return {
            "healthy": age_hours < 24,
            "latest_backup_age_hours": age_hours,
            "total_backups": len(backups),
        }

    def _restore_from_latest_backup(self, filename: str) -> bool:
        """Restore a file from the latest backup."""
        try:
            backups = self.backup_manager.list_backups()
            if not backups:
                return False

            latest_backup = max(backups, key=lambda b: b["created"])
            result = self.backup_manager.restore_backup(latest_backup["name"], [filename])
            return result.get("success", False)
        except Exception:
            return False

    def _cleanup_temp_files(self) -> int:
        """Clean up temporary files."""
        temp_patterns = ["*.tmp", "*.temp", "*~", ".#*"]
        removed_count = 0

        for pattern in temp_patterns:
            for temp_file in Path(".").glob(pattern):
                try:
                    temp_file.unlink()
                    removed_count += 1
                except Exception as e:
                    logger.debug("Could not remove file: %s", e)
                    continue

        return removed_count

    def _rotate_large_logs(self) -> list[str]:
        """Rotate logs that are too large."""
        rotated = []
        max_size = 10 * 1024 * 1024  # 10MB

        for log_file in Path(".").glob("*.log"):
            try:
                if log_file.stat().st_size > max_size:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    rotated_name = f"{log_file.stem}_{timestamp}.log"
                    log_file.rename(rotated_name)

                    # Create new empty log file
                    log_file.touch()
                    rotated.append(log_file.name)
            except Exception as e:
                logger.debug("Could not rotate log file: %s", e)
                continue

        return rotated


# Global instances
backup_manager = BackupManager()
system_recovery = SystemRecovery()


def create_backup(backup_type: str = "manual") -> dict[str, Any]:
    """Convenience function to create a backup."""
    return backup_manager.create_backup(backup_type)


def check_system_health() -> dict[str, Any]:
    """Convenience function to check system health."""
    return system_recovery.check_system_health()


def auto_repair_system() -> dict[str, Any]:
    """Convenience function to attempt auto-repair."""
    return system_recovery.auto_repair()
