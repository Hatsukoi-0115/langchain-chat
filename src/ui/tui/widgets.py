"""TUI 复用组件（样式、格式化、工具函数）。

本模块封装 rich 的渲染能力，提供全站统一的样式。
其他 TUI 文件（menu_view、chat_view、app）都调用这里的函数。

设计原则（DRY）：把样式集中在 widgets.py，改样式只改一处，全站生效。
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


# 全局 Console 实例（所有 TUI 文件共用，保证输出一致）
console = Console()


def print_banner(version: str, python_version: str) -> None:
    """打印启动横幅。

    参数：
        version: 应用版本号
        python_version: Python 版本号
    """
    banner_text = Text()
    banner_text.append("LangChain Chat", style="bold cyan")
    banner_text.append(f"  v{version}", style="dim")
    banner_text.append(f"\nPython {python_version}", style="green")
    banner_text.append("\n当前进度：Step 5  预设管理", style="yellow")

    console.print(Panel(banner_text, border_style="cyan", title="欢迎", title_align="left"))


def print_info(message: str) -> None:
    """打印普通提示信息（蓝色）。"""
    console.print(f"[blue][信息][/] {message}")


def print_success(message: str) -> None:
    """打印成功信息（绿色）。"""
    console.print(f"[bold green][成功][/] {message}")


def print_error(message: str) -> None:
    """打印错误信息（红色加粗）。"""
    console.print(f"[bold red][错误][/] {message}")


def print_warning(message: str) -> None:
    """打印警告信息（黄色）。"""
    console.print(f"[yellow][警告][/] {message}")


def print_menu(title: str, options: list[str]) -> None:
    """打印菜单（带标题和编号选项）。

    参数：
        title: 菜单标题
        options: 选项文本列表
    """
    table = Table(title=title, show_header=True, border_style="cyan", expand=True)
    table.add_column("序号", style="bold yellow", width=6)
    table.add_column("选项", style="white")

    for index, option in enumerate(options, start=1):
        table.add_row(str(index), option)

    console.print(table)


def print_divider() -> None:
    """打印分隔线。"""
    console.print("[dim]" + "-" * 60 + "[/]")


def read_choice(max_choice: int) -> int:
    """读取用户选择的菜单序号，返回从 0 开始的索引。

    参数：
        max_choice: 最大有效序号（选项总数）
    返回：
        用户选择的索引（0 到 max_choice-1）
    """
    while True:
        try:
            raw = input(f"请输入序号 (1-{max_choice})，或 0 返回上层: ").strip()
            choice = int(raw)
            if choice == 0:
                return -1                    # -1 表示返回上层
            if 1 <= choice <= max_choice:
                return choice - 1            # 转为 0 基索引
            print_error(f"序号超出范围，请输入 0 到 {max_choice} 之间的数字")
        except ValueError:
            print_error("请输入数字")


def read_text(prompt_text: str, default: str = "") -> str:
    """读取用户输入的文本，支持默认值（回车保留）。

    参数：
        prompt_text: 提示文字
        default: 默认值。非空时会在提示中显示当前值，用户直接回车则返回默认值
    返回：
        用户输入的文本（已去除首尾空白）；若用户回车且 default 非空，则返回 default
    """
    if default:
        # 显示当前值，提示用户可回车保留
        raw = input(f"{prompt_text}（当前: {default}，回车保留）: ").strip()
        return raw if raw else default
    else:
        return input(f"{prompt_text}: ").strip()
