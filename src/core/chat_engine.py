"""对话引擎（核心模块）。

封装 LLM 的调用逻辑：多轮对话、流式输出、超时重试、Token 统计。
对应需求文档 A1 至 A5（核心对话功能）与 G1（超时与重试）。

设计说明：
    - ChatEngine 通过依赖注入接收 SecretConfig（含 API 配置），不自己读 .env。
    - 用 LangChain 的 ChatOpenAI 作为 LLM 客户端（OpenAI 兼容格式）。
    - 多轮对话的记忆由调用方维护（传入消息历史），ChatEngine 不持有状态。
      这样一个 ChatEngine 实例可服务多个会话，避免状态串扰。
    - 流式输出用 astream（异步），逐 chunk 返回，调用方实时渲染。
    - 超时与重试由 ChatOpenAI 内置（max_retries、timeout 参数）。
    - Token 用量从响应的 usage_metadata 提取。

使用方式：
    engine = ChatEngine(config)
    async for chunk in engine.astream(messages):
        print(chunk.content, end="")
"""

from typing import AsyncIterator, Optional

from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI

from core.config_manager import AppConfig


class ChatEngine:
    """对话引擎。

    封装 LLM 调用，提供同步调用和异步流式两种方式。
    """

    def __init__(self, config: AppConfig):
        """初始化对话引擎。

        参数：
            config: 应用配置（从中读取 API 地址、Key、模型名、超时、重试等）
        """
        self.config = config

        # 创建 ChatOpenAI 实例
        self.llm = ChatOpenAI(
            model=config.secret.MODEL_NAME,
            api_key=config.secret.API_KEY,
            base_url=config.secret.API_BASE_URL,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.llm_timeout,
            max_retries=config.llm_max_retries,
            streaming=True,
        )

    def chat(self, messages: list[BaseMessage]) -> tuple[str, dict]:
        """同步对话（非流式）。等待 LLM 完整生成后返回。

        参数：
            messages: 消息历史（LangChain 的 BaseMessage 列表）
        返回：
            (回复文本, token 用量字典)
            token 字典含 keys: prompt_tokens, completion_tokens, total_tokens
        """
        response: AIMessage = self.llm.invoke(messages)

        reply = response.content
        usage = self._extract_usage(response)
        return reply, usage

    async def astream(
        self, messages: list[BaseMessage]
    ) -> AsyncIterator[tuple[str, Optional[dict]]]:
        """异步流式对话。逐 chunk 返回，调用方实时渲染。

        参数：
            messages: 消息历史
        生成（yield）：
            每个 chunk 是一个元组 (text, usage)。
            中间的 chunk：text 是这一段的文字，usage 为 None。
            最后的 chunk：text 为空字符串，usage 含本次调用的 token 统计。
        """
        accumulated_text = ""
        final_usage = None

        async for chunk in self.llm.astream(messages):
            text = chunk.content
            if text:
                accumulated_text += text
                yield text, None

            # 提取 token 用量（通常在最后一个 chunk）
            usage = self._extract_usage(chunk)
            if usage is not None:
                final_usage = usage

        # 最后 yield 一个带 usage 的 chunk（text 为空）
        yield "", final_usage

    def _extract_usage(self, message: BaseMessage) -> Optional[dict]:
        """从 LangChain 响应中提取 token 用量。

        LangChain 把 OpenAI 的 usage 封装到 usage_metadata 字段。
        返回 None 表示该消息没有用量信息（流式中间 chunk 通常没有）。
        """
        usage_meta = getattr(message, "usage_metadata", None)
        if usage_meta is None:
            return None

        return {
            "prompt_tokens": usage_meta.get("input_tokens", 0),
            "completion_tokens": usage_meta.get("output_tokens", 0),
            "total_tokens": usage_meta.get("total_tokens", 0),
        }

    async def close(self) -> None:
        """关闭引擎（当前 ChatOpenAI 无需显式关闭，预留接口）。"""
        pass
