"""TUI 主应用（菜单路由、状态管理）。

这是 TUI 的主入口，负责：
    1. 显示启动横幅。
    2. 显示主菜单并路由到对应视图。
    3. 维护主循环（直到用户选择退出）。

Step 4 新增：
    - 持有存储后端与各业务管理器（UserManager 等）。
    - 实现用户管理子菜单（创建/列出/切换/删除）。
    - 维护当前登录用户状态。

Step 5 新增：
    - 持有 PresetManager。
    - 实现预设管理子菜单（查看/新增/编辑/删除）。

TUIApp 继承 AbstractUI，实现其全部抽象方法，满足 UI 接口契约。
"""

import platform

from core.config_manager import get_config
from core.preset_manager import PresetManager
from core.session_manager import SessionManager
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

# 预设管理子菜单选项
PRESET_MENU_OPTIONS = [
    "列出所有预设",
    "新增自定义预设",
    "编辑自定义预设",
    "删除自定义预设",
    "返回主菜单",
]

# 会话管理子菜单选项
SESSION_MENU_OPTIONS = [
    "查看会话列表",
    "加载会话（设为当前）",
    "重命名会话",
    "删除会话",
    "返回主菜单",
]


class TUIApp(AbstractUI):
    """TUI 主应用。

    继承 AbstractUI 并实现其全部抽象方法。
    """

    def __init__(self, backend=None, engine=None, config=None) -> None:
        # 存储后端（由 main.py 注入）
        self.backend = backend
        # 对话引擎（由 main.py 注入）
        self.engine = engine
        # 应用配置（由 main.py 注入）
        self.config = config
        # 业务管理器（backend 注入后初始化）
        self.user_manager: UserManager = None
        self.preset_manager: PresetManager = None
        self.session_manager: SessionManager = None
        if backend is not None:
            self.user_manager = UserManager(backend)
            self.preset_manager = PresetManager(backend)
            if config is not None:
                self.session_manager = SessionManager(backend, config)

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

    async def get_user_input(self, prompt_text: str = "", default: str = "") -> str:
        """获取用户输入。"""
        return widgets.read_text(prompt_text, default=default)

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

    def _require_login(self) -> bool:
        """检查是否已登录。未登录则提示并返回 False。"""
        if self.current_user is None:
            widgets.print_warning("请先在用户管理中创建或切换用户")
            return False
        return True

    # ── 主循环 ────────────────────────────────────────────────────────────

    async def run(self) -> None:
        """启动 TUI 主循环。

        流程：打印横幅 → 显示主菜单 → 读取选择 → 路由 → 循环。
        """
        # 1. 打印启动横幅
        widgets.print_banner(
            version="0.1.0",
            python_version=platform.python_version(),
            current_step=get_config().current_step,
        )

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
                await self._show_session_menu()
            elif choice == 2:
                await self._show_preset_menu()
            elif choice == 3:
                await start_chat(self)
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
                self.current_session = None
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
        self.current_session = None    # 切换用户时清空当前会话（用户隔离）
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

    # ── 预设管理子菜单（Step 5 实现）──────────────────────────────────────

    async def _show_preset_menu(self) -> None:
        """预设管理子菜单。"""
        if self.preset_manager is None:
            widgets.print_error("预设管理未初始化（存储后端未注入）")
            return

        while True:
            widgets.print_divider()
            self._show_current_user()
            choice = await self.display_menu("预设管理", PRESET_MENU_OPTIONS)

            if choice == -1 or choice == 4:
                # 返回主菜单
                return
            elif choice == 0:
                await self._list_presets()
            elif choice == 1:
                await self._create_preset()
            elif choice == 2:
                await self._edit_preset()
            elif choice == 3:
                await self._delete_preset()

    async def _list_presets(self) -> None:
        """列出所有预设（内置 + 当前用户的自定义）。"""
        # 查看预设不需要登录（内置预设是公开的）
        if self.current_user:
            presets = await self.preset_manager.list_presets(self.current_user.id)
        else:
            # 未登录只看内置
            presets = await self.preset_manager.list_presets(0)

        if not presets:
            widgets.print_info("目前没有任何预设")
            return

        widgets.console.print("\n[bold]预设列表[/bold]")
        for p in presets:
            tag = "[内置]" if p.is_builtin else "[自定义]"
            widgets.console.print(
                f"  id={p.id}  {tag} [cyan]{p.name}[/cyan]"
                f"  - {p.description}"
            )
        builtin_count = sum(1 for p in presets if p.is_builtin)
        custom_count = len(presets) - builtin_count
        widgets.print_info(f"共 {len(presets)} 个预设（内置 {builtin_count}，自定义 {custom_count}）")

    async def _create_preset(self) -> None:
        """新增自定义预设（D2）。"""
        if not self._require_login():
            return

        name = await self.get_user_input("请输入预设名")
        if not name:
            widgets.print_warning("未输入预设名，取消创建")
            return

        description = await self.get_user_input("请输入预设描述（可选，回车跳过）")

        system_prompt = await self.get_user_input("请输入系统提示词（定义 AI 角色）")
        if not system_prompt:
            widgets.print_warning("系统提示词不能为空，取消创建")
            return

        try:
            preset = await self.preset_manager.create_preset(
                user_id=self.current_user.id,
                name=name,
                description=description,
                system_prompt=system_prompt,
            )
            widgets.print_success(f"预设创建成功: {preset.name}（id={preset.id}）")
        except ValueError as e:
            widgets.print_error(str(e))

    async def _edit_preset(self) -> None:
        """编辑自定义预设（D2）。"""
        if not self._require_login():
            return

        # 先列出预设，让用户选
        presets = await self.preset_manager.list_presets(self.current_user.id)
        customs = [p for p in presets if not p.is_builtin]
        if not customs:
            widgets.print_info("你没有自定义预设，无法编辑（内置预设不允许修改）")
            return

        widgets.console.print("\n[bold]可编辑的自定义预设[/bold]")
        for p in customs:
            widgets.console.print(f"  id={p.id}  [cyan]{p.name}[/cyan]  - {p.description}")

        preset_id_str = await self.get_user_input("请输入要编辑的预设 id")
        try:
            preset_id = int(preset_id_str)
        except ValueError:
            widgets.print_error("请输入有效的数字 id")
            return

        # 找到对应的预设
        target = None
        for p in customs:
            if p.id == preset_id:
                target = p
                break
        if target is None:
            widgets.print_error(f"id={preset_id} 不在您的自定义预设中（或不存在）")
            return

        # 逐字段编辑（回车保留原值）
        new_name = await self.get_user_input("预设名", default=target.name)
        new_desc = await self.get_user_input("描述", default=target.description)
        new_prompt = await self.get_user_input("系统提示词", default=target.system_prompt)

        try:
            await self.preset_manager.update_preset(
                preset=target, name=new_name, description=new_desc, system_prompt=new_prompt
            )
            widgets.print_success(f"预设 '{new_name}' 已更新")
        except ValueError as e:
            widgets.print_error(str(e))

    async def _delete_preset(self) -> None:
        """删除自定义预设（D2）。"""
        if not self._require_login():
            return

        presets = await self.preset_manager.list_presets(self.current_user.id)
        customs = [p for p in presets if not p.is_builtin]
        if not customs:
            widgets.print_info("你没有自定义预设，无法删除（内置预设不允许删除）")
            return

        widgets.console.print("\n[bold]可删除的自定义预设[/bold]")
        for p in customs:
            widgets.console.print(f"  id={p.id}  [cyan]{p.name}[/cyan]  - {p.description}")

        preset_id_str = await self.get_user_input("请输入要删除的预设 id")
        try:
            preset_id = int(preset_id_str)
        except ValueError:
            widgets.print_error("请输入有效的数字 id")
            return

        # 二次确认
        confirm = await self.get_user_input(f"确认删除预设 id={preset_id}？输入 yes 确认")
        if confirm.lower() != "yes":
            widgets.print_info("已取消删除")
            return

        try:
            await self.preset_manager.delete_preset(preset_id)
            widgets.print_success(f"预设 id={preset_id} 已删除")
        except ValueError as e:
            widgets.print_error(str(e))

    # ── 会话管理子菜单（Step 8 实现）──────────────────────────────────────

    async def _show_session_menu(self) -> None:
        """会话管理子菜单。"""
        if self.session_manager is None:
            widgets.print_error("会话管理未初始化（存储后端未注入）")
            return

        while True:
            widgets.print_divider()
            self._show_current_user()
            choice = await self.display_menu("会话管理", SESSION_MENU_OPTIONS)

            if choice == -1 or choice == 4:
                # 返回主菜单
                return
            elif choice == 0:
                await self._list_sessions()
            elif choice == 1:
                await self._load_session()
            elif choice == 2:
                await self._rename_session()
            elif choice == 3:
                await self._delete_session()

    async def _list_sessions(self) -> None:
        """查看会话列表（C3）。"""
        if not self._require_login():
            return

        sessions = await self.session_manager.list_sessions(self.current_user.id)
        if not sessions:
            widgets.print_info("目前没有任何会话")
            return

        widgets.console.print("\n[bold]会话列表[/bold]")
        for i, s in enumerate(sessions, start=1):
            # 标记当前会话
            mark = " <- 当前" if (self.current_session and s.id == self.current_session.id) else ""
            # 格式化时间（只显示日期和时分）
            created = s.created_at.strftime("%Y-%m-%d %H:%M")
            updated = s.updated_at.strftime("%Y-%m-%d %H:%M")
            total_tokens = s.total_prompt_tokens + s.total_completion_tokens
            widgets.console.print(
                f"  {i}. [cyan]{s.title}[/cyan]{mark}"
            )
            widgets.console.print(
                f"     模型: {s.model_name}  |  创建: {created}  |  更新: {updated}  |  Token: {total_tokens}"
            )
        widgets.print_info(f"共 {len(sessions)} 个会话")

    async def _load_session(self) -> None:
        """加载会话（设为当前会话，C2）。"""
        if not self._require_login():
            return

        sessions = await self.session_manager.list_sessions(self.current_user.id)
        if not sessions:
            widgets.print_info("目前没有任何会话，无法加载")
            return

        # 显示列表供选择
        widgets.console.print("\n[bold]选择要加载的会话[/bold]")
        for i, s in enumerate(sessions, start=1):
            widgets.console.print(f"  {i}. {s.title}")
        widgets.console.print("  0. 取消")

        choice_str = widgets.read_text("请输入序号")
        try:
            choice = int(choice_str)
        except ValueError:
            widgets.print_error("请输入有效的数字")
            return

        if choice == 0:
            widgets.print_info("已取消")
            return
        if not (1 <= choice <= len(sessions)):
            widgets.print_error("序号超出范围")
            return

        selected = sessions[choice - 1]
        self.current_session = selected
        widgets.print_success(f"已加载会话: {selected.title}（id={selected.id}）")
        widgets.print_info("选择「开始对话」可继续此会话")

    async def _rename_session(self) -> None:
        """重命名会话（C4）。"""
        if not self._require_login():
            return

        sessions = await self.session_manager.list_sessions(self.current_user.id)
        if not sessions:
            widgets.print_info("目前没有任何会话，无法重命名")
            return

        # 显示列表供选择
        widgets.console.print("\n[bold]选择要重命名的会话[/bold]")
        for i, s in enumerate(sessions, start=1):
            widgets.console.print(f"  {i}. {s.title}")

        choice_str = widgets.read_text("请输入序号")
        try:
            choice = int(choice_str)
        except ValueError:
            widgets.print_error("请输入有效的数字")
            return

        if not (1 <= choice <= len(sessions)):
            widgets.print_error("序号超出范围")
            return

        selected = sessions[choice - 1]
        new_title = widgets.read_text("请输入新标题", default=selected.title)
        if not new_title:
            widgets.print_warning("标题不能为空")
            return

        try:
            await self.session_manager.rename_session(selected.id, new_title)
            widgets.print_success(f"会话已重命名为: {new_title}")
            # 如果改的是当前会话，更新 current_session 的标题
            if self.current_session and selected.id == self.current_session.id:
                self.current_session.title = new_title
        except ValueError as e:
            widgets.print_error(str(e))

    async def _delete_session(self) -> None:
        """删除会话（C5），需二次确认。"""
        if not self._require_login():
            return

        sessions = await self.session_manager.list_sessions(self.current_user.id)
        if not sessions:
            widgets.print_info("目前没有任何会话，无法删除")
            return

        # 显示列表供选择
        widgets.console.print("\n[bold]选择要删除的会话[/bold]")
        for i, s in enumerate(sessions, start=1):
            mark = " <- 当前" if (self.current_session and s.id == self.current_session.id) else ""
            widgets.console.print(f"  {i}. {s.title}{mark}")

        choice_str = widgets.read_text("请输入序号")
        try:
            choice = int(choice_str)
        except ValueError:
            widgets.print_error("请输入有效的数字")
            return

        if not (1 <= choice <= len(sessions)):
            widgets.print_error("序号超出范围")
            return

        selected = sessions[choice - 1]

        # 二次确认
        confirm = await self.get_user_input(f"确认删除会话 '{selected.title}'？此操作不可恢复。输入 yes 确认")
        if confirm.lower() != "yes":
            widgets.print_info("已取消删除")
            return

        try:
            await self.session_manager.delete_session(selected.id)
            widgets.print_success(f"会话 '{selected.title}' 已删除（含全部消息）")
            # 如果删的是当前会话，清空 current_session
            if self.current_session and selected.id == self.current_session.id:
                self.current_session = None
                widgets.print_info("已清空当前会话（因为删除的就是当前会话）")
        except ValueError as e:
            widgets.print_error(str(e))
