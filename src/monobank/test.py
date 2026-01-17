import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Allow running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import Config
    from src.monobank.monobank_client import MonobankClient, JarInfo, JarTransaction
else:
    from src.config import Config
    from .monobank_client import MonobankClient, JarInfo, JarTransaction

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_dataclasses():
    """Test dataclasses."""
    jar = JarInfo(
        id="test123",
        send_id="send123",
        title="Test Jar",
        description="My test jar",
        currency_code=980,
        balance=150000,
        goal=1000000,
    )

    assert jar.id == "test123"
    assert jar.balance == 150000
    assert jar.balance_uah == 1500.0
    assert jar.goal_uah == 10000.0
    print(f"[INFO] JarInfo: {jar}")

    tx = JarTransaction(
        id="tx123",
        time=datetime.now(),
        amount=5000,
        description="Від: Тест Користувач",
        comment="Test donation",
    )

    assert tx.amount_uah == 50.0
    assert tx.donor_name == "Тест Користувач"
    print(f"[INFO] JarTransaction: {tx}")

    # Test donor name parsing
    assert JarTransaction.parse_donor_name("Від: Радим Воронянський") == "Радим Воронянський"
    assert JarTransaction.parse_donor_name("З Білої картки") is None
    print("[INFO] Donor name parsing works correctly")

    print("[PASS] test_dataclasses")


async def test_get_client_info():
    """Test getting client info (requires valid token)."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))

    if config.get_monobank_token() == "YOUR_MONOBANK_TOKEN":
        print("[SKIP] test_get_client_info - no token configured")
        return

    client = MonobankClient(config)
    info = await client.get_client_info()

    print(f"[INFO] Client name: {info.get('name')}")
    print(f"[INFO] Accounts: {len(info.get('accounts', []))}")
    print(f"[INFO] Jars: {len(info.get('jars', []))}")

    print("[PASS] test_get_client_info")


async def test_get_jars():
    """Test getting jars list (requires valid token)."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))

    if config.get_monobank_token() == "YOUR_MONOBANK_TOKEN":
        print("[SKIP] test_get_jars - no token configured")
        return

    client = MonobankClient(config)
    jars = await client.get_jars()

    print(f"[INFO] Found {len(jars)} jars:")
    for jar in jars:
        goal_str = f" / {jar.goal_uah:.2f}" if jar.goal_uah else ""
        print(f"  - {jar.title}: {jar.balance_uah:.2f}{goal_str} UAH (ID: {jar.id})")

    print("[PASS] test_get_jars")


async def test_get_jar_transactions():
    """Test getting jar transactions (requires valid token and jar_id)."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))

    if config.get_monobank_token() == "YOUR_MONOBANK_TOKEN":
        print("[SKIP] test_get_jar_transactions - no token configured")
        return

    if config.get_jar_id() == "YOUR_JAR_ID":
        print("[SKIP] test_get_jar_transactions - no jar_id configured")
        return

    client = MonobankClient(config)

    print(f"[INFO] Getting transactions for jar: {config.get_jar_id()}")
    transactions = await client.get_jar_transactions()

    print(f"[INFO] Found {len(transactions)} incoming transactions:")
    for tx in transactions[:5]:  # Show first 5
        comment = tx.comment or tx.description or "(no comment)"
        print(f"  - {tx.time}: {tx.amount_uah:.2f} UAH - {comment}")

    print("[PASS] test_get_jar_transactions")


async def test_get_jar_balance():
    """Test getting jar balance (requires valid token and jar_id)."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))

    if config.get_monobank_token() == "YOUR_MONOBANK_TOKEN":
        print("[SKIP] test_get_jar_balance - no token configured")
        return

    if config.get_jar_id() == "YOUR_JAR_ID":
        print("[SKIP] test_get_jar_balance - no jar_id configured")
        return

    client = MonobankClient(config)

    balance = await client.get_jar_balance()
    print(f"[INFO] Jar balance: {balance / 100:.2f} UAH")

    print("[PASS] test_get_jar_balance")


if __name__ == "__main__":
    test_dataclasses()

    print("\n" + "=" * 50)
    print("Running API tests (require valid token)...")
    print("=" * 50 + "\n")

    asyncio.run(test_get_client_info())
    asyncio.run(test_get_jars())
    asyncio.run(test_get_jar_transactions())
    asyncio.run(test_get_jar_balance())

    print("\nAll MonobankClient tests completed!")
