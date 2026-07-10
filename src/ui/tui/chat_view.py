from __future__ import annotations

from src.models.schemas import Message
from rich.box import ROUNDED
from rich.panel import Panel
from rich.table import Table

from src.ui.tui.widgets import render_to_ansi


def render_chat_view(messages: list[Message], width: int) -> object:
    table = Table(box=ROUNDED, expand=True)
    table.add_column("Time", style="dim", width=19)
    table.add_column("Sender", style="cyan", width=10)
    table.add_column("Message", style="white")
    if messages:
        for message in messages[-20:]:
            table.add_row(message.timestamp, message.sender, message.content)
    else:
        table.add_row("-", "-", "No messages yet. Type below and press Enter.")
    body = Panel(
        table,
        title="Chat History",
        border_style="green",
        padding=(0, 1),
    )
    return render_to_ansi(body, width)
