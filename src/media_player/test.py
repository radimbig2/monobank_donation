import sys
from pathlib import Path

# Allow running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import Config
    from src.media_player.media_player import MediaPlayer, MediaSelection
else:
    from src.config import Config
    from .media_player import MediaPlayer, MediaSelection

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_reload_media_list():
    """Test that media files are discovered correctly."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))
    player = MediaPlayer(config, project_root=PROJECT_ROOT)

    images = player.get_all_images()
    audio = player.get_all_audio()

    print(f"[INFO] Found images: {images}")
    print(f"[INFO] Found audio: {audio}")

    assert len(images) > 0, "Should find at least one image"
    assert len(audio) > 0, "Should find at least one audio file"

    print("[PASS] test_reload_media_list")


def test_random_selection():
    """Test random media selection."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))
    player = MediaPlayer(config, project_root=PROJECT_ROOT)

    # Test multiple times to ensure randomness works
    for _ in range(5):
        selection = player.select_media()
        assert selection is not None, "Selection should not be None"
        assert selection.image_path, "Should have image path"
        print(f"[INFO] Random selection: {selection}")

    print("[PASS] test_random_selection")


def test_amount_based_selection():
    """Test selection based on donation amount."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))
    player = MediaPlayer(config, project_root=PROJECT_ROOT)

    # Test different amounts (in kopecks)
    test_amounts = [
        (1000, "small donation ~10 UAH"),
        (5000, "medium donation ~50 UAH"),
        (10000, "large donation ~100 UAH"),
        (50000, "very large donation ~500 UAH"),
    ]

    for amount, desc in test_amounts:
        selection = player.select_media(amount)
        assert selection is not None, f"Selection for {desc} should not be None"
        print(f"[INFO] {desc} ({amount} kop): {selection}")

    print("[PASS] test_amount_based_selection")


def test_get_random_image():
    """Test getting random image."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))
    player = MediaPlayer(config, project_root=PROJECT_ROOT)

    image = player.get_random_image()
    assert image is not None, "Should get random image"
    print(f"[INFO] Random image: {image}")

    print("[PASS] test_get_random_image")


def test_get_random_audio():
    """Test getting random audio."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))
    player = MediaPlayer(config, project_root=PROJECT_ROOT)

    audio = player.get_random_audio()
    assert audio is not None, "Should get random audio"
    print(f"[INFO] Random audio: {audio}")

    print("[PASS] test_get_random_audio")


def test_amount_based_rule_selection():
    """Test that correct media rule is selected based on donation amount ranges."""
    import tempfile
    import yaml
    from src.config.config import MediaRule

    # Create temporary config with known rules
    config_data = {
        "server": {"port": 8080, "host": "localhost", "show_test_button": True, "player_volume": 0.7},
        "monobank": {"token": "test", "jar_id": "test", "poll_interval": 60},
        "media": {
            "path": "./media",
            "default_duration": 5000,
            "rules": [
                {"min": 100, "max": 4999, "images": ["video/small.gif"], "sounds": ["audio/small.mp3"]},
                {"min": 5000, "max": 9999, "images": ["video/medium.gif"], "sounds": ["audio/medium.mp3"]},
                {"min": 10000, "max": None, "images": ["video/large.gif"], "sounds": ["audio/large.mp3"]},
            ],
        },
    }

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name

    try:
        config = Config(temp_config_path)
        player = MediaPlayer(config, project_root=PROJECT_ROOT)

        print("\n[TEST] Amount-based rule selection:")
        print(f"[INFO] Rules from config: {config.get_media_rules()}")

        test_cases = [
            # (amount_in_kopecks, expected_rule_index, description)
            (100, 0, "Minimum of first rule (100 kop = 1 UAH)"),
            (1000, 0, "Within first rule (1000 kop = 10 UAH)"),
            (4999, 0, "Maximum of first rule (4999 kop)"),
            (5000, 1, "Minimum of second rule (5000 kop = 50 UAH)"),
            (7500, 1, "Within second rule (7500 kop = 75 UAH)"),
            (9999, 1, "Maximum of second rule (9999 kop)"),
            (10000, 2, "Minimum of third rule (10000 kop = 100 UAH)"),
            (50000, 2, "High amount in third rule (50000 kop = 500 UAH)"),
            (100000, 2, "Very high amount in third rule (100000 kop = 1000 UAH)"),
        ]

        for amount, expected_idx, desc in test_cases:
            selection = player.select_media(amount)
            assert selection is not None, f"Selection for {desc} should not be None"

            # Get the expected rule
            rules = config.get_media_rules()
            expected_rule = rules[expected_idx]

            # Verify the correct image and audio were selected from the rule
            assert selection.image_path in expected_rule.images, \
                f"{desc}: Image {selection.image_path} not in rule {expected_idx} images: {expected_rule.images}"
            assert selection.audio_path in expected_rule.sounds or selection.audio_path is None, \
                f"{desc}: Audio {selection.audio_path} not in rule {expected_idx} sounds: {expected_rule.sounds}"

            print(
                f"[OK] {desc}\n"
                f"     Amount: {amount} kop ({amount/100:.2f} UAH)\n"
                f"     Selected: {selection.image_path} + {selection.audio_path}"
            )

        print("[PASS] test_amount_based_rule_selection")

    finally:
        # Clean up temporary file
        Path(temp_config_path).unlink()


def test_rule_boundaries():
    """Test boundary conditions for media rule selection."""
    import tempfile
    import yaml

    config_data = {
        "server": {"port": 8080, "host": "localhost", "show_test_button": True, "player_volume": 0.7},
        "monobank": {"token": "test", "jar_id": "test", "poll_interval": 60},
        "media": {
            "path": "./media",
            "default_duration": 5000,
            "rules": [
                {"min": 1, "max": 99, "images": ["video/rule1.gif"], "sounds": ["audio/rule1.mp3"]},
                {"min": 100, "max": 999, "images": ["video/rule2.gif"], "sounds": ["audio/rule2.mp3"]},
                {"min": 1000, "max": None, "images": ["video/rule3.gif"], "sounds": ["audio/rule3.mp3"]},
            ],
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name

    try:
        config = Config(temp_config_path)
        player = MediaPlayer(config, project_root=PROJECT_ROOT)

        print("\n[TEST] Rule boundary conditions:")

        test_cases = [
            (1, 0, "First boundary: exactly at min of rule 1"),
            (99, 0, "First boundary: exactly at max of rule 1"),
            (100, 1, "Second boundary: exactly at min of rule 2"),
            (999, 1, "Second boundary: exactly at max of rule 2"),
            (1000, 2, "Third boundary: exactly at min of rule 3 (unbounded)"),
            (999999, 2, "Third boundary: very high value in unbounded rule"),
        ]

        for amount, expected_idx, desc in test_cases:
            selection = player.select_media(amount)
            assert selection is not None, f"{desc}: Should return selection"

            rules = config.get_media_rules()
            expected_rule = rules[expected_idx]

            assert selection.image_path in expected_rule.images, \
                f"{desc}: Got wrong rule. Expected rule {expected_idx}, got image from different rule"

            print(f"[OK] {desc} -> Rule {expected_idx}: {selection.image_path}")

        print("[PASS] test_rule_boundaries")

    finally:
        Path(temp_config_path).unlink()


if __name__ == "__main__":
    test_reload_media_list()
    test_random_selection()
    test_amount_based_selection()
    test_get_random_image()
    test_get_random_audio()
    test_amount_based_rule_selection()
    test_rule_boundaries()
    print("\nAll MediaPlayer tests passed!")
