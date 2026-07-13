"""数据库初始化脚本。

功能：
    1. 创建数据库和所有表（通过 SQLiteBackend.initialize）。
    2. 运行一轮冒烟测试，验证 CRUD 全部可用。

运行方式：
    uv run python scripts/init_db.py

对应需求文档：存储层初始化（scripts/init_db.py 数据库初始化）。
"""

import asyncio
import sys
from pathlib import Path

# 将 src 目录加入模块搜索路径（与 main.py 同样的 sys.path 注入手法）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models.schemas import Message, Preset, Session, User, UserConfig
from storage.factory import StorageFactory

# # 测试用独立的数据库，跑完即删
# import os
# test_db = "data/sqlite/test.db"
# if os.path.exists(test_db):
#     os.remove(test_db)

async def init_and_smoke_test() -> None:
    """初始化数据库并运行冒烟测试。"""
    print("=" * 60)
    print("Step 3：SQLite 存储后端初始化与冒烟测试")
    print("=" * 60)

    # 1. 通过工厂创建后端实例
    backend = StorageFactory.create("sqlite")       # 测试用独立数据库 db_path=test_db
    print(f"[1/6] 创建存储后端: {type(backend).__name__}")

    try:
        # 2. 初始化（建目录、建表）
        await backend.initialize()
        print("[2/6] 数据库已初始化（data/sqlite/app.db，5 张表已创建）")

        # 2.5 初始化后清理可能残留的测试数据（保证幂等性）
        #     无论上次运行是否正常结束、是否中途崩溃，都先清理同名测试用户。
        #     delete_user 会触发 ON DELETE CASCADE，自动清理其关联的会话和消息。
        existing = await backend.get_user_by_name("smoke_test_user")
        if existing:
            await backend.delete_user(existing.id)
            print(f"      [清理] 发现残留测试用户 id={existing.id}，已删除")

        # 3. 冒烟测试：创建用户
        user = await backend.create_user(User(id=0, username="smoke_test_user"))
        print(f"[3/6] 创建用户: id={user.id}, username={user.username}")

        # 4. 冒烟测试：创建会话
        session = await backend.create_session(Session(
            id=0, user_id=user.id, title="冒烟测试会话", model_name="deepseek-chat",
        ))
        print(f"[4/6] 创建会话: id={session.id}, title={session.title}")

        # 5. 冒烟测试：添加消息（一轮对话产生 human + ai 两条）
        human_msg = await backend.add_message(Message(
            id=0, session_id=session.id, role="human", content="你好，这是冒烟测试",
        ))
        ai_msg = await backend.add_message(Message(
            id=0, session_id=session.id, role="ai", content="你好，冒烟测试通过",
        ))
        print(f"[5/6] 添加消息: human id={human_msg.id}, ai id={ai_msg.id}")

        # 6. 冒烟测试：查询验证
        # 查消息
        msgs = await backend.list_messages(session.id)
        print(f"[6/6] 查询消息: 会话 {session.id} 共 {len(msgs)} 条")
        for m in msgs:
            print(f"      - [{m.role}] {m.content}")

        # 搜索验证
        results = await backend.search_messages(user.id, "冒烟")
        print(f"      搜索'冒烟': 命中 {len(results)} 条")

        # 列会话验证
        sessions = await backend.list_sessions(user.id)
        print(f"      用户 {user.id} 的会话数: {len(sessions)}")

        # 清理：删除测试用户（关联数据靠 CASCADE 自动清理）
        await backend.delete_user(user.id)
        print(f"\n[清理] 已删除测试用户 {user.id}（关联数据自动清理）")
        print("[完成] 数据库初始化与冒烟测试全部通过")

    finally:
        # 关闭连接
        await backend.close()
        print("[关闭] SQLite 连接已关闭")


def main() -> None:
    """脚本主入口。"""
    asyncio.run(init_and_smoke_test())


if __name__ == "__main__":
    main()
