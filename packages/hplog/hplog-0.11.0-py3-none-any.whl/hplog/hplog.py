from __future__ import annotations
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from pymongo.errors import ConfigurationError


class Connector:
    def __init__(self, uri: str, sql_mode: bool):
        self.uri = uri
        self.sql_mode = sql_mode

    def __str__(self) -> str:
        """Returns the connector URI."""
        return str(self.uri)


class HPLog:
    """Basic High Performance Logging class (Mongo + placeholder SQL)."""

    def __init__(self, connector: Connector, *, collection_name: str = "hplog_logs"):
        self.connector = connector
        self._client: Optional[AsyncIOMotorClient] = None
        self._collection_name = collection_name

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

    async def get_logs(self, limit: Optional[int] = None) -> list[dict]:
        """
        Fetch logs. If `limit` is provided, caps the number of docs returned.
        """
        if self.connector.sql_mode:
            raise NotImplementedError("SQL fetching not implemented.")
        cursor = self._get_collection().find({})
        if limit is not None:
            docs = await cursor.to_list(length=limit)
        else:
            docs = [doc async for doc in cursor]
        return docs