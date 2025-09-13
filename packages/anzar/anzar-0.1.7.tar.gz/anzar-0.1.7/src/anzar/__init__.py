import dotenv

from anzar._auth.authenticator import AuthManager
from anzar._models.anzar_config import (
    AnzarConfig,
    Database,
    DatabaseType,
    EmailAndPassword,
)

from ._api.client import HttpClient
from ._api.http_interceptor import HttpInterceptor

_ = dotenv.load_dotenv()


default_config = AnzarConfig(
    api_url="http://localhost:3000",
    database=Database(
        connection_string="sqlite:memory:",
        db_type=DatabaseType.SQLite,
    ),
    emailAndPassword=EmailAndPassword(
        enable=True,
    ),
)


def AnzarAuth(config: AnzarConfig = default_config) -> AuthManager:
    return AuthManager(
        HttpClient(
            HttpInterceptor(),
        ),
        config,
    )


__all__ = ["AnzarAuth"]
