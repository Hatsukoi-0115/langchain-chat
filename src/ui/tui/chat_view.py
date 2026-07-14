"""对话视图（完整实现）。

实现真实的多轮流式对话，对应需求文档 A1 至 A5（核心对话功能）。
Step 7 的核心里程碑：用户能在终端里和 LLM 真正聊天。

功能：
    - 多轮流式对话（LLM 逐字回复）
    - 预设角色选择（Step 5 的 system_prompt 注入）
    - 会话标题自动生成（LLM 摘要）
    - 对话自动保存（每轮存入数据库）
    - 命令系统：/exit /new /rename /help
    - prompt_toolkit 输入（支持历史回看）

对应需求：A1（多轮）、A2（流式）、C1（新建）、C6（自动保存）、C7（标题生成）、D3（选预设）、E2（Token 统计）
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from ui.tui import widgets


async def start_chat(app) -> None:
    """启动对话视图。

    参数：
        app: TUIApp 实例（从中获取 current_user、engine、session_manager、config 等）
    """
    # 1. 检查是否登录
    if app.current_user is None:
        widgets.print_warning("请先在用户管理中创建或切换用户")
        return

    # 2. 检查引擎和会话管理器
    if app.engine is None or app.session_manager is None:
        widgets.print_error("对话引擎未初始化")
        return

    # 3. 获取或创建会话
    session = app.current_session

    # 3.1 如果当前没有会话，先查数据库有没有历史会话
    if session is None:
        sessions = await app.session_manager.backend.list_sessions(app.current_user.id)
        if sessions:
            # 有历史会话，让用户选择「继续最近的」还是「新建」
            widgets.console.print(f"\n[bold]最近会话:[/bold] {sessions[0].title}")
            widgets.console.print("  1  继续最近的会话")
            widgets.console.print("  2  新建会话")
            choice = widgets.read_choice(2)
            if choice == 0:
                # 继续最近会话
                session = sessions[0]
                app.current_session = session
                widgets.print_info(f"已加载会话: {session.title}")
            elif choice == 1:
                # 新建会话
                session = await _create_new_session(app)
                if session is None:
                    return    # 用户取消创建
                app.current_session = session
            else:
                return    # 输入 0 返回主菜单
        else:
            # 没有历史会话，直接新建
            session = await _create_new_session(app)
            if session is None:
                return
            app.current_session = session

    # 3.2 如果当前已有会话（刚对话完又选开始对话），让用户选择「继续」还是「新建」
    elif session is not None:
        widgets.console.print(f"\n[bold]当前会话:[/bold] {session.title}")
        widgets.console.print("  1  继续当前会话")
        widgets.console.print("  2  新建会话")
        choice = widgets.read_choice(2)
        if choice == 0:
            pass    # 继续当前会话，session 不变
        elif choice == 1:
            # 新建会话
            session = await _create_new_session(app)
            if session is None:
                return
            app.current_session = session
        else:
            return    # 输入 0 返回主菜单

    # 4. 加载历史消息（如果有）
    messages = await app.session_manager.load_messages_as_langchain(session.id)
    if messages:
        widgets.print_info(f"已加载历史对话（{len(messages)} 条消息），继续聊天")

    # 4.1 如果是新会话且选了预设，注入 system_prompt
    if not messages and session.preset_id is not None:
        preset = await app.preset_manager.get_preset(session.preset_id)
        if preset:
            messages.append(SystemMessage(content=preset.system_prompt))
            # 同时保存到数据库（作为 system 消息）
            await app.session_manager.add_message(
                session, role="system", content=preset.system_prompt
            )
            widgets.print_info(f"已应用预设: {preset.name}")

    # 5. 创建输入会话对象（prompt_toolkit，含输入历史）
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    input_session = PromptSession(history=InMemoryHistory())

    # 6. 进入对话循环
    widgets.console.print("\n[bold green]=== 对话开始（输入 /help 查看命令，/exit 退出）===[/bold green]\n")

    while True:
        # 读取用户输入
        user_input = await widgets.read_chat_input(session=input_session)

        if not user_input:
            continue

        # 处理命令
        if user_input.startswith("/"):
            should_exit = await _handle_command(app, session, user_input)
            if should_exit == "exit":
                break
            elif should_exit == "new_session":
                # 用户新建了会话，更新 session 和 messages
                session = app.current_session
                messages = []
            continue

        # 普通对话：发送给 LLM
        # 6.1 把用户输入加入内存历史
        user_msg = HumanMessage(content=user_input)
        messages.append(user_msg)

        # 6.2 显示用户输入
        widgets.console.print(f"\n[bold cyan][你][/] {user_input}")

        # 6.3 流式调用 LLM
        widgets.console.print("[bold green][AI][/] ", end="")
        full_reply = ""
        final_usage = None

        try:
            async for text, usage in app.engine.astream(messages):
                if text:
                    widgets.console.print(text, end="", style="green")
                    full_reply += text
                if usage is not None:
                    final_usage = usage
            widgets.console.print()  # 换行
        except Exception as e:
            widgets.print_error(f"\nLLM 调用失败: {type(e).__name__}: {e}")
            # 移除刚加入的用户消息（因为没得到回复）
            messages.pop()
            continue

        # 6.4 把 AI 回复加入内存历史
        ai_msg = AIMessage(content=full_reply)
        messages.append(ai_msg)

        # 6.5 保存到数据库
        prompt_tokens = final_usage.get("prompt_tokens", 0) if final_usage else 0
        completion_tokens = final_usage.get("completion_tokens", 0) if final_usage else 0
        await app.session_manager.add_message(
            session, role="human", content=user_input
        )
        await app.session_manager.add_message(
            session, role="ai", content=full_reply,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
        )

        # 6.6 显示 Token 统计
        if final_usage:
            widgets.console.print(
                f"[dim]Token: 输入 {prompt_tokens}，输出 {completion_tokens}，"
                f"累计 {session.total_prompt_tokens + session.total_completion_tokens}[/dim]\n"
            )

        # 6.7 首轮自动生成标题
        if session.title == "新会话":
            widgets.console.print("[dim]正在生成会话标题...[/dim]", end="")
            title = await app.session_manager.generate_title(user_input, app.engine)
            await app.session_manager.update_title(session, title)
            widgets.console.print(f" [bold yellow]{title}[/bold yellow]\n")


async def _create_new_session(app) -> None:
    """创建新会话（含预设选择）。

    返回：创建的 Session，或 None（用户取消）
    """
    widgets.console.print("\n[bold]=== 新建会话 ===[/bold]")

    # 1. 选择预设
    preset_id = await _select_preset(app)

    # 2. 创建会话
    config = app.config
    session = await app.session_manager.create_session(
        user_id=app.current_user.id,
        model_name=config.default_model,
        preset_id=preset_id,
    )
    widgets.print_success(f"新会话已创建（id={session.id}）")
    return session


async def _select_preset(app) -> None:
    """选择预设。返回选中的 preset_id，或 None（不使用预设）。"""
    presets = await app.preset_manager.list_presets(app.current_user.id)

    if not presets:
        widgets.print_info("没有可用预设，将不使用预设")
        return None

    widgets.console.print("\n[bold]可选预设[/bold]")
    widgets.console.print("  0  不使用预设")
    for i, p in enumerate(presets, start=1):
        tag = "[内置]" if p.is_builtin else "[自定义]"
        widgets.console.print(f"  {i}  {tag} {p.name} - {p.description}")

    choice_str = widgets.read_text("请选择预设序号（0=不使用）")
    try:
        choice = int(choice_str)
    except ValueError:
        widgets.print_info("未选择预设")
        return None

    if choice == 0:
        return None
    if 1 <= choice <= len(presets):
        selected = presets[choice - 1]
        widgets.print_info(f"已选择预设: {selected.name}")

        # 如果选了预设，把 system_prompt 作为第一条 system 消息
        # 注意：这里返回 preset_id，实际注入 system_prompt 在对话开始时处理
        return selected.id

    widgets.print_info("序号无效，不使用预设")
    return None


async def _handle_command(app, session, command: str) -> str:
    """处理对话中的 / 命令。

    返回：
        "exit"：退出对话
        "new_session"：新建了会话
        None：其他命令（继续循环）
    """
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()

    if cmd == "/exit":
        widgets.print_info("退出对话，返回主菜单")
        return "exit"

    elif cmd == "/new":
        # 新建会话
        new_session = await _create_new_session(app)
        if new_session is not None:
            app.current_session = new_session
            widgets.print_success(f"已切换到新会话: {new_session.title}")
            return "new_session"
        return None

    elif cmd == "/rename":
        # 修改标题
        if len(parts) < 2:
            new_title = widgets.read_text("请输入新标题")
        else:
            new_title = parts[1].strip()
        if new_title:
            await app.session_manager.update_title(session, new_title)
            widgets.print_success(f"标题已修改为: {new_title}")
        else:
            widgets.print_warning("标题不能为空")
        return None

    elif cmd == "/help":
        widgets.console.print("\n[bold]可用命令[/bold]")
        widgets.console.print("  /exit         退出对话，返回主菜单")
        widgets.console.print("  /new          新建会话（选预设、清空上下文）")
        widgets.console.print("  /rename 标题  修改当前会话标题")
        widgets.console.print("  /help         显示本帮助")
        widgets.console.print("  其他文字      发给 LLM 对话\n")
        return None

    else:
        widgets.print_warning(f"未知命令: {cmd}（输入 /help 查看可用命令）")
        return None
