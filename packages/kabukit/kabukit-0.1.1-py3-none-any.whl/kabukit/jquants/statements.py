from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

import polars as pl

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, AsyncIterator

    from polars import DataFrame

    class Progress(Protocol):
        def __call__[T](
            self,
            async_iterable: AsyncIterable[T],
            total: int | None = None,
            *args: Any,
            **kwargs: Any,
        ) -> AsyncIterator[T]: ...


def clean(df: DataFrame) -> DataFrame:
    return (
        df.select(pl.exclude(r"^.*\(REIT\)$"))
        .rename(
            {"DisclosedDate": "Date", "DisclosedTime": "Time", "LocalCode": "Code"},
        )
        .with_columns(
            pl.col("^.*Date$").str.to_date("%Y-%m-%d", strict=False),
            pl.col("Time").str.to_time("%H:%M:%S", strict=False),
            pl.col("TypeOfCurrentPeriod").cast(pl.Categorical),
        )
        .pipe(_cast_float)
        .pipe(_cast_bool)
    )


def _cast_float(df: DataFrame) -> DataFrame:
    return df.with_columns(
        pl.col(f"^.*{name}.*$").cast(pl.Float64, strict=False)
        for name in [
            "Assets",
            "BookValue",
            "Cash",
            "Distributions",
            "Dividend",
            "Earnings",
            "Equity",
            "NetSales",
            "NumberOf",
            "PayoutRatio",
            "Profit",
        ]
    )


def _cast_bool(df: DataFrame) -> DataFrame:
    columns = df.select(pl.col("^.*Changes.*$")).columns
    columns.append("RetrospectiveRestatement")

    return df.with_columns(
        pl.when(pl.col(col) == "true")
        .then(True)  # noqa: FBT003
        .when(pl.col(col) == "false")
        .then(False)  # noqa: FBT003
        .otherwise(None)
        .alias(col)
        for col in columns
    )
