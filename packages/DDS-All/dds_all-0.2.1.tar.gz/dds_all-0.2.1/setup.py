from setuptools import setup, find_packages
import os

# 递归收集bin/和libs/目录下的所有二进制文件
def get_binaries():
    data_files = []
    
    # 收集所有平台的.pyd文件
    bin_dir = os.path.join("DDS_All", "bin")
    for root, _, files in os.walk(bin_dir):
        for file in files:
            if file.endswith(('.pyd', '.dll')):
                rel_path = os.path.relpath(root, "DDS_All")
                data_files.append(os.path.join(rel_path, file))
    
    # 收集libs目录下的所有.lib文件
    libs_dir = os.path.join("DDS_All", "libs")
    if os.path.exists(libs_dir):
        for root, _, files in os.walk(libs_dir):
            for file in files:
                if file.endswith('.lib'):
                    rel_path = os.path.relpath(root, "DDS_All")
                    data_files.append(os.path.join(rel_path, file))
    
    return data_files

setup(
    name="DDS_All",
    version="0.2.1",  # 更新你的版本号
    author="JackyJia",
    description="为解决不同版本Python的兼容性问题，提供多版本的预编译二进制文件",
    packages=find_packages(),
    package_data={
        "DDS_All": get_binaries() + ["libs/*.lib"],  # 包含所有二进制文件
    },
    include_package_data=True,  # 确保包含非Python文件
    python_requires=">=3.9, <=3.13",   # 设置支持的Python版本范围
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
)