"""第一层示例：用 HTTP 直接调用 LLM API。

这是最底层的调用方式。不依赖任何 LLM SDK，只用 requests 库发 HTTP 请求。
目的是让你看清「调用 LLM」的本质：就是发一个 HTTP POST 请求，带上消息，收到 JSON 响应。

运行方式（在项目根目录执行）：
    uv run python -m examples.example1_http

前提：已在 .env 中配置 API_BASE_URL、API_KEY、MODEL_NAME。
"""

import os
import sys
import json
from pathlib import Path

# 读取 .env（这里手动读，不用 python-dotenv，体现「最底层」）
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

# 导入 requests（如果项目没装，用 urllib；这里用 requests 更清晰）
try:
    import requests
except ImportError:
    print("本示例需要 requests 库。它是 langchain 的间接依赖，应该已安装。")
    sys.exit(1)


def chat_one_turn(user_message: str) -> str:
    """发送一条消息，返回 LLM 的回复（非流式，等全部生成完再返回）。

    本质就是：向 {API_BASE_URL}/chat/completions 发一个 POST 请求，
    请求体是 JSON，包含 model 和 messages；响应也是 JSON，含 LLM 的回复。
    """
    url = f"{API_BASE_URL}/chat/completions"

    # 请求头：认证（Bearer Token）
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    # 请求体：模型名 + 消息列表
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": user_message},
        ],
    }

    # 发送 POST 请求
    response = requests.post(url, headers=headers, json=payload, timeout=30)

    # 检查响应状态
    if response.status_code != 200:
        return f"请求失败，状态码 {response.status_code}: {response.text}"

    # 解析 JSON 响应
    data = response.json()

    # 提取 LLM 回复（在 choices[0].message.content）
    reply = data["choices"][0]["message"]["content"]

    # 提取 Token 用量（在 usage 字段）
    usage = data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    return reply, prompt_tokens, completion_tokens


def main():
    print("=" * 60)
    print("示例 1：用 HTTP 直接调用 LLM API（最底层）")
    print("=" * 60)
    print(f"API 地址: {API_BASE_URL}")
    print(f"模型:     {MODEL_NAME}")
    print(f"API Key:  {API_KEY[:8]}...（只显示前 8 位）")
    print()

    # 检查配置
    if not API_KEY or API_KEY == "your_api_key_here":
        print("错误：API_KEY 未配置，请在 .env 文件中填入真实的 API Key。")
        return

    # 第一轮对话
    print("-" * 60)
    user_input = "你好，请用一句话介绍你自己。"
    print(f"[你] {user_input}")

    reply, prompt_tokens, completion_tokens = chat_one_turn(user_input)
    print(f"[AI] {reply}")
    print(f"[Token] 输入 {prompt_tokens}，输出 {completion_tokens}")
    print()

    # 第二轮对话（注意：HTTP 方式下，LLM 不记得上一轮，需要自己维护历史）
    print("-" * 60)
    user_input2 = "我刚才问了什么？"
    print(f"[你] {user_input2}")

    # 如果想让 LLM 记得上一轮，需要把历史消息一起发过去
    # 这里为了演示「LLM 默认无记忆」，只发这一条
    reply2, pt2, ct2 = chat_one_turn(user_input2)
    print(f"[AI] {reply2}")
    print(f"[Token] 输入 {pt2}，输出 {ct2}")
    print()
    print("（注意：第二轮 LLM 答不出「你刚才问了什么」，因为它没有记忆。")
    print(" 这说明 LLM 本身是无状态的，多轮对话的记忆需要我们自己维护。）")


if __name__ == "__main__":
    main()
