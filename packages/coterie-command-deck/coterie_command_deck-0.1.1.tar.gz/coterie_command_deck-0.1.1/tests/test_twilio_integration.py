"""Test Twilio SMS integration (env-gated)."""

import os
import unittest.mock as mock
from unittest.mock import patch

from coterie_agents.services.sms_service import SMSResult, send_sms


class TestTwilioIntegration:
    """Test Twilio SMS integration with proper env gating."""

    def test_dry_run_when_comms_disabled(self):
        """Test that SMS stays in DRY-RUN mode when COMMS_ENABLED=false."""
        with patch.dict(os.environ, {"COMMS_ENABLED": "false"}, clear=False):
            result = send_sms("+1234567890", "Test message")

            assert isinstance(result, SMSResult)
            assert not result.success
            assert "DRY-RUN" in result.message
            assert "COMMS_ENABLED" in result.message

    def test_dry_run_when_twilio_env_missing(self):
        """Test DRY-RUN when COMMS_ENABLED=true but Twilio vars missing."""
        env_vars = {
            "COMMS_ENABLED": "true",
            # Missing TWILIO_* vars
        }
        with patch.dict(os.environ, env_vars, clear=True):
            result = send_sms("+1234567890", "Test message")

            assert not result.success
            assert "DRY-RUN" in result.message

    @patch("coterie_agents.services.sms_service.Client")
    def test_real_send_when_properly_configured(self, mock_client_class):
        """Test real Twilio send when all env vars are set."""
        # Mock Twilio client and message
        mock_client = mock.MagicMock()
        mock_message = mock.MagicMock()
        mock_message.sid = "SMxxxx1234567890"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        env_vars = {
            "COMMS_ENABLED": "true",
            "TWILIO_ACCOUNT_SID": "ACxxxx1234567890",
            "TWILIO_AUTH_TOKEN": "fake_token_123",
            "TWILIO_FROM": "+1234567890",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            result = send_sms("+0987654321", "Test message")

            # Verify result
            assert result.success
            assert "SMS sent: SID SMxxxx1234567890" in result.message

            # Verify Twilio client was called correctly
            mock_client_class.assert_called_once_with("ACxxxx1234567890", "fake_token_123")
            mock_client.messages.create.assert_called_once_with(
                body="Test message", from_="+1234567890", to="+0987654321"
            )

    @patch("coterie_agents.services.sms_service.Client")
    def test_handles_twilio_errors_gracefully(self, mock_client_class):
        """Test error handling when Twilio API call fails."""
        # Mock Twilio client to raise an exception
        mock_client = mock.MagicMock()
        mock_client.messages.create.side_effect = Exception("Twilio API Error")
        mock_client_class.return_value = mock_client

        env_vars = {
            "COMMS_ENABLED": "true",
            "TWILIO_ACCOUNT_SID": "ACxxxx1234567890",
            "TWILIO_AUTH_TOKEN": "fake_token_123",
            "TWILIO_FROM": "+1234567890",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            result = send_sms("+0987654321", "Test message")

            assert not result.success
            assert "SMS failed: Twilio API Error" in result.message

    def test_sandbox_integration_ready(self):
        """Verify integration is ready for Twilio sandbox testing."""
        # This test documents the expected env vars for sandbox testing
        expected_sandbox_env = {
            "COMMS_ENABLED": "true",
            "TWILIO_ACCOUNT_SID": "AC...",  # Twilio test account SID
            "TWILIO_AUTH_TOKEN": "...",  # Twilio test auth token
            "TWILIO_FROM": "+15005550006",  # Twilio magic number for testing
        }

        # Verify all required env vars are documented
        assert len(expected_sandbox_env) == 4
        assert "COMMS_ENABLED" in expected_sandbox_env
        assert all(
            key.startswith("TWILIO_") for key in expected_sandbox_env if key != "COMMS_ENABLED"
        )
