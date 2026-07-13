"""TUI 主应用（菜单路由、状态管理）。

这是 TUI 的主入口，负责：
    1. 显示启动横幅。
    2. 显示主菜单并路由到对应视图。
    3. 维护主循环（直到用户选择退出）。

Step 4 新增：
    - 持有存储后端与各业务管理器（UserManager 等）。
    - 实现用户管理子菜单（创建/列出/切换/删除）。
    - 维护当前登录用户状态。

TUIApp 继承 AbstractUI，实现其全部抽象方法，满足 UI 接口契约。
"""

import platform

from core.config_manager import get_config
from core.user_manager import UserManager
from interface.ui_protocol import AbstractUI
from storage.factory import StorageFactory
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

# 用户管理子菜单选项
USER_MENU_OPTIONS = [
    "创建用户",
    "列出所有用户",
    "切换当前用户",
    "删除用户",
    "返回主菜单",
]


class TUIApp(AbstractUI):
    """TUI 主应用。

    继承 AbstractUI 并实现其全部抽象方法。
    """

    def __init__(self, backend=None) -> None:
        # 存储后端（由 main.py 注入）
        self.backend = backend
        # 业务管理器（backend 注入后初始化）
        self.user_manager: UserManager = None
        if backend is not None:
            self.user_manager = UserManager(backend)

        # 应用状态
        self.current_user = None          # 当前登录用户（User 对象或 None）
        self.current_session = None       # 当前会话（Step 7 起使用）

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

    # ── 辅助：显示当前用户状态 ────────────────────────────────────────────

    def _show_current_user(self) -> None:
        """在菜单顶部显示当前登录用户。"""
        if self.current_user:
            widgets.console.print(
                f"[dim]当前用户: [bold yellow]{self.current_user.username}[/bold yellow]"
                f"（id={self.current_user.id}）[/dim]"
            )
        else:
            widgets.console.print("[dim]当前用户: 未登录[/dim]")

    # ── 主循环 ────────────────────────────────────────────────────────────

    async def run(self) -> None:
        """启动 TUI 主循环。

        流程：打印横幅 → 显示主菜单 → 读取选择 → 路由 → 循环。
        """
        # 1. 打印启动横幅
        widgets.print_banner(version="0.1.0", python_version=platform.python_version())

        # 2. 主循环
        while True:
            # 显示当前用户状态
            self._show_current_user()

            # 显示主菜单
            choice = await self.display_menu("主菜单", MAIN_MENU_OPTIONS)

            # 路由到对应视图
            if choice == -1:
                # 用户输入 0（返回上层），在主菜单中等同于不做操作
                continue
            elif choice == 0:
                await self._show_user_menu()
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

    # ── 用户管理子菜单（Step 4 实现）──────────────────────────────────────

    async def _show_user_menu(self) -> None:
        """用户管理子菜单。"""
        if self.user_manager is None:
            widgets.print_error("用户管理未初始化（存储后端未注入）")
            return

        while True:
            widgets.print_divider()
            self._show_current_user()
            choice = await self.display_menu("用户管理", USER_MENU_OPTIONS)

            if choice == -1 or choice == 4:
                # 返回主菜单
                return
            elif choice == 0:
                await self._create_user()
            elif choice == 1:
                await self._list_users()
            elif choice == 2:
                await self._switch_user()
            elif choice == 3:
                await self._delete_user()

    async def _create_user(self) -> None:
        """创建用户（B1）。"""
        username = await self.get_user_input("请输入新用户名")
        if not username:
            widgets.print_warning("未输入用户名，取消创建")
            return
        try:
            # 默认模型用配置里的默认值
            config = get_config()
            user = await self.user_manager.create_user(
                username, default_model=config.default_model
            )
            widgets.print_success(f"用户创建成功: {user.username}（id={user.id}）")
            # 创建后自动切换为当前用户（首次使用体验更好）
            if self.current_user is None:
                self.current_user = user
                widgets.print_info(f"已自动切换为当前用户: {user.username}")
        except ValueError as e:
            widgets.print_error(str(e))

    async def _list_users(self) -> None:
        """列出所有用户。"""
        users = await self.user_manager.list_users()
        if not users:
            widgets.print_info("目前没有任何用户")
            return

        widgets.console.print("\n[bold]用户列表[/bold]")
        for u in users:
            # 标记当前用户
            mark = " <- 当前" if (self.current_user and u.id == self.current_user.id) else ""
            widgets.console.print(
                f"  id={u.id}  用户名=[cyan]{u.username}[/cyan]"
                f"  模型={u.default_model or '默认'}{mark}"
            )
        widgets.print_info(f"共 {len(users)} 个用户")

    async def _switch_user(self) -> None:
        """切换当前用户（B2）。"""
        username = await self.get_user_input("请输入要切换到的用户名")
        if not username:
            widgets.print_warning("未输入用户名，取消切换")
            return

        user = await self.user_manager.get_user(username)
        if user is None:
            widgets.print_error(f"用户 '{username}' 不存在")
            return

        self.current_user = user
        widgets.print_success(f"已切换到用户: {user.username}（id={user.id}）")

    async def _delete_user(self) -> None:
        """删除用户（B3），需二次确认。"""
        username = await self.get_user_input("请输入要删除的用户名")
        if not username:
            widgets.print_warning("未输入用户名，取消删除")
            return

        user = await self.user_manager.get_user(username)
        if user is None:
            widgets.print_error(f"用户 '{username}' 不存在")
            return

        # 安全检查：不允许删除当前登录的用户
        if self.current_user and user.id == self.current_user.id:
            widgets.print_warning("不允许删除当前正在登录的用户，请先切换到其他用户")
            return

        # 二次确认
        confirm = await self.get_user_input(f"确认删除用户 '{username}'？输入 yes 确认")
        if confirm.lower() != "yes":
            widgets.print_info("已取消删除")
            return

        await self.user_manager.delete_user(user.id)
        widgets.print_success(f"用户 '{username}' 已删除（关联数据已自动清理）")
