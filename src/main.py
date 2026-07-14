"""langchain-chat 程序总入口。

Step 5 阶段：加载配置、初始化存储后端、导入内置预设、启动 TUI 主界面。
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

    启动流程（Step 5 起）：
        1. 加载配置（config_manager）
        2. 初始化存储后端（根据 config.storage_type 创建并 initialize）
        3. 导入系统内置预设（从 config/presets.yaml，幂等）
        4. 启动 TUI 主循环（把存储后端注入 TUIApp）
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

    # 3. 导入系统内置预设（幂等，已存在的不会重复导入）
    from core.preset_manager import PresetManager

    # 导入预设并不是保存在 PresetManager 或 backend 实例中，而是 backend 指向的数据库
    preset_manager = PresetManager(backend)
    imported = await preset_manager.load_builtin_presets()
    if imported > 0:
        print(f"[启动] 导入了 {imported} 个系统内置预设")

    # 4. 创建对话引擎
    from core.chat_engine import ChatEngine

    engine = ChatEngine(config)
    print(f"[启动] 对话引擎已就绪: {config.secret.MODEL_NAME}")

    # 5. 启动 TUI 主循环（注入存储后端、引擎、配置）
    from ui.tui.app import TUIApp

    try:
        app = TUIApp(backend=backend, engine=engine, config=config)
        await app.run()
    finally:
        # 无论正常退出还是异常，都关闭引擎和存储后端
        await engine.close()
        await backend.close()
        print("[关闭] 对话引擎与存储后端已关闭")


def main() -> None:
    """程序主函数（同步入口，内部启动异步事件循环）。"""
    asyncio.run(async_main())


# 入口守护：只有直接运行本文件时才执行，被 import 时不执行。
if __name__ == "__main__":
    main()
