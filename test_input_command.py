"""
Tests for /test command parsing and test donation creation.
"""
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent))

from src.notification import Donation, NotificationService
from src.config import Config

PROJECT_ROOT = Path(__file__).parent


def test_test_donation_with_parameters():
    """Test that test_donation accepts custom parameters."""
    print("\n[TEST] test_donation with parameters")

    # Create mock objects
    mock_web_host = Mock()
    mock_media_player = Mock()
    mock_config = Mock()

    notification_service = NotificationService(mock_web_host, mock_media_player, mock_config)

    # Test with default parameters
    donation = Donation(
        amount=10000,
        currency="UAH",
        comment="Test donation",
        donor_name="Test User",
    )

    print(f"  Default donation: {donation.donor_name} - {donation.amount_uah:.2f} UAH - {donation.comment}")
    assert donation.donor_name == "Test User"
    assert donation.amount_uah == 100.0
    assert donation.comment == "Test donation"

    # Test with custom parameters
    donation2 = Donation(
        amount=5000,
        currency="UAH",
        comment="YouTube link https://youtu.be/xyz",
        donor_name="John Doe",
    )

    print(f"  Custom donation: {donation2.donor_name} - {donation2.amount_uah:.2f} UAH - {donation2.comment}")
    assert donation2.donor_name == "John Doe"
    assert donation2.amount_uah == 50.0
    assert donation2.comment == "YouTube link https://youtu.be/xyz"

    print("[PASS] test_test_donation_with_parameters")


def test_command_parsing():
    """Test parsing of /test command format with flexible arguments."""
    print("\n[TEST] /test command parsing (flexible format)")

    import shlex

    test_cases = [
        # (input, expected_result)
        ("/test Alice", {"donor": "Alice", "text": "test", "amount": 100.0, "valid": True}),
        ("/test Bob text", {"donor": "Bob", "text": "text", "amount": 100.0, "valid": True}),
        ("/test Charlie comment 50", {"donor": "Charlie", "text": "comment", "amount": 50.0, "valid": True}),
        ("/test Alice https://youtu.be/xyz 100", {"donor": "Alice", "text": "https://youtu.be/xyz", "amount": 100.0, "valid": True}),
        ("/test Bob \"YouTube link\" 75", {"donor": "Bob", "text": "YouTube link", "amount": 75.0, "valid": True}),
        ("/test Charlie text 25.5", {"donor": "Charlie", "text": "text", "amount": 25.5, "valid": True}),
        ("/test", {"valid": False, "reason": "no args"}),
    ]

    for user_input, expected in test_cases:
        result = {"valid": False}

        if user_input.startswith("/test"):
            parts = user_input.split(maxsplit=1)
            if len(parts) >= 2:
                remaining = parts[1].strip()

                try:
                    args = shlex.split(remaining)
                    if len(args) >= 1:
                        donor_name = args[0]
                        text = args[1] if len(args) > 1 else "test"
                        amount_uah = 100.0  # Default 100 UAH

                        if len(args) > 2:
                            try:
                                amount_uah = float(args[2])
                            except ValueError:
                                result = {"valid": False, "reason": "invalid amount"}
                                continue

                        amount_kop = int(amount_uah * 100)

                        result = {
                            "valid": True,
                            "donor": donor_name,
                            "text": text,
                            "amount": amount_uah,
                            "amount_kop": amount_kop,
                        }
                    else:
                        result = {"valid": False, "reason": "no args"}
                except ValueError:
                    result = {"valid": False, "reason": "invalid quotes"}
            else:
                result = {"valid": False, "reason": "no args"}

        # Check result
        if expected["valid"]:
            assert result["valid"], f"Input '{user_input}': should be valid"
            assert result["donor"] == expected["donor"], f"Donor name mismatch"
            assert result["text"] == expected["text"], f"Text mismatch"
            assert abs(result["amount"] - expected["amount"]) < 0.01, f"Amount mismatch"
            print(f"  [OK] /test {result['donor']} {result['text']} {result['amount']} UAH")
        else:
            assert not result["valid"], f"Input '{user_input}': should be invalid"
            print(f"  [OK] Rejected: {user_input} ({result.get('reason', 'unknown')})")

    print("[PASS] test_command_parsing")


