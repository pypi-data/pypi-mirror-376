import os
import sys
import ctypes
from pathlib import Path

def load_dds():
    # 获取当前Python版本对应的编译目录
    python_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    platform_tag = "win_amd64" if sys.maxsize > 2**32 else "win32"
    bin_dir = Path(__file__).parent / "bin" / f"{python_tag}-{platform_tag}"
    
    # 检查.pyd文件是否存在
    pyd_file = bin_dir / "DDS_All.pyd"    
    print(f"[DEBUG] Python版本: {python_tag}")
    print(f"[DEBUG] 平台: {platform_tag}")
    print(f"[DEBUG] .pyd 文件路径: {pyd_file}")
    print(f"[DEBUG] .pyd 文件是否存在: {pyd_file.exists()}")

    if not pyd_file.exists():
        raise ImportError(f"找不到匹配的DDS_All.pyd (需要 {python_tag}-{platform_tag})")

    # 加载依赖项
    libs_dir = Path(__file__).parent / "libs"
    if libs_dir.exists():
        for dll in libs_dir.glob("*.dll"):
            try:
                ctypes.cdll.LoadLibrary(str(dll))
                print(f"[DEBUG] 成功加载依赖: {dll.name}")
            except Exception as e:
                print(f"警告: 加载依赖 {dll.name} 失败: {e}")

    # 直接从文件路径加载 .pyd
    import importlib.util
    spec = importlib.util.spec_from_file_location("DDS_All", str(pyd_file))
    dds_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dds_module)
    print("[DEBUG] 成功导入 DDS_All.pyd")

    return dds_module            


    
try:
        print("[DEBUG] 正在加载 DDS_All 模块...")
        _dds_module = load_dds()
        # 导出所有公共符号到当前命名空间
        globals().update(
            (name, getattr(_dds_module, name))
            for name in dir(_dds_module)
            if not name.startswith('_')
        )
        # 标记已加载
        globals()['_dds_loaded'] = True
        __all__ = [n for n in dir() if not n.startswith("_")]
        
        
except ImportError as e:
        print(f"致命错误: {e}")
        raise