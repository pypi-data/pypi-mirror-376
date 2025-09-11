import sys
import os
import shutil
from pathlib import Path

def _load_platform_specific_binary():
    # 1. 检测当前 Python 版本和平台
    py_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
    is_64bit = sys.maxsize > 2**32
    platform = "win_amd64" if is_64bit else "win32"

    # 2. 构造目标 .pyd 路径
    source_pyd = Path(__file__).parent / "bin" / f"{py_version}-{platform}" / "DDS_All.pyd"
    target_pyd = Path(__file__).parent / "_native.pyd"

    # 3. 检查是否存在对应的预编译文件
    if not source_pyd.exists():
        available_versions = [
            f.stem for f in (Path(__file__).parent / "bin").glob("*/*.pyd")
        ]
        raise ImportError(
            f"Unsupported platform: Python {py_version} on {platform}\n"
            f"Available versions: {available_versions}"
        )

    # 4. 复制正确的 .pyd 到 _native.pyd
    if target_pyd.exists():
        target_pyd.unlink()
    shutil.copy(source_pyd, target_pyd)

# 在导入时动态加载
_load_platform_specific_binary()
from ._native import *  # 导出 C++ 模块的功能