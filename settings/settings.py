import json
from pathlib import Path

from attrs import define


@define
class Settings:
    conn_str: str


def load_settings() -> Settings:
    with open(Path().resolve() / "settings/settings.json", "r") as f:
        return Settings(**json.load(f))
