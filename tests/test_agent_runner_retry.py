"""Tests voor RetryConfig en run_agent_with_retry() — exponential backoff en foutafhandeling."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from pathlib import Path

import httpx
import pytest

from ollama.agent_runner import AgentRunner, RetryConfig


AGENTS_DIR = Path(__file__).parent.parent / "agents"


def _make_runner() -> AgentRunner:
    return AgentRunner(agents_dir=AGENTS_DIR)


# ─────────────────────────────────────────────────────────
# RetryConfig defaults
# ─────────────────────────────────────────────────────────

class TestRetryConfig:
    def test_default_values(self):
        cfg = RetryConfig()
        assert cfg.max_retries == 3
        assert cfg.delay_seconds == 2.0
        assert cfg.backoff_factor == 2.0

    def test_custom_values(self):
        cfg = RetryConfig(max_retries=1, delay_seconds=0.5, backoff_factor=1.5)
        assert cfg.max_retries == 1
        assert cfg.delay_seconds == 0.5
        assert cfg.backoff_factor == 1.5

    def test_zero_retries_allowed(self):
        cfg = RetryConfig(max_retries=0)
        assert cfg.max_retries == 0


# ─────────────────────────────────────────────────────────
# run_agent_with_retry — succes-scenario's
# ─────────────────────────────────────────────────────────

class TestRunAgentWithRetrySuccess:
    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        """Agent slaagt direct — geen retry nodig."""
        runner = _make_runner()
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Antwoord!")

        result, interaction_id = await runner.run_agent_with_retry(
            "klantenservice_agent",
            "Testinput",
            client=mock_client,
        )
        assert result == "Antwoord!"
        assert isinstance(interaction_id, str)
        # Generate slechts één keer aangeroepen
        mock_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_succeeds_on_second_attempt_after_timeout(self):
        """Agent slaagt na één timeout."""
        runner = _make_runner()
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.TimeoutException("Timeout!")
            return "Antwoord na retry"

        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(side_effect=mock_generate)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result, _ = await runner.run_agent_with_retry(
                "klantenservice_agent",
                "test",
                client=mock_client,
                retry_config=RetryConfig(max_retries=2, delay_seconds=0.01),
            )
        assert result == "Antwoord na retry"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_succeeds_on_third_attempt_after_connect_errors(self):
        """Agent slaagt na twee ConnectErrors."""
        runner = _make_runner()
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("Connectie geweigerd")
            return "Eindelijk verbonden"

        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(side_effect=mock_generate)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result, _ = await runner.run_agent_with_retry(
                "klantenservice_agent",
                "test",
                client=mock_client,
                retry_config=RetryConfig(max_retries=3, delay_seconds=0.01),
            )
        assert result == "Eindelijk verbonden"
        assert call_count == 3


# ─────────────────────────────────────────────────────────
# run_agent_with_retry — fout-scenario's
# ─────────────────────────────────────────────────────────

class TestRunAgentWithRetryFailures:
    @pytest.mark.asyncio
    async def test_raises_after_max_retries_exceeded(self):
        """Na max_retries+1 pogingen wordt de laatste exception gegooid."""
        runner = _make_runner()
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(
            side_effect=httpx.TimeoutException("Altijd timeout")
        )

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(httpx.TimeoutException):
                await runner.run_agent_with_retry(
                    "klantenservice_agent",
                    "test",
                    client=mock_client,
                    retry_config=RetryConfig(max_retries=2, delay_seconds=0.01),
                )
        assert mock_client.generate.call_count == 3  # 1 initieel + 2 retries

    @pytest.mark.asyncio
    async def test_non_retryable_exception_raised_immediately(self):
        """ValueError (niet-retrybaar) stopt direct zonder retry."""
        runner = _make_runner()
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(
            side_effect=ValueError("Ongeldig model opgegeven")
        )

        with pytest.raises(ValueError, match="Ongeldig model"):
            await runner.run_agent_with_retry(
                "klantenservice_agent",
                "test",
                client=mock_client,
                retry_config=RetryConfig(max_retries=3),
            )
        # Slechts één keer aangeroepen — geen retries
        assert mock_client.generate.call_count == 1

    @pytest.mark.asyncio
    async def test_nonexistent_agent_raises_value_error_immediately(self):
        """Onbestaande agent gooit meteen ValueError, geen retry."""
        runner = _make_runner()

        with pytest.raises(ValueError, match="niet gevonden"):
            await runner.run_agent_with_retry(
                "agent_bestaat_niet",
                "test",
                retry_config=RetryConfig(max_retries=3),
            )

    @pytest.mark.asyncio
    async def test_zero_retries_fails_immediately(self):
        """max_retries=0 → slechts één poging, daarna exception."""
        runner = _make_runner()
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout!")
        )

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(httpx.TimeoutException):
                await runner.run_agent_with_retry(
                    "klantenservice_agent",
                    "test",
                    client=mock_client,
                    retry_config=RetryConfig(max_retries=0, delay_seconds=0.01),
                )
        mock_client.generate.assert_called_once()
        mock_sleep.assert_not_called()


# ─────────────────────────────────────────────────────────
# Exponential backoff timing
# ─────────────────────────────────────────────────────────

class TestExponentialBackoff:
    @pytest.mark.asyncio
    async def test_backoff_delays_increase_exponentially(self):
        """Sleep-tijden volgen delay * backoff_factor^attempt patroon."""
        runner = _make_runner()
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise httpx.TimeoutException("Timeout!")
            return "Succes"

        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(side_effect=mock_generate)
        sleep_calls = []

        async def mock_sleep(seconds):
            sleep_calls.append(seconds)

        with patch("asyncio.sleep", side_effect=mock_sleep):
            await runner.run_agent_with_retry(
                "klantenservice_agent",
                "test",
                client=mock_client,
                retry_config=RetryConfig(max_retries=3, delay_seconds=1.0, backoff_factor=2.0),
            )

        # Eerste retry: 1.0 * 2.0^0 = 1.0, tweede retry: 1.0 * 2.0^1 = 2.0
        assert len(sleep_calls) == 2
        assert sleep_calls[0] == pytest.approx(1.0)
        assert sleep_calls[1] == pytest.approx(2.0)
