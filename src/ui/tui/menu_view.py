"""菜单视图。

负责显示各个菜单并处理用户选择。
本步骤（Step 2）所有菜单选项的功能都是桩函数（stub），
只显示提示信息，不执行真实业务逻辑。
真实功能在后续步骤逐步实现：
    - 用户管理：Step 4
    - 预设管理：Step 5
    - 会话管理与对话：Step 7
    - 设置：Step 10
"""

from ui.tui import widgets


def show_user_menu() -> None:
    """用户管理菜单（桩）。Step 4 实现。"""
    widgets.print_info("用户管理功能将在 Step 4 实现")
    widgets.print_divider()


def show_session_menu() -> None:
    """会话管理菜单。

    注意：此函数在 Step 8 后不再被调用（app.py 改为调用 self._show_session_menu）。
    保留是为了兼容性。会话管理功能已在 app.py 的 _show_session_menu 实现。
    """
    widgets.print_info("请通过主菜单的「会话管理」访问此功能")
    widgets.print_divider()


def show_preset_menu() -> None:
    """预设管理菜单（桩）。Step 5 实现。"""
    widgets.print_info("预设管理功能将在 Step 5 实现")
    widgets.print_divider()


def show_settings_menu() -> None:
    """设置菜单。

    注意：此函数在 Step 10 后不再被调用（app.py 改为调用 self._show_settings_menu）。
    """
    widgets.print_info("请通过主菜单的「设置」访问此功能")
    widgets.print_divider()


def show_chat_view() -> None:
    """对话视图（桩）。Step 7 实现。"""
    widgets.print_info("对话功能将在 Step 7 实现（核心里程碑）")
    widgets.print_divider()


def show_about() -> None:
    """显示关于信息。"""
    widgets.console.print(
        "\n[bold cyan]LangChain Chat[/bold cyan]  "
        "基于 LangChain 的多轮会话系统（教学项目）\n"
        "[dim]按步骤开发中[/dim]\n"
    )
    widgets.print_divider()
