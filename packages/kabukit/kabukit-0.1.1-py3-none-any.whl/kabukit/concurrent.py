from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable, Iterable

MAX_CONCURRENCY = 12


async def collect[R](
    awaitables: Iterable[Awaitable[R]],
    /,
    max_concurrency: int | None = None,
) -> AsyncIterator[R]:
    max_concurrency = max_concurrency or MAX_CONCURRENCY
    semaphore = asyncio.Semaphore(max_concurrency)

    async def run(awaitable: Awaitable[R]) -> R:
        async with semaphore:
            return await awaitable

    futures = (run(awaitable) for awaitable in awaitables)

    async for future in asyncio.as_completed(futures):
        yield await future


async def collect_fn[T, R](
    function: Callable[[T], Awaitable[R]],
    args: Iterable[T],
    /,
    max_concurrency: int | None = None,
) -> AsyncIterator[R]:
    max_concurrency = max_concurrency or MAX_CONCURRENCY
    awaitables = (function(arg) for arg in args)

    async for item in collect(awaitables, max_concurrency=max_concurrency):
        yield item
