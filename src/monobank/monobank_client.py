import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from functools import partial

import monobank

if TYPE_CHECKING:
    from src.config import Config


@dataclass
class JarInfo:
    id: str
    title: str
    description: str
    currency: int  # ISO 4217 code (980 = UAH)
    balance: int  # in kopecks
    goal: int | None  # in kopecks, None if no goal


@dataclass
class JarTransaction:
    id: str
    time: datetime
    amount: int  # in kopecks (positive = incoming)
    comment: str | None

    @property
    def amount_uah(self) -> float:
        return self.amount / 100


class MonobankClient:
    def __init__(self, config: "Config"):
        self._config = config
        self._token = config.get_monobank_token()
        self._client: monobank.Client | None = None

    def _get_client(self) -> monobank.Client:
        """Get or create monobank client."""
        if self._client is None:
            self._client = monobank.Client(self._token)
        return self._client

    async def _run_sync(self, func, *args, **kwargs):
        """Run synchronous function in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def get_client_info(self) -> dict:
        """Get client info including jars."""
        client = self._get_client()
        return await self._run_sync(client.get_client_info)

    async def get_jars(self) -> list[JarInfo]:
        """Get list of all jars (банки)."""
        info = await self.get_client_info()
        jars = info.get("jars", [])

        return [
            JarInfo(
                id=jar["id"],
                title=jar.get("title", ""),
                description=jar.get("description", ""),
                currency=jar.get("currencyCode", 980),
                balance=jar.get("balance", 0),
                goal=jar.get("goal"),
            )
            for jar in jars
        ]

    async def get_jar_by_id(self, jar_id: str) -> JarInfo | None:
        """Get jar by ID."""
        jars = await self.get_jars()
        for jar in jars:
            if jar.id == jar_id:
                return jar
        return None

    async def get_statements(
        self,
        account_id: str,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> list[dict]:
        """
        Get account statements.
        Note: For jars, account_id should be the jar ID.
        """
        client = self._get_client()

        # Default: last 31 days (monobank limit)
        if from_time is None:
            from_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            from_time = from_time.replace(day=1)  # First day of month

        from_timestamp = int(from_time.timestamp())
        to_timestamp = int(to_time.timestamp()) if to_time else None

        if to_timestamp:
            return await self._run_sync(
                client.get_statements, account_id, from_timestamp, to_timestamp
            )
        else:
            return await self._run_sync(
                client.get_statements, account_id, from_timestamp
            )

    async def get_jar_transactions(
        self,
        jar_id: str | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> list[JarTransaction]:
        """
        Get transactions for a jar.
        If jar_id is None, uses jar_id from config.
        Returns only incoming transactions (donations).
        """
        jar_id = jar_id or self._config.get_jar_id()

        if not jar_id:
            raise ValueError("No jar_id provided and none in config")

        # Jar account ID format for statements
        account_id = f"jar/{jar_id}"

        try:
            statements = await self.get_statements(account_id, from_time, to_time)
        except Exception as e:
            print(f"[MonobankClient] Error getting statements: {e}")
            return []

        transactions = []
        for stmt in statements:
            # Only incoming transactions (positive amount)
            amount = stmt.get("amount", 0)
            if amount <= 0:
                continue

            transactions.append(
                JarTransaction(
                    id=stmt.get("id", ""),
                    time=datetime.fromtimestamp(stmt.get("time", 0)),
                    amount=amount,
                    comment=stmt.get("comment"),
                )
            )

        # Sort by time descending (newest first)
        transactions.sort(key=lambda t: t.time, reverse=True)

        return transactions

    async def get_jar_balance(self, jar_id: str | None = None) -> int:
        """Get current jar balance in kopecks."""
        jar_id = jar_id or self._config.get_jar_id()

        if not jar_id:
            raise ValueError("No jar_id provided and none in config")

        jar = await self.get_jar_by_id(jar_id)
        if jar:
            return jar.balance
        return 0
