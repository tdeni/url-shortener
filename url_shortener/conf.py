from pydantic import BaseSettings


class Config(BaseSettings):
    """Project config."""

    secret_key: str

    database: str
    db_user: str
    db_password: str
    db_host: str
    db_port: int = 3306

    redis_host: str
    redis_port: int = 6379

    debug: bool = False

    cleanup_interval: float = 15
    mysql_max_age: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def database_uri(self) -> str:
        return f"mysql+aiomysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.database}"

    @property
    def database_uri_sync(self) -> str:
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.database}"


config = Config()
