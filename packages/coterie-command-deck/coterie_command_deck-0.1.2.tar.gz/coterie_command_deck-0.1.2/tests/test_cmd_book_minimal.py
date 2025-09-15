"""Minimal smoke test for book command."""

from __future__ import annotations

import json
import os
import tempfile
from unittest import mock

from coterie_agents.commands import book


def test_book_help():
    """Test book command help."""
    result = book.run(["--help"])
    assert result == 0


def test_book_unknown_flag():
    """Test book command with unknown flag."""
    result = book.run(["--unknown"])
    assert result == 0


def test_book_missing_args():
    """Test book command with missing required arguments."""
    result = book.run([])
    assert result == 1


def test_book_missing_at_flag():
    """Test book command with missing --at flag."""
    result = book.run(["Rig wash"])
    assert result == 1


def test_book_invalid_datetime():
    """Test book command with invalid datetime format."""
    result = book.run(["Rig wash", "--at", "invalid-date"])
    assert result == 1


def test_book_valid_booking():
    """Test successful booking creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        booking_file = os.path.join(temp_dir, "bookings.json")

        # Mock the BOOKING_FILE constant to use temp file
        with mock.patch.object(book, "BOOKING_FILE", booking_file):
            result = book.run(["Rig wash", "--at", "2025-09-15T08:30"])
            assert result == 0

            # Verify booking was saved
            assert os.path.exists(booking_file)
            with open(booking_file) as f:
                bookings = json.load(f)
            assert len(bookings) == 1
            assert bookings[0]["job_title"] == "Rig wash"
            assert bookings[0]["datetime"] == "2025-09-15T08:30:00"


def test_book_with_duration_and_assignees():
    """Test booking with duration and assignees."""
    with tempfile.TemporaryDirectory() as temp_dir:
        booking_file = os.path.join(temp_dir, "bookings.json")

        with mock.patch.object(book, "BOOKING_FILE", booking_file):
            result = book.run(
                [
                    "Rig wash",
                    "--at",
                    "2025-09-15T08:30",
                    "--duration",
                    "90",
                    "--assignees",
                    "Jet,Mixie",
                ]
            )
            assert result == 0

            # Verify booking details
            with open(booking_file) as f:
                bookings = json.load(f)
            assert len(bookings) == 1
            booking = bookings[0]
            assert booking["job_title"] == "Rig wash"
            assert booking["duration_minutes"] == 90
            assert booking["assignees"] == ["Jet", "Mixie"]
