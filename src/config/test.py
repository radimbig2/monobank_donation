import tempfile
from pathlib import Path
from .config import Config


def test_default_values():
    """Test that Config returns default values when no config file exists."""
    config = Config("nonexistent.yaml")

    assert config.get_port() == 8080
    assert config.get_host() == "localhost"
    assert config.get_poll_interval() == 60
    assert config.get_media_path() == "./media"
    assert config.get_default_duration() == 5000
    print("[PASS] test_default_values")


def test_load_from_file():
    """Test loading config from YAML file."""
    yaml_content = """
server:
  port: 9000
  host: "0.0.0.0"

monobank:
  token: "test_token"
  jar_id: "test_jar"
  poll_interval: 30

media:
  path: "./custom_media"
  default_duration: 3000
  rules:
    - min: 0
      max: 5000
      images: ["small.gif"]
      sounds: ["small.mp3"]
    - min: 5000
      max: null
      images: ["big.gif"]
      sounds: ["big.mp3"]
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        config = Config(temp_path)

        assert config.get_port() == 9000
        assert config.get_host() == "0.0.0.0"
        assert config.get_monobank_token() == "test_token"
        assert config.get_jar_id() == "test_jar"
        assert config.get_poll_interval() == 30
        assert config.get_media_path() == "./custom_media"
        assert config.get_default_duration() == 3000

        rules = config.get_media_rules()
        assert len(rules) == 2
        assert rules[0].min_amount == 0
        assert rules[0].max_amount == 5000
        assert rules[1].max_amount is None

        print("[PASS] test_load_from_file")
    finally:
        Path(temp_path).unlink()


def test_reload():
    """Test config reload functionality."""
    yaml_content_v1 = """
server:
  port: 8080
"""
    yaml_content_v2 = """
server:
  port: 9999
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content_v1)
        temp_path = f.name

    try:
        config = Config(temp_path)
        assert config.get_port() == 8080

        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(yaml_content_v2)

        config.reload()
        assert config.get_port() == 9999

        print("[PASS] test_reload")
    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    test_default_values()
    test_load_from_file()
    test_reload()
    print("\nAll Config tests passed!")
