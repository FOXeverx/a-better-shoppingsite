import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 3306
    username: str = "root"
    password: str = ""
    name: str = "shopping_site"

    @property
    def url(self) -> str:
        return f"mysql+mysqlconnector://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class AppConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    frontend_url: str = "http://localhost:3000"


class JWTConfig(BaseModel):
    secret: str = "your-secret-key"
    algorithm: str = "HS256"
    expire_minutes: int = 1440


class SecurityConfig(BaseModel):
    ip_limit_per_minute: int = 60
    max_login_attempts: int = 5
    block_duration_minutes: int = 30


class SMTPConfig(BaseModel):
    host: str = "smtp.gmail.com"
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True


class Config(BaseModel):
    database: DatabaseConfig = DatabaseConfig()
    app: AppConfig = AppConfig()
    jwt: JWTConfig = JWTConfig()
    security: SecurityConfig = SecurityConfig()
    smtp: SMTPConfig = SMTPConfig()


config: Optional[Config] = None


def load_config(config_path: str = "config.yaml") -> Config:
    global config
    path = Path(config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        config = Config(
            database=DatabaseConfig(**data.get("database", {})),
            app=AppConfig(**data.get("app", {})),
            jwt=JWTConfig(**data.get("jwt", {})),
            security=SecurityConfig(**data.get("security", {})),
            smtp=SMTPConfig(**data.get("smtp", {}))
        )
    else:
        config = Config()
    return config


def get_config() -> Config:
    global config
    if config is None:
        return load_config()
    return config