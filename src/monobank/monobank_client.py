import aiohttp
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import Config

BASE_URL = "https://api.monobank.ua"


@dataclass
class JarInfo:
    id: str
    send_id: str
    title: str
    description: str
    currency_code: int  # ISO 4217 code (980 = UAH)
    balance: int  # in kopecks
    goal: int | None  # in kopecks, None if no goal

    @property
    def balance_uah(self) -> float:
        return self.balance / 100

    @property
    def goal_uah(self) -> float | None:
        return self.goal / 100 if self.goal else None


@dataclass
class JarTransaction:
    id: str
    time: datetime
    amount: int  # in kopecks (positive = incoming)
    description: str
    comment: str | None
    donor_name: str | None = None

    @property
    def amount_uah(self) -> float:
        return self.amount / 100

    @staticmethod
    def parse_donor_name(description: str) -> str | None:
        """Extract donor name from description.

        Examples:
        "From: John Doe" -> "John Doe"
        "From White Card" -> None
        """
        if description.startswith("Від: "):
            return description.replace("Від: ", "").strip()
        return None


class MonobankClient:
    def __init__(self, config: "Config"):
        self._config = config
        self._token = config.get_monobank_token()

    def _get_headers(self) -> dict:
        return {"X-Token": self._token}

    async def _request(self, endpoint: str) -> dict | list:
        """Make GET request to Monobank API."""
        url = f"{BASE_URL}{endpoint}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._get_headers()) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Monobank API error {response.status}: {error_text}")

                return await response.json()

    async def get_client_info(self) -> dict:
        """Get client info including accounts and jars."""
        return await self._request("/personal/client-info")

    async def get_jars(self) -> list[JarInfo]:
        """Get list of all jars (банки)."""
        info = await self.get_client_info()
        jars_raw = info.get("jars", [])

        return [
            JarInfo(
                id=jar["id"],
                send_id=jar.get("sendId", ""),
                title=jar.get("title", ""),
                description=jar.get("description", ""),
                currency_code=jar.get("currencyCode", 980),
                balance=jar.get("balance", 0),
                goal=jar.get("goal"),
            )
            for jar in jars_raw
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
        from_time: int,
        to_time: int | None = None,
    ) -> list[dict]:
        """
        Get account statements.

        Args:
            account_id: Account or jar ID
            from_time: Start time as Unix timestamp
            to_time: End time as Unix timestamp (optional, defaults to now)
        """
        if to_time:
            endpoint = f"/personal/statement/{account_id}/{from_time}/{to_time}"
        else:
            endpoint = f"/personal/statement/{account_id}/{from_time}"

        return await self._request(endpoint)

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

        # Default: last hour
        if from_time is None:
            from_timestamp = int(datetime.now().timestamp()) - 3600
        else:
            from_timestamp = int(from_time.timestamp())

        to_timestamp = int(to_time.timestamp()) if to_time else None

        try:
            statements = await self.get_statements(jar_id, from_timestamp, to_timestamp)
        except Exception as e:
            print(f"[MonobankClient] Error getting statements: {e}")
            return []

        transactions = []
        for stmt in statements:
            # Only incoming transactions (positive amount)
            amount = stmt.get("amount", 0)
            if amount <= 0:
                continue

            description = stmt.get("description", "")
            donor_name = JarTransaction.parse_donor_name(description)

            transactions.append(
                JarTransaction(
                    id=stmt.get("id", ""),
                    time=datetime.fromtimestamp(stmt.get("time", 0)),
                    amount=amount,
                    description=description,
                    comment=stmt.get("comment"),
                    donor_name=donor_name,
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
