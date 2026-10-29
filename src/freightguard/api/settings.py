"""Small environment-based API configuration, separate from frozen model settings."""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

MODEL_VERSION = "v1"
FROZEN_THRESHOLD = 0.40
DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[3] / "data/processed/models/v1/pipeline.joblib"
)
DEFAULT_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


@dataclass(frozen=True)
class Settings:
    model_path: Path = DEFAULT_MODEL_PATH
    trust_local_model: bool = False
    model_sha256: str = ""
    cors_origins: tuple[str, ...] = DEFAULT_ORIGINS

    def __post_init__(self) -> None:
        for origin in self.cors_origins:
            try:
                parsed = urlsplit(origin)
                valid = (
                    parsed.scheme in ("http", "https")
                    and parsed.hostname
                    and not parsed.username
                    and not parsed.password
                    and not parsed.path
                    and not parsed.query
                    and not parsed.fragment
                    and "*" not in origin
                )
                _ = parsed.port
            except ValueError:
                valid = False
            if not valid:
                raise ValueError(
                    "CORS requires explicit HTTP(S) origins without paths."
                )

    @classmethod
    def from_env(cls) -> "Settings":
        trust = os.getenv("FREIGHTGUARD_TRUST_LOCAL_MODEL", "false").lower()
        if trust not in ("true", "false"):
            raise ValueError("FREIGHTGUARD_TRUST_LOCAL_MODEL must be true or false.")
        origins = os.getenv("FREIGHTGUARD_CORS_ORIGINS")
        return cls(
            model_path=Path(
                os.getenv("FREIGHTGUARD_MODEL_PATH", str(DEFAULT_MODEL_PATH))
            ),
            trust_local_model=trust == "true",
            model_sha256=os.getenv("FREIGHTGUARD_MODEL_SHA256", ""),
            cors_origins=DEFAULT_ORIGINS
            if origins is None
            else tuple(
                origin.strip() for origin in origins.split(",") if origin.strip()
            ),
        )
