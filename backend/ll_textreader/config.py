from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LL_TEXTREADER_", env_file=".env", extra="ignore")

    db_path: Path = REPO_ROOT / "data" / "ll_textreader.db"
    data_dir: Path = REPO_ROOT / "data"
    host: str = "127.0.0.1"
    port: int = 8000
    languages: str = "fr"

    # Set this and every request needs it. Empty means no password, which is fine
    # on localhost and never fine behind a tunnel — scripts/serve.sh enforces that.
    password: str = ""
    username: str = "read"

    @property
    def language_list(self) -> list[str]:
        return [x.strip() for x in self.languages.split(",") if x.strip()]


settings = Settings()
