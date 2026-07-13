"""第二层示例：用 OpenAI 官方 SDK 调用 LLM。

这一层比 HTTP 封装更高级。OpenAI SDK 把「构造请求、发送、解析响应」封装成函数调用，
你不需要手写 HTTP 请求，只需调用 client.chat.completions.create()。

重要：OpenAI SDK 兼容所有「OpenAI 格式」的 API（DeepSeek、通义千问等），
只要把 base_url 换成对应服务的地址即可。

运行方式（在项目根目录执行）：
    uv run python -m examples.example2_openai_sdk

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

from openai import OpenAI


def main():
    print("=" * 60)
    print("示例 2：用 OpenAI SDK 调用 LLM（第二层封装）")
    print("=" * 60)
    print(f"API 地址: {API_BASE_URL}")
    print(f"模型:     {MODEL_NAME}")
    print(f"API Key:  {API_KEY[:8]}...（只显示前 8 位）")
    print()

    if not API_KEY or API_KEY == "your_api_key_here":
        print("错误：API_KEY 未配置，请在 .env 文件中填入真实的 API Key。")
        return

    # 创建客户端（把 HTTP 的 headers、base_url 等封装了）
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE_URL,
    )

    # 第一轮：单轮对话（对比示例 1，代码简洁很多）
    print("-" * 60)
    user_input = "你好，请用一句话介绍你自己。"
    print(f"[你] {user_input}")

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": user_input}],
    )
    print(f"[AI] {response.choices[0].message.content}")
    print(f"[Token] 输入 {response.usage.prompt_tokens}，输出 {response.usage.completion_tokens}")
    print()

    # 第二轮：多轮对话（自己维护消息历史）
    print("-" * 60)
    print("多轮对话（手动维护消息历史）：")
    messages = [
        {"role": "user", "content": "你好，请用一句话介绍你自己。"},
    ]
    response1 = client.chat.completions.create(model=MODEL_NAME, messages=messages)
    ai_reply1 = response1.choices[0].message.content
    print(f"[你] {messages[0]['content']}")
    print(f"[AI] {ai_reply1}")

    # 把 AI 的回复加入历史，再发第二轮
    messages.append({"role": "assistant", "content": ai_reply1})
    messages.append({"role": "user", "content": "我刚才问了什么？"})
    print(f"[你] 我刚才问了什么？")

    response2 = client.chat.completions.create(model=MODEL_NAME, messages=messages)
    print(f"[AI] {response2.choices[0].message.content}")
    print()
    print("（这次 LLM 答出了「你问了让我介绍自己」，因为我们手动维护了消息历史。）")


if __name__ == "__main__":
    main()
