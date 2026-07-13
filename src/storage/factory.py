"""存储后端工厂。

根据 config.yaml 中的 storage.type 配置，创建对应的存储后端实例。
对应需求文档第四章「存储架构」的工厂模式设计。

设计说明：
    - 业务代码不直接 new 某个后端，而是通过工厂获取。
    - 这样切换后端（sqlite/mysql/file）只需改配置，无需改业务代码。
    - 新增后端时，只需在工厂里加一个分支。
"""

from storage.base import StorageBackend


class StorageFactory:
    """存储后端工厂。

    使用方式：
        backend = StorageFactory.create("sqlite")
        await backend.initialize()
    """

    @staticmethod
    def create(storage_type: str, db_path: str = "data/sqlite/app.db") -> StorageBackend:
        """根据存储类型创建对应的后端实例。

        参数：
            storage_type: 存储类型字符串（sqlite / mysql / file）
            db_path: 数据库文件路径（仅 sqlite 类型需要）
        返回：
            对应的 StorageBackend 实例（未初始化，需再调用 initialize）
        """
        if storage_type == "sqlite":
            # 延迟导入：只用 sqlite 时才加载 sqlite_backend，避免无用依赖
            from storage.sqlite_backend import SQLiteBackend
            return SQLiteBackend(db_path=db_path)
        elif storage_type == "mysql":
            # MySQL 后端在 Step 11 实现
            raise NotImplementedError("MySQL 后端将在 Step 11 实现")
        elif storage_type == "file":
            # File 后端在 Step 12 实现
            raise NotImplementedError("File 后端将在 Step 12 实现")
        else:
            raise ValueError(f"不支持的存储类型: {storage_type}（可选: sqlite/mysql/file）")
