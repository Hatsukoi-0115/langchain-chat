from __future__ import annotations

from io import StringIO

from prompt_toolkit.formatted_text import ANSI
from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def render_to_ansi(renderable, width: int) -> ANSI:
    buffer = StringIO()
    console = Console(
        file=buffer,
        force_terminal=True,
        color_system="truecolor",
        width=width,
        legacy_windows=False,
    )
    console.print(renderable, end="")
    return ANSI(buffer.getvalue())


def build_header(route: str, status: str, width: int) -> ANSI:
    title = Text("Chat Bot TUI", style="bold cyan")
    meta = Text()
    meta.append(" route=", style="dim")
    meta.append(route, style="yellow")
    meta.append(" | status=", style="dim")
    meta.append(status, style="green")
    panel = Panel(
        Align.left(Text.assemble(title, "\n", meta)),
        box=ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )
    return render_to_ansi(panel, width)


def build_footer(width: int) -> ANSI:
    footer = Text()
    footer.append("ESC", style="bold")
    footer.append(" back  ", style="dim")
    footer.append("q", style="bold")
    footer.append(" quit  ", style="dim")
    footer.append("1/2/3", style="bold")
    footer.append(" menu shortcuts", style="dim")
    return render_to_ansi(footer, width)


def build_settings_view(user: str, email: str, session_id: str, message_count: int, width: int) -> ANSI:
    table = Table(box=ROUNDED, expand=True)
    table.add_column("Field", style="cyan", width=18)
    table.add_column("Value", style="white")
    table.add_row("User", user)
    table.add_row("Email", email)
    table.add_row("Session", session_id)
    table.add_row("Messages", str(message_count))
    body = Panel(
        table,
        title="Settings",
        border_style="yellow",
        padding=(0, 1),
    )
    return render_to_ansi(body, width)
