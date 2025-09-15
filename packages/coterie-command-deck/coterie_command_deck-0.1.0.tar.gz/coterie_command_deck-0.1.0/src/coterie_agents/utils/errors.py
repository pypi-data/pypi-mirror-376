"""Error handling utilities with retry logic and structured error messages."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any


class RetryableError(Exception):
    """Base class for errors that can be retried."""

    pass


class NetworkError(RetryableError):
    """Network-related error that can be retried."""

    pass


class TemporaryError(RetryableError):
    """Temporary error that can be retried."""

    pass


class PermanentError(Exception):
    """Permanent error that should not be retried."""

    pass


def format_error_message(error: Exception, context: str = "") -> str:
    """Format error message with context and suggestions."""
    error_msg = str(error)

    # Build structured error message
    parts = [f"[❌] {type(error).__name__}"]
    if context:
        parts.append(f"in {context}")
    parts.append(f": {error_msg}")

    message = " ".join(parts)

    # Add suggestions based on error type
    suggestions = _get_error_suggestions(error)
    if suggestions:
        message += f"\n[💡] Try: {suggestions}"

    return message


def _get_error_suggestions(error: Exception) -> str:
    """Get contextual suggestions based on error type."""
    error_msg = str(error).lower()

    # Network-related errors
    if isinstance(error, NetworkError | ConnectionError) or "network" in error_msg:
        return "Check network connection, try --retries 3"

    # File system errors
    if "permission" in error_msg or "access" in error_msg:
        return "Check file permissions or run with appropriate privileges"

    if "not found" in error_msg or "no such file" in error_msg:
        return "Verify file path exists, try absolute path"

    # API/Service errors
    if "401" in error_msg or "unauthorized" in error_msg:
        return "Check credentials or tokens, try re-authentication"

    if "429" in error_msg or "rate limit" in error_msg:
        return "Wait and retry with --retries 3, or check rate limits"

    if "timeout" in error_msg:
        return "Increase timeout or check network stability"

    # Command-specific suggestions
    if "invalid" in error_msg and "format" in error_msg:
        return "Check command syntax with --help"

    # General suggestions
    return "Check command syntax with --help, or try with verbose logging"


def retry_with_backoff(
    func: Callable[..., Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_delay: float = 60.0,
) -> Callable[..., Any]:
    """Decorator to add retry logic with exponential backoff."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except PermanentError:
                # Don't retry permanent errors
                raise
            except RetryableError as e:
                last_error = e
                if attempt < max_retries:
                    delay = min(base_delay * (backoff_multiplier**attempt), max_delay)
                    print(f"[⚠️] Attempt {attempt + 1} failed: {e}")
                    print(f"[⏳] Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                else:
                    # Final attempt failed
                    break
            except Exception as e:
                # Treat unknown exceptions as non-retryable by default
                last_error = e
                break

        # All retries exhausted or permanent error
        if last_error:
            raise last_error

        return None  # Should never reach here

    return wrapper


def handle_command_errors(func: Callable[..., int]) -> Callable[..., int]:
    """Decorator to handle command errors with structured output."""

    def wrapper(*args: Any, **kwargs: Any) -> int:
        try:
            # Extract --retries flag if present
            argv = args[0] if args and isinstance(args[0], list) else []
            max_retries = _extract_retries_flag(argv)

            if max_retries > 0:
                # Apply retry logic
                retry_func = retry_with_backoff(func, max_retries)
                return retry_func(*args, **kwargs)
            else:
                # No retries requested
                return func(*args, **kwargs)

        except Exception as e:
            # Format and print structured error message
            command_name = getattr(func, "__module__", "command")
            if "." in command_name:
                command_name = command_name.split(".")[-1].replace("_", " ")

            error_msg = format_error_message(e, command_name)
            print(error_msg)
            return 1

    return wrapper


def _extract_retries_flag(argv: list[str]) -> int:
    """Extract --retries flag value from command arguments."""
    try:
        if "--retries" in argv:
            retries_idx = argv.index("--retries")
            if retries_idx + 1 < len(argv):
                return int(argv[retries_idx + 1])
    except (ValueError, IndexError):
        pass
    return 0


def suggest_retry_command(original_command: str, retries: int = 3) -> str:
    """Generate a retry command suggestion."""
    if "--retries" in original_command:
        return original_command
    else:
        return f"{original_command} --retries {retries}"
