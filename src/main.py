# 仅使用 Python 标准库，体现 Step 1「零依赖」设计意图
import platform
import sys
from datetime import datetime

# 项目常量
APP_NAME = "langchain-chat"
APP_VERSION = "0.1.0"
CURRENT_STEP = "Step 1：项目初始化与工程化配置"

def print_banner() -> None:
    """打印启动横幅。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    banner = f"""
================================================================================
  {APP_NAME}  v{APP_VERSION}
================================================================================
  Python 版本  : {platform.python_version()}   ({sys.version.split()[0]})
  运行平台     : {platform.system()} {platform.machine()}
  启动时间     : {now}
  当前进度     : {CURRENT_STEP}
================================================================================
"""
    print(banner)
    print(f"[完成] {APP_NAME} 项目已启动（{CURRENT_STEP}）")


def main() -> None:
    print_banner()


if __name__ == "__main__":
    main()
