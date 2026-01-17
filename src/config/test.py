import sys
import tempfile
import yaml
from pathlib import Path

# Allow running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import Config
else:
    from . import Config

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_youtube_config_default():
    """Test YouTube config with default values."""
    config_data = {
        "server": {"port": 8080},
        "monobank": {"token": "test", "jar_id": "test", "poll_interval": 60},
        "media": {"path": "./media", "default_duration": 5000, "rules": []},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name

    try:
        config = Config(temp_config_path)
        min_donation = config.get_min_donation_for_music()
        assert min_donation == 0, f"Default should be 0, got {min_donation}"
        print("[PASS] test_youtube_config_default")
    finally:
        Path(temp_config_path).unlink()


def test_youtube_config_with_minimum():
    """Test YouTube config with custom minimum donation."""
    config_data = {
        "server": {"port": 8080},
        "monobank": {"token": "test", "jar_id": "test", "poll_interval": 60},
        "media": {"path": "./media", "default_duration": 5000, "rules": []},
        "youtube": {"min_donation_for_music": 50},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name

    try:
        config = Config(temp_config_path)
        min_donation = config.get_min_donation_for_music()
        assert min_donation == 50, f"Expected 50, got {min_donation}"
        print("[PASS] test_youtube_config_with_minimum")
    finally:
        Path(temp_config_path).unlink()


def test_media_rules_parsing():
    """Test that media rules are parsed correctly from config."""
    config_data = {
        "server": {"port": 8080},
        "monobank": {"token": "test", "jar_id": "test", "poll_interval": 60},
        "media": {
            "path": "./media",
            "default_duration": 5000,
            "rules": [
                {"min": 100, "max": 4999, "images": ["image1.gif"], "sounds": ["sound1.mp3"]},
                {"min": 5000, "max": 9999, "images": ["image2.gif"], "sounds": ["sound2.mp3"]},
                {"min": 10000, "max": None, "images": ["image3.gif"], "sounds": ["sound3.mp3"]},
            ],
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name

    try:
        config = Config(temp_config_path)
        rules = config.get_media_rules()

        assert len(rules) == 3, f"Expected 3 rules, got {len(rules)}"

        # Check first rule
        assert rules[0].min_amount == 100
        assert rules[0].max_amount == 4999
        assert rules[0].images == ["image1.gif"]
        assert rules[0].sounds == ["sound1.mp3"]

        # Check second rule
        assert rules[1].min_amount == 5000
        assert rules[1].max_amount == 9999
        assert rules[1].images == ["image2.gif"]
        assert rules[1].sounds == ["sound2.mp3"]

        # Check third rule (unbounded max)
        assert rules[2].min_amount == 10000
        assert rules[2].max_amount is None
        assert rules[2].images == ["image3.gif"]
        assert rules[2].sounds == ["sound3.mp3"]

        print("[PASS] test_media_rules_parsing")
    finally:
        Path(temp_config_path).unlink()


def test_media_rules_with_multiple_items():
    """Test media rules with multiple images and sounds."""
    config_data = {
        "server": {"port": 8080},
        "monobank": {"token": "test", "jar_id": "test", "poll_interval": 60},
        "media": {
            "path": "./media",
            "default_duration": 5000,
            "rules": [
                {
                    "min": 0,
                    "max": 999,
                    "images": ["img1.gif", "img2.gif", "img3.gif"],
                    "sounds": ["sound1.mp3", "sound2.mp3"],
                },
                {
                    "min": 1000,
                    "max": None,
                    "images": ["premium1.gif", "premium2.gif"],
                    "sounds": ["premium_sound.mp3"],
                },
            ],
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name

    try:
        config = Config(temp_config_path)
        rules = config.get_media_rules()

        assert len(rules) == 2, f"Expected 2 rules, got {len(rules)}"

        # Check first rule has multiple items
        assert len(rules[0].images) == 3
        assert len(rules[0].sounds) == 2

        # Check second rule
        assert len(rules[1].images) == 2
        assert len(rules[1].sounds) == 1

        print("[PASS] test_media_rules_with_multiple_items")
    finally:
        Path(temp_config_path).unlink()


def test_media_rules_min_max_order():
    """Test that media rules handle min/max correctly (order independent)."""
    config_data = {
        "server": {"port": 8080},
        "monobank": {"token": "test", "jar_id": "test", "poll_interval": 60},
        "media": {
            "path": "./media",
            "default_duration": 5000,
            "rules": [
                {"min": 1, "max": 99, "images": ["small.gif"], "sounds": ["small.mp3"]},
                {"min": 100, "max": 999, "images": ["medium.gif"], "sounds": ["medium.mp3"]},
                {"min": 1000, "max": None, "images": ["large.gif"], "sounds": ["large.mp3"]},
            ],
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name

    try:
        config = Config(temp_config_path)
        rules = config.get_media_rules()

        test_cases = [
            (1, 0, "min=1, max=99"),
            (50, 0, "mid=50"),
            (99, 0, "max=99"),
            (100, 1, "min=100, max=999"),
            (500, 1, "mid=500"),
            (999, 1, "max=999"),
            (1000, 2, "min=1000, max=None"),
            (10000, 2, "high=10000"),
        ]

        for amount, expected_rule_idx, desc in test_cases:
            rule = rules[expected_rule_idx]
            if amount >= rule.min_amount:
                if rule.max_amount is None or amount <= rule.max_amount:
                    assert True, f"Amount {amount} ({desc}) matches rule {expected_rule_idx}"
                    print(f"[OK] Amount {amount} ({desc}) -> Rule {expected_rule_idx}")

        print("[PASS] test_media_rules_min_max_order")
    finally:
        Path(temp_config_path).unlink()


if __name__ == "__main__":
    test_youtube_config_default()
    test_youtube_config_with_minimum()
    test_media_rules_parsing()
    test_media_rules_with_multiple_items()
    test_media_rules_min_max_order()
    print("\nAll Config tests passed!")
