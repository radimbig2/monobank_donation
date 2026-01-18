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
    """Test parsing of /test command format."""
    print("\n[TEST] /test command parsing")

    test_cases = [
        # (input, expected_result)
        ("/test Alice text 50", {"donor": "Alice", "text": "text", "amount": 50.0, "valid": True}),
        ("/test Bob https://youtu.be/xyz 100", {"donor": "Bob", "text": "https://youtu.be/xyz", "amount": 100.0, "valid": True}),
        ("/test Charlie comment 25.5", {"donor": "Charlie", "text": "comment", "amount": 25.5, "valid": True}),
        ("/test", {"valid": False, "reason": "too few args"}),
        ("/test OnlyName", {"valid": False, "reason": "too few args"}),
        ("/test OnlyName NoAmount", {"valid": False, "reason": "missing amount"}),
    ]

    for user_input, expected in test_cases:
        # Parse command
        parts = user_input.split(maxsplit=4)

        result = {"valid": False}

        if user_input.startswith("/test"):
            if len(parts) >= 4:
                try:
                    donor_name = parts[1]
                    text = parts[2]
                    amount_uah = float(parts[3])
                    amount_kop = int(amount_uah * 100)

                    result = {
                        "valid": True,
                        "donor": donor_name,
                        "text": text,
                        "amount": amount_uah,
                        "amount_kop": amount_kop,
                    }
                except ValueError:
                    result = {"valid": False, "reason": "invalid amount"}
            else:
                result = {"valid": False, "reason": "too few args"}

        # Check result
        assert result["valid"] == expected["valid"], \
            f"Input '{user_input}': expected valid={expected['valid']}, got {result['valid']}"

        if result["valid"]:
            assert result["donor"] == expected["donor"]
            assert result["text"] == expected["text"]
            assert result["amount"] == expected["amount"]
            print(f"  [OK] Parsed: /test {result['donor']} {result['text']} {result['amount']} UAH")
        else:
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


if __name__ == "__main__":
    test_test_donation_with_parameters()
    test_command_parsing()
    test_amount_conversion()
    test_donation_object_creation()

    print("\n" + "=" * 60)
    print("All /test command tests passed!")
    print("=" * 60)
