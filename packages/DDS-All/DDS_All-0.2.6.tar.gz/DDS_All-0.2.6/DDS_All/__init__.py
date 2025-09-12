import sys
import os
from pathlib import Path

def _load_platform_pyd():
    # 获取用户环境的 Python 版本和平台
    py_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
    is_64bit = sys.maxsize > 2**32
    platform = "win_amd64" if is_64bit else "win32"
    
    # 目标 .pyd 路径
    pyd_path = Path(__file__).parent / "bin" / f"{py_version}-{platform}" / "DDS_All.pyd"
    
    # 检查文件是否存在
    if not pyd_path.exists():
        available = [d.name for d in (Path(__file__).parent / "bin").glob("cp*") if d.is_dir()]
        raise ImportError(
            f"不兼容的平台: Python {py_version} {platform}\n"
            f"可用版本: {available}"
        )
    
    # 将依赖 DLL 所在目录加入系统路径
    libs_dir = Path(__file__).parent / "bin" / "libs"
    if libs_dir.exists():
        os.add_dll_directory(str(libs_dir))
    
    # 直接导入 .pyd 文件
    import importlib.util
    spec = importlib.util.spec_from_file_location("DDS_All._native", pyd_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# 暴露模块内容
core = _load_platform_pyd()
globals().update({k: v for k, v in core.__dict__.items() if not k.startswith("_")})