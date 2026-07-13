"""langchain-chat 程序总入口。

Step 2 阶段：加载配置，启动 TUI 主界面。
运行方式：uv run python src/main.py
"""

import asyncio
import sys
from pathlib import Path

# 将 src 目录加入模块搜索路径，确保 import 链路在任意运行方式下都工作。
# Path(__file__).resolve().parent 是 main.py 所在目录（即 src）。
sys.path.insert(0, str(Path(__file__).resolve().parent))


async def async_main() -> None:
    """异步主函数。

    后续步骤会在此函数中按顺序执行：
        1. 加载配置（config_manager）
        2. 初始化存储后端（Step 3 起）
        3. 启动 TUI 主循环
    当前 Step 2 阶段：加载配置 + 启动 TUI。
    """
    # 1. 加载配置（触发单例创建，读取 .env 与 config.yaml）
    from core.config_manager import get_config

    config = get_config()
    # 暂时只用打印验证配置加载成功，后续步骤会用 config 初始化存储等
    print(f"[启动] 存储后端: {config.storage_type}，默认模型: {config.default_model}")

    # 2. 启动 TUI 主循环
    from ui.tui.app import TUIApp

    app = TUIApp()
    await app.run()


def main() -> None:
    """程序主函数（同步入口，内部启动异步事件循环）。"""
    asyncio.run(async_main())


# 入口守护：只有直接运行本文件时才执行，被 import 时不执行。
if __name__ == "__main__":
    main()
