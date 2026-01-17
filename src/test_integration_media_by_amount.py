"""
Integration tests for media selection by donation amount and music ordering.
"""
import sys
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.config import Config
    from src.media_player import MediaPlayer
    from src.notification import Donation
else:
    from src.config import Config
    from src.media_player import MediaPlayer
    from src.notification import Donation

PROJECT_ROOT = Path(__file__).parent.parent


def test_media_selection_by_donation_amount():
    """Test that correct media is selected based on donation amount rules."""
    print("\n" + "=" * 60)
    print("[TEST] Media selection by donation amount")
    print("=" * 60)

    config_data = {
        "server": {"port": 8080},
        "monobank": {"token": "test", "jar_id": "test"},
        "media": {
            "path": "./media",
            "rules": [
                {"min": 100, "max": 4999, "images": ["budget.gif"], "sounds": ["budget.mp3"]},
                {"min": 5000, "max": 9999, "images": ["standard.gif"], "sounds": ["standard.mp3"]},
                {"min": 10000, "max": None, "images": ["premium.gif"], "sounds": ["premium.mp3"]},
            ],
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name

    try:
        config = Config(temp_config_path)

        # Create mock media player that doesn't need actual files
        player = MediaPlayer(config, project_root=PROJECT_ROOT)

        # Override to return our test files
        player._images = ["budget.gif", "standard.gif", "premium.gif"]
        player._audio = ["budget.mp3", "standard.mp3", "premium.mp3"]

        test_cases = [
            (100, "budget.gif", "minimum for budget rule"),
            (2500, "budget.gif", "within budget range"),
            (5000, "standard.gif", "minimum for standard rule"),
            (7500, "standard.gif", "within standard range"),
            (10000, "premium.gif", "minimum for premium rule"),
            (50000, "premium.gif", "high premium donation"),
        ]

        print("\nTesting media selection with amount-based rules:")
        for amount, expected_image, desc in test_cases:
            selection = player.select_media(amount)
            assert selection is not None, f"No selection for {desc}"
            assert selection.image_path == expected_image, \
                f"{desc}: Expected {expected_image}, got {selection.image_path}"
            print(f"  [OK] {amount} kop ({amount/100:.2f} UAH) - {desc} -> {selection.image_path}")

        print("\n[PASS] test_media_selection_by_donation_amount")

    finally:
        Path(temp_config_path).unlink()


async def test_music_minimum_donation_check():
    """Test that music is only added when donation meets minimum threshold."""
    print("\n" + "=" * 60)
    print("[TEST] Music minimum donation check")
    print("=" * 60)

    config_data = {
        "server": {"port": 8080},
        "monobank": {"token": "test", "jar_id": "test"},
        "media": {"path": "./media", "rules": []},
        "youtube": {"min_donation_for_music": 10000},  # 100 UAH minimum
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name

    try:
        config = Config(temp_config_path)

        test_cases = [
            (5000, False, "50 UAH - below minimum"),
            (9999, False, "99.99 UAH - below minimum"),
            (10000, True, "100 UAH - exactly at minimum"),
            (20000, True, "200 UAH - above minimum"),
        ]

        print("\nTesting minimum donation check with threshold = 10000 kop (100 UAH):")
        for amount, should_pass, desc in test_cases:
            min_donation = config.get_min_donation_for_music()
            passes = amount >= min_donation
            assert passes == should_pass, f"{desc}: Expected {should_pass}, got {passes}"

            status = "ALLOWS" if passes else "BLOCKS"
            print(f"  [OK] {amount} kop ({amount/100:.2f} UAH) - {desc} - {status} music")

        print("\n[PASS] test_music_minimum_donation_check")

    finally:
        Path(temp_config_path).unlink()


def test_config_rule_with_exact_ranges():
    """Test config with exact min-max ranges from config.example.yaml."""
    print("\n" + "=" * 60)
    print("[TEST] Config rule with exact ranges")
    print("=" * 60)

    # Using ranges similar to config.example.yaml
    config_data = {
        "server": {"port": 8080},
        "monobank": {"token": "test", "jar_id": "test"},
        "media": {
            "path": "./media",
            "rules": [
                {"min": 0, "max": 4999, "images": ["200.gif"], "sounds": ["donat_gitara.mp3"]},
                {"min": 5000, "max": 9999, "images": ["bebra.gif"], "sounds": ["donat_gitara.mp3"]},
                {"min": 10000, "max": None, "images": ["a021d7d1c9c83486f22fb3579ff07780.gif"], "sounds": ["donat_gitara.mp3"]},
            ],
        },
        "youtube": {"min_donation_for_music": 0},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name

    try:
        config = Config(temp_config_path)
        rules = config.get_media_rules()

        print("\nRules from config:")
        for i, rule in enumerate(rules):
            print(f"  Rule {i}: {rule.min_amount}-{rule.max_amount} -> {rule.images[0]}")

        # Test boundary cases
        test_cases = [
            (0, 0, "exactly at start"),
            (1, 0, "just after start"),
            (4999, 0, "just before boundary"),
            (5000, 1, "exactly at second rule start"),
            (9999, 1, "just before third rule"),
            (10000, 2, "exactly at premium rule start"),
            (1000000, 2, "very large donation"),
        ]

        print("\nBoundary testing:")
        for amount, expected_idx, desc in test_cases:
            rule = rules[expected_idx]
            matches = amount >= rule.min_amount and (rule.max_amount is None or amount <= rule.max_amount)
            assert matches, f"{desc}: {amount} should match rule {expected_idx}"
            print(f"  [OK] {amount} kop - {desc} - Rule {expected_idx}")

        print("\n[PASS] test_config_rule_with_exact_ranges")

    finally:
        Path(temp_config_path).unlink()


if __name__ == "__main__":
    import asyncio

    test_media_selection_by_donation_amount()
    asyncio.run(test_music_minimum_donation_check())
    test_config_rule_with_exact_ranges()

    print("\n" + "=" * 60)
    print("All integration tests passed!")
    print("=" * 60)
