from pathlib import Path
import datetime as dt
from dataclasses import dataclass, field


@dataclass
class FileMeta:
    path: str | Path
    date: dt.datetime
    country: str | None = field(default='')
    city: str | None = field(default='')