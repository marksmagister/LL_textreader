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

    # --- accounts (docs/decisions/0021) ---

    # Anyone with a Google account may sign up, until there are max_users of
    # them. The cap is the whole growth control — deliberately a blunt number
    # rather than an invite system, because a number is one line and an invite
    # table is a table, a command and a landing page. Raise it when it binds.
    #
    # It bounds what strangers can cost: a lesson is 53.5 kB, so a hundred
    # readers is single-digit gigabytes even if they all read hard.
    #
    # "off" closes the door entirely without locking out the people already in.
    signup: str = "open"
    max_users: int = 100

    google_client_id: str = ""
    google_client_secret: str = ""
    # Must match a redirect URI registered on the OAuth client, exactly.
    google_redirect_uri: str = ""

    # How long a session survives without being used. Touched on every request,
    # so this is idle time and not a hard cap: reading daily never signs you out,
    # and a forgotten tab on a borrowed laptop expires on its own.
    session_days: int = 90

    # Cookies are Secure by default, which means they are ignored over plain
    # HTTP. That is right everywhere except localhost, where there is no TLS to
    # have — scripts/serve.sh turns it off for development only.
    cookie_secure: bool = True

    @property
    def language_list(self) -> list[str]:
        return [x.strip() for x in self.languages.split(",") if x.strip()]

    @property
    def google_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)


settings = Settings()
