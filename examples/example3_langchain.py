"""第三层示例：用 LangChain ChatOpenAI 调用 LLM（项目最终选用）。

这一层在 OpenAI SDK 之上再加抽象。LangChain 提供了：
    - ChatOpenAI：封装了 OpenAI SDK，支持流式、重试等。
    - 消息类型：HumanMessage、AIMessage、SystemMessage，比 dict 更规范。
    - 后续可接 Memory、Chain、Agent 等高级组件。

本项目选用 LangChain，因为它为多轮对话、流式输出、记忆管理提供了完整支持。

运行方式（在项目根目录执行）：
    uv run python -m examples.example3_langchain

前提：已在 .env 中配置 API_BASE_URL、API_KEY、MODEL_NAME。
"""

import os
from pathlib import Path

# 读取 .env
env_path = Path(".env")
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

API_BASE_URL = os.environ.get("API_BASE_URL", "")
API_KEY = os.environ.get("API_KEY", "")
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-chat")

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI


def main():
    print("=" * 60)
    print("示例 3：用 LangChain ChatOpenAI 调用 LLM（第三层，项目选用）")
    print("=" * 60)
    print(f"API 地址: {API_BASE_URL}")
    print(f"模型:     {MODEL_NAME}")
    print(f"API Key:  {API_KEY[:8]}...（只显示前 8 位）")
    print()

    if not API_KEY or API_KEY == "your_api_key_here":
        print("错误：API_KEY 未配置，请在 .env 文件中填入真实的 API Key。")
        return

    # 创建 ChatOpenAI（封装了 OpenAI SDK，支持流式、重试、超时等）
    llm = ChatOpenAI(
        model=MODEL_NAME,
        api_key=API_KEY,
        base_url=API_BASE_URL,
        temperature=0.7,
        max_tokens=512,
        timeout=30,
        max_retries=2,
    )

    # 第一轮：用 HumanMessage 构造消息（比 dict 更规范）
    print("-" * 60)
    print("单轮对话：")
    user_msg = HumanMessage(content="你好，请用一句话介绍你自己。")
    print(f"[你] {user_msg.content}")

    ai_msg = llm.invoke([user_msg])
    print(f"[AI] {ai_msg.content}")
    if ai_msg.usage_metadata:
        um = ai_msg.usage_metadata
        print(f"[Token] 输入 {um.get('input_tokens', '?')}，输出 {um.get('output_tokens', '?')}")
    print()

    # 第二轮：多轮对话（用消息列表维护历史，和 SDK 类似但消息类型更规范）
    print("-" * 60)
    print("多轮对话（用消息列表维护历史）：")
    history = [user_msg, ai_msg]
    user_msg2 = HumanMessage(content="我刚才问了什么？")
    history.append(user_msg2)
    print(f"[你] {user_msg2.content}")

    ai_msg2 = llm.invoke(history)
    print(f"[AI] {ai_msg2.content}")
    print()

    # 第三轮：流式输出（逐字返回，这是 LangChain 的强大之处）
    print("-" * 60)
    print("流式输出（逐字返回）：")
    print("[你] 请数 1 到 5")
    print("[AI] ", end="", flush=True)
    for chunk in llm.stream([HumanMessage(content="请数 1 到 5")]):
        print(chunk.content, end="", flush=True)
    print()
    print()
    print("（流式输出：LLM 一边生成一边返回，不需要等全部生成完。体验更好。）")


if __name__ == "__main__":
    main()
