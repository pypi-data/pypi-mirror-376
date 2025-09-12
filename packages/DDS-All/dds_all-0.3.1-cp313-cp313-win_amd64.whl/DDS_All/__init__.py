import os
import sys
import platform
from pathlib import Path

def load_pyd():
    python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == 'windows' and machine == 'amd64':
        pyd_path = Path(__file__).parent / 'bin' / f'{python_version}-win_amd64' / 'DDS_All.pyd'
        if pyd_path.exists():
            import ctypes
            # 加载依赖的 DLL 文件
            libs_dir = Path(__file__).parent / 'libs'
            for dll in libs_dir.glob('*.dll'):
                ctypes.cdll.LoadLibrary(str(dll))
            # 加载主 PYD 文件
            return ctypes.cdll.LoadLibrary(str(pyd_path))
    
    raise ImportError(f"Could not find compatible DDS_All.pyd for Python {python_version} on {system}-{machine}")

# 加载 PYD 文件
DDS_All = load_pyd()

'''
if __name__ == "__main__":
    # 自测代码
    try:
        loaded_dll = load_pyd()
        print(f"✅ 成功加载 DDS_All.pyd: {loaded_dll}")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
'''