"""配置加载与管理。

本模块负责读取并合并两个配置源：
    1. .env 文件：敏感信息（API Key、数据库密码），通过 pydantic-settings 自动读取。
    2. config.yaml 文件：业务配置（模型列表、存储类型等），通过 PyYAML 读取。

合并后的配置以 AppConfig 对象形式提供，全局通过 get_config() 访问（单例模式）。
"""

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ─────────────────────────────────────────────────────────────────────────────
# 敏感配置模型（从 .env 读取）
# ─────────────────────────────────────────────────────────────────────────────
class SecretConfig(BaseSettings):
    """敏感配置模型。

    自动从项目根目录的 .env 文件读取对应环境变量。
    pydantic-settings 会把大写的环境变量名映射到同名字段。
    """

    API_BASE_URL: str = "https://api.example.com/v1"
    API_KEY: str = "your_api_key_here"
    MODEL_NAME: str = "deepseek-chat"
    MYSQL_PASSWORD: str = ""

    # pydantic-settings v2 的配置方式（v2 用 model_config，不用 v1 的 class Config）
    model_config = SettingsConfigDict(
        env_file=".env",                # 指定 .env 文件路径（相对于运行目录）
        env_file_encoding="utf-8",      # 文件编码
        extra="ignore",                 # 忽略 .env 中未定义的变量
    )


# ─────────────────────────────────────────────────────────────────────────────
# 应用配置（合并敏感配置与业务配置）
# ─────────────────────────────────────────────────────────────────────────────
class AppConfig:
    """应用配置（单例）。

    封装敏感配置（SecretConfig）与业务配置（config.yaml 字典）。
    通过 get_config() 全局访问。
    """

    def __init__(self) -> None:
        # 1. 加载敏感配置（自动读 .env）
        self.secret = SecretConfig()

        # 2. 加载业务配置（读 config.yaml）
        self._yaml_config: dict[str, Any] = self._load_yaml("config.yaml")

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """读取 YAML 配置文件，返回字典。文件不存在时返回空字典。"""
        path = Path(filename)
        if not path.exists():
            print(f"[配置警告] 配置文件 {filename} 不存在，使用空配置")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    # ── 业务配置访问方法 ──────────────────────────────────────────────────

    @property
    def current_step(self) -> str:
        """当前开发步骤（横幅显示用，方案 B：从配置读取）。"""
        return self._yaml_config.get("app", {}).get("current_step", "开发中")

    @property
    def storage_type(self) -> str:
        """存储后端类型（sqlite / mysql / file）。"""
        return self._yaml_config.get("storage", {}).get("type", "sqlite")

    @property
    def default_model(self) -> str:
        """默认模型名。"""
        return self._yaml_config.get("models", {}).get("default", "deepseek-chat")

    @property
    def available_models(self) -> list[dict[str, str]]:
        """可选模型列表。"""
        return self._yaml_config.get("models", {}).get("available", [])

    @property
    def temperature(self) -> float:
        """生成温度（创造性程度，范围 0 到 2。0=最确定，2=最随机，本项目默认 0.7）。"""
        return self._yaml_config.get("models", {}).get("temperature", 0.7)

    @property
    def max_tokens(self) -> int:
        """单次回复最大 token 数。"""
        return self._yaml_config.get("models", {}).get("max_tokens", 2048)

    @property
    def llm_timeout(self) -> int:
        """LLM 调用超时（秒）。"""
        return self._yaml_config.get("llm", {}).get("timeout", 30)

    @property
    def llm_max_retries(self) -> int:
        """LLM 最大重试次数。"""
        return self._yaml_config.get("llm", {}).get("max_retries", 3)

    @property
    def title_max_length(self) -> int:
        """会话标题自动截断长度。"""
        return self._yaml_config.get("session", {}).get("title_max_length", 30)

    def get(self, *keys: str, default: Any = None) -> Any:
        """按层级键路径读取业务配置。

        示例：get_config().get("storage", "sqlite", "path")
        等价于读取 config.yaml 中 storage.sqlite.path 的值。
        """
        value: Any = self._yaml_config
        for key in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(key)
            if value is None:
                return default
        return value


# ─────────────────────────────────────────────────────────────────────────────
# 全局单例访问
# ─────────────────────────────────────────────────────────────────────────────
# 模块级变量，第一次调用 get_config() 时创建实例，之后复用。
_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例（单例模式）。

    第一次调用时读取配置文件并创建实例，之后所有调用返回同一实例。
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance
