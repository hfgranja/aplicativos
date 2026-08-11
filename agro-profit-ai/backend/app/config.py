import os


def _bool_env(key: str, default: str = "false") -> bool:
    return os.getenv(key, default).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    # Non-commercial-licensed providers (e.g. Open-Meteo public tier) must be
    # explicitly opted into — never enabled by default in a commercial deploy.
    ALLOW_NON_COMMERCIAL_PROVIDERS: bool = _bool_env("ALLOW_NON_COMMERCIAL_PROVIDERS", "true")

    # Optional providers requiring paid/registered credentials — disabled
    # unless a key/config is present (spec 4.6-4.8, 4.13).
    ENABLE_EARTH_ENGINE: bool = _bool_env("ENABLE_EARTH_ENGINE", "false")
    COPERNICUS_CLIENT_ID: str | None = os.getenv("COPERNICUS_CLIENT_ID")
    COPERNICUS_CLIENT_SECRET: str | None = os.getenv("COPERNICUS_CLIENT_SECRET")
    OPENWEATHER_API_KEY: str | None = os.getenv("OPENWEATHER_API_KEY")
    TOMORROW_API_KEY: str | None = os.getenv("TOMORROW_API_KEY")
    PLANET_API_KEY: str | None = os.getenv("PLANET_API_KEY")
    CDS_API_KEY: str | None = os.getenv("CDS_API_KEY")  # Copernicus Climate Data Store (ERA5-Land)

    DEFAULT_GRID_RESOLUTION_M: int = int(os.getenv("DEFAULT_GRID_RESOLUTION_M", "30"))


settings = Settings()
