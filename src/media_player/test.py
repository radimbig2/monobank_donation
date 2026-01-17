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


if __name__ == "__main__":
    test_reload_media_list()
    test_random_selection()
    test_amount_based_selection()
    test_get_random_image()
    test_get_random_audio()
    print("\nAll MediaPlayer tests passed!")
