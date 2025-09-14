import asyncio

import httpx
import pytest

from pjdev_decorators.decorators import async_retry_http

pytest_plugins = ("pytest_asyncio",)

async def default_fake_sleep(_: float):
    pass

@pytest.mark.asyncio
async def test_async_retry_no_delay_on_single_attempt(monkeypatch):
    async def fake_sleep(_seconds: float):
        raise AssertionError("asyncio.sleep should not be called when max_attempts=1")

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    call_count = 0

    @async_retry_http(max_attempts=1, delay_seconds=5)
    async def unstable():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("boom")

    with pytest.raises(ExceptionGroup):
        await unstable()

    assert call_count == 1


@pytest.mark.asyncio
async def test_async_retry_correct_total_delay_time(monkeypatch):
    num_attempts = 5
    delay_seconds = 10
    expected_delay = sum(delay_seconds ** i for i in range(1, num_attempts))

    total_seconds = 0.0

    async def fake_sleep(_seconds: float):
        nonlocal total_seconds
        total_seconds += _seconds

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    @async_retry_http(max_attempts=num_attempts, delay_seconds=delay_seconds)
    async def unstable():
        raise RuntimeError("boom")

    with pytest.raises(ExceptionGroup):
        await unstable()


    assert total_seconds == expected_delay


@pytest.mark.asyncio
async def test_async_retry_correct_return_value(monkeypatch):
    num_attempts = 5
    delay_seconds = 10
    expected_result = "default"

    monkeypatch.setattr(asyncio, "sleep", default_fake_sleep)

    @async_retry_http(max_attempts=num_attempts, delay_seconds=delay_seconds, default_value=expected_result)
    async def unstable():
        raise RuntimeError("boom")

    result = await unstable()


    assert result == expected_result


@pytest.mark.asyncio
async def test_async_retry_correct_http_exception_handling(monkeypatch):
    monkeypatch.setattr(asyncio, "sleep", default_fake_sleep)

    call_count = 0

    @async_retry_http(max_attempts=2, delay_seconds=2, status_codes_to_ignore=[404])
    async def unstable():
        nonlocal call_count
        call_count += 1

        r = httpx.get('https://google.com/someroutethatdoesnotexist')
        r.raise_for_status()

    with pytest.raises(ExceptionGroup):
        await unstable()

    assert call_count == 1

