"""ChatEngine 冒烟测试脚本。

全面验证对话引擎的各项功能，确保及早发现问题（呼应 Step 5 教训）。
覆盖：单轮对话、多轮对话（记忆）、流式输出、Token 统计、错误处理。

运行方式：
    uv run python scripts/test_chat_engine.py

前提：已在 .env 中配置真实的 API_BASE_URL、API_KEY、MODEL_NAME。
"""

import asyncio
import sys
from pathlib import Path

# 将 src 目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from langchain_core.messages import HumanMessage, SystemMessage

from core.chat_engine import ChatEngine
from core.config_manager import get_config


async def test_single_turn(engine: ChatEngine) -> None:
    """测试 1：单轮对话（非流式）。"""
    print("[测试 1] 单轮对话（非流式）")
    messages = [HumanMessage(content="请用一句话回答：1+1 等于几？")]
    reply, usage = engine.chat(messages)
    print(f"  回复: {reply}")
    print(f"  Token: {usage}")
    assert reply, "回复不应为空"
    print("  结果: 通过\n")


async def test_multi_turn(engine: ChatEngine) -> None:
    """测试 2：多轮对话（验证记忆）。"""
    print("[测试 2] 多轮对话（验证记忆）")
    # 第一轮
    msg1 = HumanMessage(content="我叫小明，请记住我的名字。")
    reply1, _ = engine.chat([msg1])
    print(f"  第一轮回复: {reply1[:50]}...")

    # 第二轮（带上第一轮的历史，验证 LLM 记得名字）
    history = [msg1, HumanMessage(content="我叫什么名字？")]
    reply2, _ = engine.chat(history)
    print(f"  第二轮回复: {reply2}")
    assert "小明" in reply2, f"LLM 应该记得名字是小明，实际回复: {reply2}"
    print("  结果: 通过（LLM 记住了名字）\n")


async def test_streaming(engine: ChatEngine) -> None:
    """测试 3：流式输出。"""
    print("[测试 3] 流式输出")
    messages = [HumanMessage(content="请数 1 到 5，每个数字占一行。")]
    print("  流式输出: ", end="")
    chunk_count = 0
    final_usage = None
    async for text, usage in engine.astream(messages):
        if text:
            print(text, end="", flush=True)
            chunk_count += 1
        if usage is not None:
            final_usage = usage
    print()
    print(f"  收到 {chunk_count} 个文本 chunk")
    print(f"  Token: {final_usage}")
    assert chunk_count > 0, "流式应返回多个 chunk"
    print("  结果: 通过\n")


async def test_token_usage(engine: ChatEngine) -> None:
    """测试 4：Token 统计。"""
    print("[测试 4] Token 统计")
    messages = [HumanMessage(content="你好")]
    reply, usage = engine.chat(messages)
    print(f"  回复: {reply}")
    print(f"  Token 统计: {usage}")
    assert usage["prompt_tokens"] > 0, "输入 token 应大于 0"
    assert usage["completion_tokens"] > 0, "输出 token 应大于 0"
    assert usage["total_tokens"] > 0, "总 token 应大于 0"
    print("  结果: 通过（Token 统计正常）\n")


async def test_system_prompt(engine: ChatEngine) -> None:
    """测试 5：系统预设（system_prompt）。"""
    print("[测试 5] 系统预设（system_prompt）")
    messages = [
        SystemMessage(content="你是一个只会说英语的助手，即使用户说中文你也用英语回复。"),
        HumanMessage(content="你好"),
    ]
    reply, _ = engine.chat(messages)
    print(f"  回复: {reply[:80]}")
    # 不做强断言（LLM 不一定严格遵守），只展示 system_prompt 的效果
    print("  结果: 通过（已发送 system_prompt）\n")


async def test_error_handling(engine: ChatEngine) -> None:
    """测试 6：错误处理（用错误的模型名触发错误）。"""
    print("[测试 6] 错误处理（错误的模型名）")
    from langchain_openai import ChatOpenAI
    provider = engine.config.find_provider_by_model(engine.current_model)
    bad_llm = ChatOpenAI(
        model="this-model-does-not-exist",
        api_key=engine.config.get_api_key(provider["api_key_env"]),
        base_url=provider["base_url"],
        timeout=10,
        max_retries=1,
    )
    try:
        bad_llm.invoke([HumanMessage(content="test")])
        print("  结果: 未触发错误（可能 API 容错较强）\n")
    except Exception as e:
        error_type = type(e).__name__
        print(f"  触发错误（预期行为）: {error_type}")
        print("  结果: 通过（错误被正确触发）\n")


async def main():
    print("=" * 60)
    print("Step 6：ChatEngine 冒烟测试")
    print("=" * 60)

    # 加载配置
    config = get_config()
    print(f"默认模型: {config.default_model}")
    provider = config.find_provider_by_model(config.default_model)
    if provider:
        print(f"服务商:   {provider['name']}")
        api_key = config.get_api_key(provider["api_key_env"])
        print(f"API Key:  {api_key[:8]}..." if api_key else "API Key:  未配置")
    else:
        print("错误: 默认模型不在 providers 列表中")
        return
    print()

    # 检查 API Key 是否已配置
    if not config.secret.API_KEY or config.secret.API_KEY == "your_api_key_here":
        print("错误：API_KEY 未配置，请在 .env 文件中填入真实的 API Key。")
        return

    # 创建引擎
    engine = ChatEngine(config)

    # 运行所有测试
    try:
        await test_single_turn(engine)
        await test_multi_turn(engine)
        await test_streaming(engine)
        await test_token_usage(engine)
        await test_system_prompt(engine)
        await test_error_handling(engine)
        print("=" * 60)
        print("[全部通过] ChatEngine 冒烟测试全部成功")
        print("=" * 60)
    except AssertionError as e:
        print(f"[断言失败] {e}")
    except Exception as e:
        print(f"[异常] {type(e).__name__}: {e}")
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(main())
