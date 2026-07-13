"""langchain-chat 程序总入口。

Step 4 阶段：加载配置、初始化存储后端、启动 TUI 主界面。
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

    启动流程（Step 4 起）：
        1. 加载配置（config_manager）
        2. 初始化存储后端（根据 config.storage_type 创建并 initialize）
        3. 启动 TUI 主循环（把存储后端注入 TUIApp）
    """
    # 1. 加载配置（触发单例创建，读取 .env 与 config.yaml）
    from core.config_manager import get_config

    config = get_config()
    print(f"[启动] 存储后端: {config.storage_type}，默认模型: {config.default_model}")

    # 2. 初始化存储后端
    from storage.factory import StorageFactory

    backend = StorageFactory.create(config.storage_type)
    await backend.initialize()
    print(f"[启动] 存储后端已就绪: {type(backend).__name__}")

    # 3. 启动 TUI 主循环（注入存储后端）
    from ui.tui.app import TUIApp

    try:
        app = TUIApp(backend=backend)
        await app.run()
    finally:
        # 无论正常退出还是异常，都关闭存储后端连接
        await backend.close()
        print("[启动] 存储后端已关闭")


def main() -> None:
    """程序主函数（同步入口，内部启动异步事件循环）。"""
    asyncio.run(async_main())


# 入口守护：只有直接运行本文件时才执行，被 import 时不执行。
if __name__ == "__main__":
    main()
