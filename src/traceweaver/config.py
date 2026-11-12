"""Small, explicit configuration shared by the CLI and HTTP application."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database: Path = field(
        default_factory=lambda: Path(os.getenv("TRACEWEAVER_DATABASE", "data/traceweaver.rl"))
    )

    def __post_init__(self) -> None:
        path = Path(self.database)
        if path.suffix.lower() != ".rl":
            raise ValueError("TRACEWEAVER_DATABASE must name a persistent .rl file")
        object.__setattr__(self, "database", path)
