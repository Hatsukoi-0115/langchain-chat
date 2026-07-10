from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, TextArea

from src.interface.ui_protocol import AbstractUI
from src.models.schemas import Message, Session, User
from src.ui.tui.chat_view import render_chat_view
from src.ui.tui.menu_view import render_menu_view
from src.ui.tui.widgets import build_footer, build_header, build_settings_view


class Route(StrEnum):
    MENU = "menu"
    CHAT = "chat"
    SETTINGS = "settings"


@dataclass
class AppState:
    route: Route = Route.MENU
    status: str = "ready"
    user: User = field(
        default_factory=lambda: User(username="guest", email="guest@example.com")
    )
    session: Session = field(
        default_factory=lambda: Session(
            session_id=uuid4().hex,
            user=User(username="guest", email="guest@example.com"),
        )
    )
    messages: list[Message] = field(default_factory=list)
    selected_menu_index: int = 0

    def add_message(self, sender: str, content: str) -> Message:
        message = Message(
            message_id=uuid4().hex,
            session_id=self.session.session_id,
            sender=sender,
            content=content,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
        self.messages.append(message)
        return message


class TUIApplication(AbstractUI):
    def __init__(self) -> None:
        self.state = AppState()
        self._menu_items: list[tuple[str, Route]] = [
            ("Chat", Route.CHAT),
            ("Settings", Route.SETTINGS),
            ("Exit", Route.MENU),
        ]
        self._input = TextArea(
            height=3,
            prompt="You> ",
            multiline=False,
            wrap_lines=True,
        )
        self._input.accept_handler = self._handle_submit
        self._header = Window(
            content=FormattedTextControl(text=self._render_header),
            height=3,
            always_hide_cursor=True,
        )
        self._body = Window(
            content=FormattedTextControl(text=self._render_body),
            always_hide_cursor=True,
            wrap_lines=True,
        )
        self._footer = Window(
            content=FormattedTextControl(text=self._render_footer),
            height=1,
            always_hide_cursor=True,
        )
        self._app: Application | None = None

    def _build_application(self) -> Application:
        bindings = KeyBindings()

        menu_active = Condition(lambda: self.state.route == Route.MENU)
        not_menu = Condition(lambda: self.state.route != Route.MENU)

        @bindings.add("c-c")
        @bindings.add("q")
        def _quit(event) -> None:
            event.app.exit()

        @bindings.add("escape", filter=not_menu)
        def _back(event) -> None:
            self.go_to(Route.MENU)

        @bindings.add("1", filter=menu_active)
        def _menu_one(event) -> None:
            self.go_to(Route.CHAT)

        @bindings.add("2", filter=menu_active)
        def _menu_two(event) -> None:
            self.go_to(Route.SETTINGS)

        @bindings.add("3", filter=menu_active)
        def _menu_three(event) -> None:
            self.state.status = "exit requested"
            event.app.exit()

        root = HSplit(
            [
                self._header,
                Frame(body=self._body, title="Main View"),
                Frame(body=self._input, title="Input"),
                self._footer,
            ]
        )

        return Application(
            layout=Layout(root, focused_element=self._input),
            key_bindings=bindings,
            full_screen=True,
            style=self._style(),
        )

    def _style(self) -> Style:
        return Style.from_dict(
            {
                "frame.label": "bold",
                "textarea": "bg:#0b1220 #f8fafc",
            }
        )

    def _console_width(self) -> int:
        if self._app is None:
            return 88
        return max(40, self._app.output.get_size().columns - 4)

    def _render_header(self):
        return build_header(self.state.route.value, self.state.status, self._console_width())

    def _render_body(self):
        if self.state.route == Route.CHAT:
            return render_chat_view(self.state.messages, self._console_width())
        if self.state.route == Route.SETTINGS:
            return build_settings_view(
                self.state.user.username,
                self.state.user.email,
                self.state.session.session_id,
                len(self.state.messages),
                self._console_width(),
            )
        return render_menu_view(self._console_width())

    def _render_footer(self):
        return build_footer(self._console_width())

    def _handle_submit(self, buffer: Buffer) -> bool:
        text = buffer.text.strip()
        if not text:
            return False

        buffer.text = ""

        if self.state.route == Route.MENU:
            self._dispatch_menu_command(text)
        elif self.state.route == Route.CHAT:
            self.state.add_message("user", text)
            self.state.add_message("assistant", f"Echo: {text}")
            self.state.status = "message received"
        else:
            self.state.status = text

        self._invalidate()
        return True

    def _dispatch_menu_command(self, text: str) -> None:
        command = text.lower()
        if command in {"1", "chat"}:
            self.go_to(Route.CHAT)
            return
        if command in {"2", "settings"}:
            self.go_to(Route.SETTINGS)
            return
        if command in {"3", "exit", "quit"}:
            self.state.status = "exit requested"
            if self._app is not None:
                self._app.exit()
            return
        self.state.status = f"unknown command: {text}"

    def _invalidate(self) -> None:
        if self._app is not None:
            self._app.invalidate()

    def go_to(self, route: Route) -> None:
        self.state.route = route
        self.state.status = f"routed to {route.value}"
        self._invalidate()

    def display_message(self, message: str) -> None:
        self.state.add_message("system", message)
        self.state.status = message
        self._invalidate()

    def get_user_input(self, prompt: str) -> str:
        self.display_message(prompt)
        return self._input.text.strip()

    def run(self) -> None:
        if self._app is None:
            self._app = self._build_application()
        self._app.run()


def create_app() -> TUIApplication:
    return TUIApplication()


def main() -> None:
    create_app().run()


if __name__ == "__main__":
    main()
