"""对话引擎（核心模块）。

封装 LLM 的调用逻辑：多轮对话、流式输出、超时重试、Token 统计、模型切换。
对应需求文档 A1 至 A5（核心对话功能）、A5（会话内模型切换）、G1（超时与重试）。

Step 10 重构：支持多服务商模型切换（switch_model）。
"""

import os
from typing import AsyncIterator, Optional

from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI

from core.config_manager import AppConfig


class ChatEngine:
    """对话引擎。

    封装 LLM 调用，提供同步调用、异步流式和模型切换。
    """

    def __init__(self, config: AppConfig):
        """初始化对话引擎，使用默认模型。"""
        self.config = config
        self.current_model: str = config.default_model
        self.llm: ChatOpenAI = self._create_llm(self.current_model)

    def _create_llm(self, model_value: str) -> ChatOpenAI:
        """按模型标识创建 ChatOpenAI 实例。

        自动查找模型所属服务商，用对应的 base_url 和 API Key。
        """
        provider = self.config.find_provider_by_model(model_value)
        if provider is None:
            raise ValueError(f"模型 '{model_value}' 不在可选列表中")

        api_key = self.config.get_api_key(provider["api_key_env"])
        if not api_key:
            raise ValueError(f"服务商 '{provider['name']}' 的 API Key 未配置（请检查 .env 的 {provider['api_key_env']}）")

        return ChatOpenAI(
            model=model_value,
            api_key=api_key,
            base_url=provider["base_url"],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.llm_timeout,
            max_retries=self.config.llm_max_retries,
            streaming=True,
        )

    def switch_model(self, model_value: str) -> None:
        """切换模型（A5 会话内模型切换）。

        自动查找新模型所属服务商，用对应的 base_url 和 Key 重建 LLM 客户端。
        切换后历史上下文保留（消息列表由调用方维护，不受影响）。

        参数：
            model_value: 新模型标识（如 deepseek-v4-pro）

        异常：
            ValueError: 模型不在可选列表中 或 API Key 未配置
        """
        # 先验证模型存在（_create_llm 内部会校验）
        self.llm = self._create_llm(model_value)
        self.current_model = model_value

    def chat(self, messages: list[BaseMessage]) -> tuple[str, dict]:
        """同步对话（非流式）。"""
        response: AIMessage = self.llm.invoke(messages)
        reply = response.content
        usage = self._extract_usage(response)
        return reply, usage

    async def astream(
        self, messages: list[BaseMessage]
    ) -> AsyncIterator[tuple[str, Optional[dict]]]:
        """异步流式对话。"""
        final_usage = None
        async for chunk in self.llm.astream(messages):
            text = chunk.content
            if text:
                yield text, None
            usage = self._extract_usage(chunk)
            if usage is not None:
                final_usage = usage
        yield "", final_usage

    def _extract_usage(self, message: BaseMessage) -> Optional[dict]:
        """从 LangChain 响应中提取 token 用量。"""
        usage_meta = getattr(message, "usage_metadata", None)
        if usage_meta is None:
            return None
        return {
            "prompt_tokens": usage_meta.get("input_tokens", 0),
            "completion_tokens": usage_meta.get("output_tokens", 0),
            "total_tokens": usage_meta.get("total_tokens", 0),
        }

    async def close(self) -> None:
        """关闭引擎（预留接口）。"""
        pass
