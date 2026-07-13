"""TUI 主应用（菜单路由、状态管理）。

这是 TUI 的主入口，负责：
    1. 显示启动横幅。
    2. 显示主菜单并路由到对应视图。
    3. 维护主循环（直到用户选择退出）。

TUIApp 继承 AbstractUI，实现其全部抽象方法，满足 UI 接口契约。
"""

import platform

from interface.ui_protocol import AbstractUI
from ui.tui import menu_view, widgets
from ui.tui.chat_view import start_chat

# 主菜单选项（序号与选项的对应关系）
MAIN_MENU_OPTIONS = [
    "用户管理",
    "会话管理",
    "预设管理",
    "开始对话",
    "设置",
    "关于",
    "退出",
]


class TUIApp(AbstractUI):
    """TUI 主应用。

    继承 AbstractUI 并实现其全部抽象方法。
    """

    def __init__(self) -> None:
        # 应用状态（当前用户、当前会话等，后续步骤扩展）
        self.current_user = None
        self.current_session = None

    # ── AbstractUI 接口实现 ───────────────────────────────────────────────

    async def display_message(self, role: str, content: str) -> None:
        """显示一条消息。"""
        if role == "human":
            widgets.console.print(f"[bold cyan][你][/] {content}")
        elif role == "ai":
            widgets.console.print(f"[bold green][AI][/] {content}")
        else:
            widgets.console.print(f"[dim][系统][/] {content}")

    async def get_user_input(self, prompt_text: str = "") -> str:
        """获取用户输入。"""
        return widgets.read_text(prompt_text)

    async def display_menu(self, title: str, options: list[str]) -> int:
        """显示菜单并获取选择。"""
        widgets.print_menu(title, options)
        return widgets.read_choice(len(options))

    async def display_error(self, message: str) -> None:
        """显示错误。"""
        widgets.print_error(message)

    async def display_info(self, message: str) -> None:
        """显示提示。"""
        widgets.print_info(message)

    # ── 主循环 ────────────────────────────────────────────────────────────

    async def run(self) -> None:
        """启动 TUI 主循环。

        流程：打印横幅 → 显示主菜单 → 读取选择 → 路由 → 循环。
        """
        # 1. 打印启动横幅
        widgets.print_banner(version="0.1.0", python_version=platform.python_version())

        # 2. 主循环
        while True:
            # 显示主菜单
            choice = await self.display_menu("主菜单", MAIN_MENU_OPTIONS)

            # 路由到对应视图
            if choice == -1:
                # 用户输入 0（返回上层），在主菜单中等同于不做操作
                continue
            elif choice == 0:
                menu_view.show_user_menu()
            elif choice == 1:
                menu_view.show_session_menu()
            elif choice == 2:
                menu_view.show_preset_menu()
            elif choice == 3:
                await start_chat()
            elif choice == 4:
                menu_view.show_settings_menu()
            elif choice == 5:
                menu_view.show_about()
            elif choice == 6:
                # 退出
                widgets.print_info("感谢使用，再见。")
                break
