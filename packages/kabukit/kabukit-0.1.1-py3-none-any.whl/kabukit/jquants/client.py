from __future__ import annotations

import datetime
import os
from enum import StrEnum
from typing import TYPE_CHECKING

import polars as pl
from httpx import AsyncClient
from polars import DataFrame

from kabukit.config import load_dotenv, set_key
from kabukit.params import get_params

from . import statements

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any, Self

    from httpx import HTTPStatusError  # noqa: F401
    from httpx._types import QueryParamTypes

API_VERSION = "v1"
BASE_URL = f"https://api.jquants.com/{API_VERSION}"


class AuthKey(StrEnum):
    """J-Quants認証のための環境変数キー。"""

    REFRESH_TOKEN = "JQUANTS_REFRESH_TOKEN"  # noqa: S105
    ID_TOKEN = "JQUANTS_ID_TOKEN"  # noqa: S105


class JQuantsClient:
    """J-Quants APIと対話するためのクライアント。

    API認証トークン（リフレッシュトークンおよびIDトークン）を管理し、
    各種J-Quants APIエンドポイントへアクセスするメソッドを提供する。
    トークンは設定ファイルから読み込まれ、またファイルに保存される。

    Attributes:
        client: APIリクエストを行うための `AsyncClient` インスタンス。
    """

    client: AsyncClient

    def __init__(self, id_token: str | None = None) -> None:
        self.client = AsyncClient(base_url=BASE_URL)
        self.set_id_token(id_token)

    def set_id_token(self, id_token: str | None = None) -> None:
        """IDトークンをヘッダーに設定する。

        Args:
            id_token (str | None, optional): 設定するIDトークン。
                Noneの場合、環境変数から読み込む。
        """

        if id_token is None:
            load_dotenv()
            id_token = os.environ.get(AuthKey.ID_TOKEN)

        if id_token:
            self.client.headers["Authorization"] = f"Bearer {id_token}"

    async def aclose(self) -> None:
        """HTTPクライアントを閉じる。"""
        await self.client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # pyright: ignore[reportMissingParameterType, reportUnknownParameterType]  # noqa: ANN001
        await self.aclose()

    async def auth(
        self,
        mailaddress: str,
        password: str,
        *,
        save: bool = False,
    ) -> Self:
        """認証を行い、トークンを保存する。

        Args:
            mailaddress (str): J-Quantsに登録したメールアドレス。
            password (str): J-Quantsのパスワード。
            save (bool, optional): トークンを環境変数に保存するかどうか。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        refresh_token = await self.get_refresh_token(mailaddress, password)
        id_token = await self.get_id_token(refresh_token)

        if save:
            set_key(AuthKey.REFRESH_TOKEN, refresh_token)
            set_key(AuthKey.ID_TOKEN, id_token)

        self.set_id_token(id_token)
        return self

    async def post(self, url: str, json: Any | None = None) -> Any:
        """指定されたURLにPOSTリクエストを送信する。

        Args:
            url: POSTリクエストのURLパス。
            json: リクエストボディのJSONペイロード。

        Returns:
            APIからのJSONレスポンス。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        resp = await self.client.post(url, json=json)
        resp.raise_for_status()
        return resp.json()

    async def get_refresh_token(self, mailaddress: str, password: str) -> str:
        """APIから新しいリフレッシュトークンを取得する。

        Args:
            mailaddress (str): ユーザーのメールアドレス。
            password (str): ユーザーのパスワード。

        Returns:
            新しいリフレッシュトークン。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        json_data = {"mailaddress": mailaddress, "password": password}
        data = await self.post("/token/auth_user", json=json_data)
        return data["refreshToken"]

    async def get_id_token(self, refresh_token: str) -> str:
        """APIから新しいIDトークンを取得する。

        Args:
            refresh_token (str): 使用するリフレッシュトークン。

        Returns:
            新しいIDトークン。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        url = f"/token/auth_refresh?refreshtoken={refresh_token}"
        data = await self.post(url)
        return data["idToken"]

    async def get(self, url: str, params: QueryParamTypes | None = None) -> Any:
        """指定されたURLにGETリクエストを送信する。

        Args:
            url (str): GETリクエストのURLパス。
            params (QueryParamTypes | None, optional): リクエストのクエリパラメータ。

        Returns:
            APIからのJSONレスポンス。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_info(
        self,
        code: str | None = None,
        date: str | datetime.date | None = None,
    ) -> DataFrame:
        """銘柄情報を取得する。

        Args:
            code (str | None, optional): 情報を取得する銘柄のコード。
            date (str | datetime.date | None, optional): 情報を取得する日付。

        Returns:
            銘柄情報を含むPolars DataFrame。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        params = get_params(code=code, date=date)
        url = "/listed/info"
        data = await self.get(url, params)
        df = DataFrame(data["info"])

        return df.with_columns(
            pl.col("Date").str.to_date("%Y-%m-%d"),
            pl.col("^.*CodeName$", "ScaleCategory").cast(pl.Categorical),
        ).drop("^.+Code$", "CompanyNameEnglish")

    async def iter_pages(
        self,
        url: str,
        params: dict[str, Any] | None,
        name: str,
    ) -> AsyncIterator[DataFrame]:
        """ページ分割されたAPIレスポンスを反復処理する。

        Args:
            url (str): APIエンドポイントのベースURL。
            params (dict[str, Any]): クエリパラメータの辞書。
            name (str): アイテムのリストを含むJSONレスポンスのキー。

        Yields:
            データの各ページに対応するPolars DataFrame。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        params = params or {}

        while True:
            data = await self.get(url, params)
            yield DataFrame(data[name])
            if "pagination_key" in data:
                params["pagination_key"] = data["pagination_key"]
            else:
                break

    async def get_prices(
        self,
        code: str | None = None,
        date: str | datetime.date | None = None,
        from_: str | datetime.date | None = None,
        to: str | datetime.date | None = None,
    ) -> DataFrame:
        """日々の株価四本値を取得する。

        Args:
            code: 株価を取得する銘柄のコード。
            date: 株価を取得する特定の日付。`from_`または`to`とは併用不可。
            from_: 取得期間の開始日。`date`とは併用不可。
            to: 取得期間の終了日。`date`とは併用不可。

        Returns:
            日々の株価四本値を含むPolars DataFrame。

        Raises:
            ValueError: `date`と`from_`/`to`の両方が指定された場合。
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        if not date and not code:
            return await self.get_latest_available_prices()

        if date and (from_ or to):
            msg = "Cannot specify both date and from/to parameters."
            raise ValueError(msg)

        params = get_params(code=code, date=date, from_=from_, to=to)

        url = "/prices/daily_quotes"
        name = "daily_quotes"

        dfs = [df async for df in self.iter_pages(url, params, name)]
        df = pl.concat(dfs)

        if df.is_empty():
            return df

        return df.with_columns(
            pl.col("Date").str.to_date("%Y-%m-%d"),
            pl.col("^.*Limit$").cast(pl.Int8).cast(pl.Boolean),
        )

    async def get_latest_available_prices(self) -> DataFrame:
        """直近利用可能な日付の株価を取得する。"""
        today = datetime.date.today()  # noqa: DTZ011

        for days in range(30):
            date = today - datetime.timedelta(days)
            df = await self.get_prices(date=date)

            if not df.is_empty():
                return df

        return DataFrame()

    async def get_statements(
        self,
        code: str | None = None,
        date: str | datetime.date | None = None,
    ) -> DataFrame:
        """財務情報を取得する。

        Args:
            code: 財務情報を取得する銘柄のコード。
            date: 財務情報を取得する日付。

        Returns:
            財務情報を含むPolars DataFrame。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        params = get_params(code=code, date=date)
        url = "/fins/statements"
        name = "statements"

        dfs = [df async for df in self.iter_pages(url, params, name)]
        df = pl.concat(dfs)

        if df.is_empty():
            return df

        return statements.clean(df)

    async def get_announcement(self) -> DataFrame:
        """翌日発表予定の決算情報を取得する。

        Returns:
            開示情報を含むPolars DataFrame。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        url = "fins/announcement"
        name = "announcement"

        dfs = [df async for df in self.iter_pages(url, {}, name)]
        df = pl.concat(dfs)
        if df.is_empty():
            return df

        return df.with_columns(pl.col("Date").str.to_date("%Y-%m-%d", strict=False))

    async def get_trades_spec(
        self,
        section: str | None = None,
        from_: str | datetime.date | None = None,
        to: str | datetime.date | None = None,
    ) -> DataFrame:
        """投資部門別の情報を取得する。

        Args:
            section: 絞り込み対象のセクション。
            from_: 取得期間の開始日。
            to: 取得期間の終了日。

        Returns:
            投資部門別の情報を含むPolars DataFrame。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        params = get_params(section=section, from_=from_, to=to)

        url = "/markets/trades_spec"
        name = "trades_spec"

        dfs = [df async for df in self.iter_pages(url, params, name)]
        df = pl.concat(dfs)
        if df.is_empty():
            return df

        return df.with_columns(pl.col("^.*Date$").str.to_date("%Y-%m-%d", strict=False))
