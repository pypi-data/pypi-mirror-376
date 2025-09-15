from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

import polars as pl

from kabukit.concurrent import collect_fn

from .client import JQuantsClient
from .info import get_codes

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, AsyncIterator, Callable, Iterable

    from polars import DataFrame

    class Progress(Protocol):
        def __call__[T](
            self,
            aiterable: AsyncIterable[T],
            total: int | None = None,
            *args: Any,
            **kwargs: Any,
        ) -> AsyncIterator[T]: ...


type Callback = Callable[[DataFrame], DataFrame | None]


@dataclass
class Stream:
    """JQuantsから各種データを銘柄コードごとにストリーム形式で取得する。"""

    resource: str
    codes: list[str]
    max_concurrency: int | None = None

    async def __aiter__(self) -> AsyncIterator[DataFrame]:
        async with JQuantsClient() as client:
            fn = getattr(client, f"get_{self.resource}")

            async for df in collect_fn(fn, self.codes, self.max_concurrency):
                yield df


async def fetch(
    resource: str,
    codes: Iterable[str],
    /,
    max_concurrency: int | None = None,
    progress: Progress | None = None,
    callback: Callback | None = None,
) -> DataFrame:
    """全銘柄の各種データを取得し、単一のDataFrameにまとめて返す。

    Args:
        resource (str): 取得するデータの種類。JQuantsClientのメソッド名から"get_"を
            除いたものを指定する。
        codes (Iterable[str]): 取得対象の銘柄コードのリスト。
        max_concurrency (int | None, optional): 同時に実行するリクエストの最大数。
            指定しないときはデフォルト値が使用される。
        progress (Progress | None, optional): 進捗表示のための関数。
            tqdm, marimoなどのライブラリを使用できる。
            指定しないときは進捗表示は行われない。
        callback (Callback | None, optional): 各DataFrameに対して適用する
            コールバック関数。指定しないときはそのままのDataFrameが使用される。

    Returns:
        DataFrame:
            すべての銘柄の財務情報を含む単一のDataFrame。
    """
    codes = list(codes)
    stream = Stream(resource, codes, max_concurrency)

    if progress:
        stream = progress(aiter(stream), total=len(codes))

    if callback:
        stream = (x if (r := callback(x)) is None else r async for x in stream)

    return pl.concat([df async for df in stream if not df.is_empty()])


async def fetch_all(
    resource: str,
    /,
    limit: int | None = None,
    max_concurrency: int | None = None,
    progress: Progress | None = None,
    callback: Callback | None = None,
) -> DataFrame:
    """全銘柄の各種データを取得し、単一のDataFrameにまとめて返す。

    Args:
        resource (str): 取得するデータの種類。JQuantsClientのメソッド名から"get_"を
            除いたものを指定する。
        limit (int | None, optional): 取得する銘柄数の上限。
            指定しないときはすべての銘柄が対象となる。
        max_concurrency (int | None, optional): 同時に実行するリクエストの最大数。
            指定しないときはデフォルト値が使用される。
        progress (Progress | None, optional): 進捗表示のための関数。
            tqdm, marimoなどのライブラリを使用できる。
            指定しないときは進捗表示は行われない。
        callback (Callback | None, optional): 各DataFrameに対して適用する
            コールバック関数。指定しないときはそのままのDataFrameが使用される。

    Returns:
        DataFrame:
            すべての銘柄の財務情報を含む単一のDataFrame。
    """

    codes = await get_codes()
    codes = codes[:limit]

    return await fetch(
        resource,
        codes,
        max_concurrency=max_concurrency,
        progress=progress,
        callback=callback,
    )
