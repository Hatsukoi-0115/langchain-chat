"""配置加载与管理。

本模块负责读取并合并两个配置源：
    1. .env 文件：各服务商的 API Key、默认模型名，通过 pydantic-settings 自动读取。
    2. config.yaml 文件：服务商分组配置、生成参数、存储配置等。

Step 10 重构：从单一服务商改为多服务商分组（providers 结构）。
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv


def _load_env():
    """加载 .env 文件到环境变量。"""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path, override=True)


_load_env()


def get_config_value(env_key: str, default: str = "") -> str:
    """从环境变量读取配置值。"""
    return os.environ.get(env_key, default)


class AppConfig:
    """应用配置（单例）。

    封装 .env（敏感配置）与 config.yaml（业务配置）。
    通过 get_config() 全局访问。
    """

    def __init__(self) -> None:
        # 加载业务配置（读 config.yaml）
        self._yaml_config: dict[str, Any] = self._load_yaml("config.yaml")

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """读取 YAML 配置文件，返回字典。"""
        path = Path(filename)
        if not path.exists():
            print(f"[配置警告] 配置文件 {filename} 不存在，使用空配置")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    # ── 敏感配置（从 .env 读取）─────────────────────────────────────────

    @property
    def default_model(self) -> str:
        """默认模型名（从 .env 的 DEFAULT_MODEL 读取）。"""
        return get_config_value("DEFAULT_MODEL", "qwen3.6-flash")

    def get_api_key(self, env_key: str) -> str:
        """按变量名从 .env 读取 API Key。"""
        return get_config_value(env_key, "")

    # ── 服务商配置（从 config.yaml 的 providers 读取）────────────────────

    @property
    def providers(self) -> list[dict]:
        """所有服务商配置列表。"""
        return self._yaml_config.get("providers", [])

    def get_all_models(self) -> list[dict[str, str]]:
        """获取所有服务商下的全部模型（扁平化列表）。

        返回格式: [{"name": "显示名", "value": "模型标识", "provider": "服务商名"}, ...]
        """
        result = []
        for provider in self.providers:
            for model in provider.get("models", []):
                result.append({
                    "name": model.get("name", model.get("value", "")),
                    "value": model.get("value", ""),
                    "provider": provider.get("name", ""),
                })
        return result

    def find_provider_by_model(self, model_value: str) -> Optional[dict]:
        """按模型标识查找所属服务商配置。

        参数：
            model_value: 模型标识（如 qwen3.6-flash）
        返回：
            服务商配置字典，或 None（模型不存在）
        """
        for provider in self.providers:
            for model in provider.get("models", []):
                if model.get("value") == model_value:
                    return provider
        return None

    # ── 生成参数（从 config.yaml 顶层读取）──────────────────────────────

    @property
    def temperature(self) -> float:
        """生成温度（范围 0 到 2。0=最确定，2=最随机，本项目默认 0.7）。"""
        return self._yaml_config.get("temperature", 0.7)

    @property
    def max_tokens(self) -> int:
        """单次回复最大 token 数。"""
        return self._yaml_config.get("max_tokens", 2048)

    # ── 其他配置 ────────────────────────────────────────────────────────

    @property
    def current_step(self) -> str:
        """当前开发步骤（横幅显示用）。"""
        return self._yaml_config.get("app", {}).get("current_step", "开发中")

    @property
    def storage_type(self) -> str:
        """存储后端类型。"""
        return self._yaml_config.get("storage", {}).get("type", "sqlite")

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
        """按层级键路径读取业务配置。"""
        value: Any = self._yaml_config
        for key in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(key)
            if value is None:
                return default
        return value


# ── 全局单例 ────────────────────────────────────────────────────────────
_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例（单例）。"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance
