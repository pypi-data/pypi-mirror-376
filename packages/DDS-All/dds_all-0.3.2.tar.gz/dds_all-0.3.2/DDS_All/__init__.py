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
    if not pyd_file.exists():
        raise ImportError(f"找不到匹配的DDS_All.pyd (需要 {python_tag}-{platform_tag})")

    # 加载依赖项
    libs_dir = Path(__file__).parent / "libs"
    if libs_dir.exists():
        for dll in libs_dir.glob("*.dll"):
            try:
                ctypes.cdll.LoadLibrary(str(dll))
            except Exception as e:
                print(f"警告: 加载依赖 {dll.name} 失败: {e}")

    # 将.pyd所在目录加入Python路径
    sys.path.insert(0, str(bin_dir))
    
    # 尝试导入模块
    try:
        import DDS_All
        return DDS_All
    except ImportError as e:
        raise ImportError(f"无法导入DDS_All模块: {str(e)}")

# 主加载逻辑
try:
    _dds_module = load_dds()
    # 导出所有公共符号到当前命名空间
    globals().update(
        (name, getattr(_dds_module, name))
        for name in dir(_dds_module)
        if not name.startswith('_')
    )
except ImportError as e:
    print(f"致命错误: {e}")
    raise

if __name__ == "__main__":
    print("成功加载，导出符号:", [n for n in dir() if not n.startswith('_')])