import json
from pathlib import Path

from attrs import define


@define
class Settings:
    conn_str: str
    cities_data: str
    countries_data: str


def load_settings() -> Settings:
    with open(Path().resolve() / "settings/settings.json", "r") as f:
        s = json.load(f)
        conn_str = f"postgresql+psycopg2://{s['user']}:{s['password']}@{s['hostname']}/{s['database_name']}"
        return Settings(conn_str=conn_str, cities_data=s['cities_data'], countries_data=s['countries_data'])
