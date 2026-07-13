"""对话视图（骨架）。

本步骤只占位，真实对话功能（流式输出、Token 统计、多轮交互）在 Step 7 实现。
对应需求文档 A1 至 A5（核心对话功能）。
"""

from ui.tui import widgets


async def start_chat() -> None:
    """启动对话（桩）。Step 7 实现真实的流式多轮对话。"""
    widgets.print_info("对话功能将在 Step 7 实现（核心里程碑）")
    widgets.print_divider()
