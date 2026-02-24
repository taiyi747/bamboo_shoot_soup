"""应用配置：从环境变量加载 API/数据库/LLM 运行参数。"""

import json
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """集中管理后端运行时配置。"""

    app_name: str = "Bamboo Shoot Soup Backend"
    debug: bool = False
    database_url: str = "sqlite:///./data/bss.db"
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ]
    )
    # 生产生成链路依赖 LLM，因此这三项会在启动时做必填校验。
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    model_name: str | None = None
    openai_timeout_seconds: float = Field(default=90.0, gt=0)
    openai_max_retries: int = Field(default=2, ge=0)

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_allow_origins(cls, value: object) -> object:
        """兼容 JSON 数组和逗号分隔字符串两种配置格式。"""
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in text.split(",") if item.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def validate_llm_settings(self) -> None:
        """在服务启动前校验 LLM 必填环境变量。"""
        missing: list[str] = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.openai_base_url:
            missing.append("OPENAI_BASE_URL")
        if not self.model_name:
            missing.append("MODEL_NAME")
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing required LLM environment variables: {joined}")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回缓存后的 Settings，避免重复解析环境变量。"""
    return Settings()
