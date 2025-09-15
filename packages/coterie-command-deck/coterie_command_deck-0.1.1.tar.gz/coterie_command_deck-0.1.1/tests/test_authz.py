"""Test authorization and role-based access control."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from coterie_agents.audit import audit_entry, audit_fields
from coterie_agents.authz import (
    _load_users,
    has_at_least,
    require_role,
    resolve_actor,
    role_of,
)


def test_load_users_default():
    """Test that _load_users returns default empty roles when no config exists."""
    with patch("coterie_agents.authz.CONFIG_PATHS", [Path("/nonexistent")]):
        users = _load_users()
        assert users == {"owner": [], "lead": [], "tech": [], "viewer": []}


def test_load_users_from_file():
    """Test loading users from a valid config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"owner": ["alice"], "lead": ["bob"], "tech": ["charlie"], "viewer": ["dave"]}')
        f.flush()

        with patch("coterie_agents.authz.CONFIG_PATHS", [Path(f.name)]):
            users = _load_users()
            assert users["owner"] == ["alice"]
            assert users["lead"] == ["bob"]
            assert users["tech"] == ["charlie"]
            assert users["viewer"] == ["dave"]


def test_resolve_actor_priority():
    """Test actor resolution priority: CLI > env > OS user."""
    with patch("getpass.getuser", return_value="osuser"):
        # CLI override takes precedence
        assert resolve_actor("cliuser") == "cliuser"

        # Env var with no CLI override
        with patch.dict(os.environ, {"DECK_USER": "envuser"}):
            assert resolve_actor() == "envuser"

        # OS user as fallback
        with patch.dict(os.environ, {}, clear=True):
            assert resolve_actor() == "osuser"


def test_role_of():
    """Test role resolution for users."""
    users = {
        "owner": ["alice"],
        "lead": ["bob"],
        "tech": ["charlie"],
        "viewer": ["dave"],
    }

    with patch("coterie_agents.authz.USERS", users):
        assert role_of("alice") == "owner"
        assert role_of("bob") == "lead"
        assert role_of("charlie") == "tech"
        assert role_of("dave") == "viewer"
        assert role_of("nobody") == "viewer"  # Default

        # Case insensitive
        assert role_of("ALICE") == "owner"


def test_has_at_least():
    """Test role hierarchy permissions."""
    users = {
        "owner": ["alice"],
        "lead": ["bob"],
        "tech": ["charlie"],
        "viewer": ["dave"],
    }

    with patch("coterie_agents.authz.USERS", users):
        # Owner has all permissions
        assert has_at_least("alice", "viewer") is True
        assert has_at_least("alice", "tech") is True
        assert has_at_least("alice", "lead") is True
        assert has_at_least("alice", "owner") is True

        # Tech can't access lead/owner
        assert has_at_least("charlie", "viewer") is True
        assert has_at_least("charlie", "tech") is True
        assert has_at_least("charlie", "lead") is False
        assert has_at_least("charlie", "owner") is False

        # Viewer only has viewer access
        assert has_at_least("dave", "viewer") is True
        assert has_at_least("dave", "tech") is False


def test_require_role_decorator():
    """Test the role requirement decorator."""
    users = {
        "owner": ["alice"],
        "lead": ["bob"],
        "tech": ["charlie"],
        "viewer": ["dave"],
    }

    with patch("coterie_agents.authz.USERS", users):

        @require_role("tech")
        def tech_command():
            return "success"

        # Test with sufficient permissions
        with patch("coterie_agents.authz.resolve_actor", return_value="alice"):
            result = tech_command()
            assert result == "success"

        with patch("coterie_agents.authz.resolve_actor", return_value="charlie"):
            result = tech_command()
            assert result == "success"

        # Test with insufficient permissions
        with patch("coterie_agents.authz.resolve_actor", return_value="dave"):
            result = tech_command()
            assert result == 2  # Access denied


def test_require_role_with_actor_override():
    """Test role decorator with actor override."""
    users = {"owner": ["alice"], "viewer": ["dave"]}

    with patch("coterie_agents.authz.USERS", users):

        @require_role("owner")
        def owner_command(**kwargs):
            return "success"

        # Override actor via _actor parameter
        result = owner_command(_actor="alice")
        assert result == "success"

        result = owner_command(_actor="dave")
        assert result == 2


# RBAC Matrix Tests - Production Users
def test_rbac_matrix_production_users():
    """Test RBAC matrix with production user assignments."""
    prod_users = {
        "owner": ["chase"],
        "lead": ["emerald_ghost"],
        "tech": ["jet", "mixie"],
        "viewer": [],
    }

    with patch("coterie_agents.authz.USERS", prod_users):
        # Chase (owner) - full access
        assert has_at_least("chase", "viewer") is True
        assert has_at_least("chase", "tech") is True
        assert has_at_least("chase", "lead") is True
        assert has_at_least("chase", "owner") is True

        # Emerald Ghost (lead) - up to lead
        assert has_at_least("emerald_ghost", "viewer") is True
        assert has_at_least("emerald_ghost", "tech") is True
        assert has_at_least("emerald_ghost", "lead") is True
        assert has_at_least("emerald_ghost", "owner") is False

        # Jet & Mixie (tech) - up to tech
        for tech_user in ["jet", "mixie"]:
            assert has_at_least(tech_user, "viewer") is True
            assert has_at_least(tech_user, "tech") is True
            assert has_at_least(tech_user, "lead") is False
            assert has_at_least(tech_user, "owner") is False

        # Random user defaults to viewer
        assert has_at_least("random", "viewer") is True
        assert has_at_least("random", "tech") is False