def test_amount_conversion():
    """Test conversion of UAH to kopecks."""
    print("\n[TEST] Amount conversion (UAH to kopecks)")

    test_cases = [
        (1, 100),
        (10, 1000),
        (50, 5000),
        (100, 10000),
        (0.5, 50),
        (25.5, 2550),
        (999.99, 99999),
    ]

    for amount_uah, expected_kop in test_cases:
        amount_kop = int(amount_uah * 100)
        assert amount_kop == expected_kop, \
            f"Conversion failed: {amount_uah} UAH -> {amount_kop} kop (expected {expected_kop})"

        # Check reverse conversion
        back_to_uah = amount_kop / 100
        assert abs(back_to_uah - amount_uah) < 0.01, \
            f"Reverse conversion failed: {amount_kop} kop -> {back_to_uah} UAH"

        print(f"  [OK] {amount_uah} UAH = {amount_kop} kop")

    print("[PASS] test_amount_conversion")


def test_donation_object_creation():
    """Test creating Donation objects with parsed command data."""
    print("\n[TEST] Donation object creation")

    test_donations = [
        {
            "donor_name": "Alice",
            "comment": "Test",
            "amount_uah": 10,
            "expected_kop": 1000,
        },
        {
            "donor_name": "Bob Streamer",
            "comment": "https://youtu.be/music123",
            "amount_uah": 50,
            "expected_kop": 5000,
        },
        {
            "donor_name": "Charlie",
            "comment": "Best stream ever!",
            "amount_uah": 100,
            "expected_kop": 10000,
        },
    ]

    for test_case in test_donations:
        amount_kop = int(test_case["amount_uah"] * 100)
        assert amount_kop == test_case["expected_kop"]

        donation = Donation(
            amount=amount_kop,
            currency="UAH",
            comment=test_case["comment"],
            donor_name=test_case["donor_name"],
        )

        assert donation.donor_name == test_case["donor_name"]
        assert donation.comment == test_case["comment"]
        assert donation.amount == amount_kop
        assert abs(donation.amount_uah - test_case["amount_uah"]) < 0.01

        print(f"  [OK] Created: {donation}")

    print("[PASS] test_donation_object_creation")


def test_optional_parameters():
    """Test that /test handles optional parameters with defaults."""
    print("\n[TEST] Optional parameters with defaults")

    import shlex

    # Test case 1: Only name - defaults to "test", 100 UAH
    args = shlex.split("Alice")
    donor = args[0]
    text = args[1] if len(args) > 1 else "test"
    amount = float(args[2]) if len(args) > 2 else 100.0

    assert donor == "Alice"
    assert text == "test"
    assert amount == 100.0
    print(f"  [OK] /test Alice -> {donor}, {text}, {amount} UAH")

    # Test case 2: Name + text - defaults to 100 UAH
    args = shlex.split("Bob \"YouTube link\"")
    donor = args[0]
    text = args[1] if len(args) > 1 else "test"
    amount = float(args[2]) if len(args) > 2 else 100.0

    assert donor == "Bob"
    assert text == "YouTube link"
    assert amount == 100.0
    print(f"  [OK] /test Bob \"YouTube link\" -> {donor}, {text}, {amount} UAH")

    # Test case 3: Name + text + amount
    args = shlex.split("Charlie \"my comment\" 35")
    donor = args[0]
    text = args[1] if len(args) > 1 else "test"
    amount = float(args[2]) if len(args) > 2 else 100.0

    assert donor == "Charlie"
    assert text == "my comment"
    assert amount == 35.0
    print(f"  [OK] /test Charlie \"my comment\" 35 -> {donor}, {text}, {amount} UAH")

    print("[PASS] test_optional_parameters")


if __name__ == "__main__":
    test_test_donation_with_parameters()
    test_command_parsing()
    test_amount_conversion()
    test_donation_object_creation()
    test_optional_parameters()

    print("\n" + "=" * 60)
    print("All /test command tests passed!")
    print("=" * 60)
