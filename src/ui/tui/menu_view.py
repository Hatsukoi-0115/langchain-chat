from __future__ import annotations

from rich.box import ROUNDED
from rich.panel import Panel
from rich.table import Table

from src.ui.tui.widgets import render_to_ansi


def render_menu_view(width: int) -> object:
    table = Table(title="Menu", box=ROUNDED, expand=True)
    table.add_column("Key", style="cyan", width=8)
    table.add_column("Action", style="white")
    table.add_column("Hint", style="dim")
    table.add_row("1", "Chat", "Open the chat room")
    table.add_row("2", "Settings", "Inspect current session")
    table.add_row("3", "Exit", "Close the app")
    body = Panel(
        table,
        title="Main Menu",
        border_style="magenta",
        padding=(0, 1),
    )
    return render_to_ansi(body, width)