def test_viewer_blocked_on_sensitive_commands():
    """Test that viewer role is blocked on assign/invoice commands."""
    prod_users = {
        "owner": ["chase"],
        "lead": ["emerald_ghost"],
        "tech": ["jet", "mixie"],
        "viewer": [],
    }

    with patch("coterie_agents.authz.USERS", prod_users):
        # Simulate viewer trying assign (requires tech)
        @require_role("tech")
        def assign_command():
            return "success"

        # Simulate viewer trying invoice (requires owner)
        @require_role("owner")
        def invoice_command():
            return "success"

        # Test random user (defaults to viewer)
        with patch("coterie_agents.authz.resolve_actor", return_value="random"):
            assert assign_command() == 2  # Blocked
            assert invoice_command() == 2  # Blocked


def test_tech_permissions():
    """Test tech role permissions - allowed on end_job, blocked on invoice."""
    prod_users = {
        "owner": ["chase"],
        "lead": ["emerald_ghost"],
        "tech": ["jet", "mixie"],
        "viewer": [],
    }

    with patch("coterie_agents.authz.USERS", prod_users):

        @require_role("tech")
        def end_job_command():
            return "success"

        @require_role("owner")
        def invoice_command():
            return "success"

        # Test jet (tech user)
        with patch("coterie_agents.authz.resolve_actor", return_value="jet"):
            assert end_job_command() == "success"  # Allowed
            assert invoice_command() == 2  # Blocked


def test_lead_permissions():
    """Test lead role permissions - allowed on assign."""
    prod_users = {
        "owner": ["chase"],
        "lead": ["emerald_ghost"],
        "tech": ["jet", "mixie"],
        "viewer": [],
    }

    with patch("coterie_agents.authz.USERS", prod_users):

        @require_role("lead")
        def assign_command():
            return "success"

        # Test emerald_ghost (lead user)
        with patch("coterie_agents.authz.resolve_actor", return_value="emerald_ghost"):
            assert assign_command() == "success"  # Allowed


def test_deck_user_env_var_respected():
    """Test that DECK_USER environment variable is respected."""
    prod_users = {
        "owner": ["chase"],
        "lead": ["emerald_ghost"],
        "tech": ["jet", "mixie"],
        "viewer": [],
    }

    with (
        patch("coterie_agents.authz.USERS", prod_users),
        patch("getpass.getuser", return_value="osuser"),
    ):
        # DECK_USER should override OS user
        with patch.dict(os.environ, {"DECK_USER": "chase"}):
            assert resolve_actor() == "chase"
            assert role_of(resolve_actor()) == "owner"

        # Without DECK_USER, falls back to OS user
        with patch.dict(os.environ, {}, clear=True):
            assert resolve_actor() == "osuser"
            assert role_of(resolve_actor()) == "viewer"  # Default


def test_cli_as_override_respected():
    """Test that --as CLI override is respected."""
    prod_users = {
        "owner": ["chase"],
        "lead": ["emerald_ghost"],
        "tech": ["jet", "mixie"],
        "viewer": [],
    }

    with (
        patch("coterie_agents.authz.USERS", prod_users),
        patch("getpass.getuser", return_value="osuser"),
        patch.dict(os.environ, {"DECK_USER": "jet"}),
    ):
        # CLI override should have highest priority
        assert resolve_actor("chase") == "chase"
        assert role_of(resolve_actor("chase")) == "owner"

        # Without CLI override, uses DECK_USER
        assert resolve_actor() == "jet"
        assert role_of(resolve_actor()) == "tech"


def test_missing_users_json_defaults_to_viewer():
    """Test that missing users.json results in viewer role for all users."""
    with (
        patch("coterie_agents.authz.CONFIG_PATHS", [Path("/nonexistent")]),
        patch(
            "coterie_agents.authz.USERS",
            {"owner": [], "lead": [], "tech": [], "viewer": []},
        ),
    ):
        assert role_of("anyone") == "viewer"
        assert has_at_least("anyone", "viewer") is True
        assert has_at_least("anyone", "tech") is False


# Audit Tests
def test_audit_fields():
    """Test audit fields generation."""
    prod_users = {
        "owner": ["chase"],
        "lead": ["emerald_ghost"],
        "tech": ["jet", "mixie"],
        "viewer": [],
    }

    with patch("coterie_agents.authz.USERS", prod_users):
        # Test with DECK_USER
        with patch.dict(os.environ, {"DECK_USER": "chase"}):
            fields = audit_fields()
            assert fields == {"actor": "chase", "role": "owner"}

        # Test with CLI override
        fields = audit_fields("emerald_ghost")
        assert fields == {"actor": "emerald_ghost", "role": "lead"}


def test_audit_entry():
    """Test audit entry creation."""
    prod_users = {
        "owner": ["chase"],
        "lead": ["emerald_ghost"],
        "tech": ["jet", "mixie"],
        "viewer": [],
    }

    with (
        patch("coterie_agents.authz.USERS", prod_users),
        patch.dict(os.environ, {"DECK_USER": "jet"}),
    ):
        payload = {"action": "end_job", "job_id": "123"}
        entry = audit_entry(payload)

        expected = {
            "action": "end_job",
            "job_id": "123",
            "actor": "jet",
            "role": "tech",
        }
        assert entry == expected
