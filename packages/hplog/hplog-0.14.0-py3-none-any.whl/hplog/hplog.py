from __future__ import annotations
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from pymongo.errors import ConfigurationError
import json
import pandas as pd
import dask.dataframe as dd
from typing import Any, Iterable, Mapping


class Connector:
    def __init__(self, uri: str, sql_mode: bool):
        self.uri = uri
        self.sql_mode = sql_mode

    def __str__(self) -> str:
        """Returns the connector URI."""
        return str(self.uri)


class GetLogsNamespace:
    """
    Namespace: foo.get_logs()  # callable
              foo.get_logs.to_pandas(...)
              foo.get_logs.to_dask(...)
              foo.get_logs.to_json(...)
    Kein interner, persistenter Zustand -> thread-/task-sicherer.
    """

    def __init__(self, hplog: HPLog):
        self._hplog = hplog

    async def __call__(
        self,
        *,
        limit: Optional[int] = None,
        query: Optional[Mapping[str, Any]] = None,
        projection: Optional[Mapping[str, int]] = None,
        sort: Optional[Iterable[tuple[str, int]]] = None,
    ) -> list[dict]:
        return await self._fetch(limit=limit, query=query, projection=projection, sort=sort)

    async def _fetch(
        self,
        *,
        limit: Optional[int],
        query: Optional[Mapping[str, Any]],
        projection: Optional[Mapping[str, int]],
        sort: Optional[Iterable[tuple[str, int]]],
    ) -> list[dict]:
        if self._hplog.connector.sql_mode:
            raise NotImplementedError("SQL fetching not implemented.")
        coll = self._hplog._get_collection()
        cur = coll.find(query or {}, projection=projection)
        # deterministische Reihenfolge: neueste zuerst
        cur = cur.sort(list(sort) if sort is not None else [("_id", -1)])
        docs = (
            await cur.to_list(length=limit or 10_000)
            if limit is not None
            else [doc async for doc in cur]
        )
        return docs

    # --- Convenience-Exporter ------------------------------------------------
    async def to_list(self, **kwargs) -> list[dict]:
        return await self._fetch(**self._normalize_kwargs(kwargs))

    async def to_json(self, **kwargs) -> str:
        docs = await self._fetch(**self._normalize_kwargs(kwargs))
        return json.dumps(docs, default=str, ensure_ascii=False)

    async def to_pandas(self, **kwargs) -> pd.DataFrame:
        docs = await self._fetch(**self._normalize_kwargs(kwargs))
        return pd.DataFrame(docs)

    async def to_dask(self, npartitions: int = 1, **kwargs) -> dd.DataFrame:
        df = await self.to_pandas(**kwargs)
        return dd.from_pandas(df, npartitions=npartitions)

    @staticmethod
    def _normalize_kwargs(kwargs: Mapping[str, Any]) -> dict:
        # erlaubt Kurzaufrufe wie: get_logs(limit=100) ohne weitere Parameter
        return {
            "limit": kwargs.get("limit"),
            "query": kwargs.get("query"),
            "projection": kwargs.get("projection"),
            "sort": kwargs.get("sort"),
        }


class HPLog:
    """Basic High Performance Logging class (Mongo + placeholder SQL)."""

    def __init__(self, connector: Connector, *, collection_name: str = "hplog_logs"):
        self.connector = connector
        self._client: Optional[AsyncIOMotorClient] = None
        self._collection_name = collection_name
        self.get_logs = GetLogsNamespace(self)

    # --- Client / DB helpers -------------------------------------------------

    def _ensure_client(self):
        if self._client is None:
            if self.connector.sql_mode:
                raise NotImplementedError("SQL mode not implemented.")
            self._client = AsyncIOMotorClient(self.connector.uri)
        return self._client

    def _get_db(self):
        """
        Returns the default DB from the URI.
        NOTE: This requires the Mongo URI to include a database name, e.g.
        'mongodb://localhost:27017/mydb'. Otherwise, an error is raised.
        """
        client = self._ensure_client()
        try:
            db = client.get_default_database()
        except ConfigurationError as e:
            raise ConfigurationError(
                "Mongo URI must include a database name (e.g., .../mydb)."
            ) from e
        return db

    def _get_collection(self):
        return self._get_db()[self._collection_name]

    async def aclose(self):
        """Close underlying client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    async def __aenter__(self):
        self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.aclose()

    def get_connector(self):
        return self.connector

    async def log(self, model: BaseModel):
        """
        Insert a Pydantic model into the log collection.
        Returns the inserted_id.
        """
        if self.connector.sql_mode:
            raise NotImplementedError("SQL logging not implemented.")
        document = model.model_dump(include=model.__class__.model_fields.keys())
        result = await self._get_collection().insert_one(document)
        return result.inserted_id
