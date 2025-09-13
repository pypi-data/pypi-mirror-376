from enum import Enum
from pydantic import BaseModel


class DatabaseType(str, Enum):
    SQLite = "SQLite"
    PostgreSQL = "PostgreSQL"
    MongoDB = "MongoDB"


class Database(BaseModel):
    connection_string: str
    db_type: DatabaseType


class EmailAndPassword(BaseModel):
    enable: bool


class AnzarConfig(BaseModel):
    api_url: str
    database: Database
    emailAndPassword: EmailAndPassword
