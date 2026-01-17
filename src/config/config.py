from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml


@dataclass
class MediaRule:
    min_amount: int
    max_amount: int | None
    images: list[str] = field(default_factory=list)
    sounds: list[str] = field(default_factory=list)


@dataclass
class ServerConfig:
    port: int = 8080
    host: str = "localhost"


@dataclass
class MonobankConfig:
    token: str = ""
    jar_id: str = ""
    poll_interval: int = 60


@dataclass
class MediaConfig:
    path: str = "./media"
    default_duration: int = 5000
    rules: list[MediaRule] = field(default_factory=list)


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self._config_path = Path(config_path)
        self._raw: dict[str, Any] = {}
        self._server = ServerConfig()
        self._monobank = MonobankConfig()
        self._media = MediaConfig()

        self.reload()

    def reload(self) -> None:
        if not self._config_path.exists():
            return

        with open(self._config_path, "r", encoding="utf-8") as f:
            self._raw = yaml.safe_load(f) or {}

        self._parse_server()
        self._parse_monobank()
        self._parse_media()

    def _parse_server(self) -> None:
        server = self._raw.get("server", {})
        self._server = ServerConfig(
            port=server.get("port", 8080),
            host=server.get("host", "localhost"),
        )

    def _parse_monobank(self) -> None:
        monobank = self._raw.get("monobank", {})
        self._monobank = MonobankConfig(
            token=monobank.get("token", ""),
            jar_id=monobank.get("jar_id", ""),
            poll_interval=monobank.get("poll_interval", 60),
        )

    def _parse_media(self) -> None:
        media = self._raw.get("media", {})
        rules_raw = media.get("rules", [])
        rules = []

        for rule in rules_raw:
            rules.append(MediaRule(
                min_amount=rule.get("min", 0),
                max_amount=rule.get("max"),
                images=rule.get("images", []),
                sounds=rule.get("sounds", []),
            ))

        self._media = MediaConfig(
            path=media.get("path", "./media"),
            default_duration=media.get("default_duration", 5000),
            rules=rules,
        )

    # Server getters
    def get_port(self) -> int:
        return self._server.port

    def get_host(self) -> str:
        return self._server.host

    # Monobank getters
    def get_monobank_token(self) -> str:
        return self._monobank.token

    def get_jar_id(self) -> str:
        return self._monobank.jar_id

    def get_poll_interval(self) -> int:
        return self._monobank.poll_interval

    # Media getters
    def get_media_path(self) -> str:
        return self._media.path

    def get_default_duration(self) -> int:
        return self._media.default_duration

    def get_media_rules(self) -> list[MediaRule]:
        return self._media.rules
