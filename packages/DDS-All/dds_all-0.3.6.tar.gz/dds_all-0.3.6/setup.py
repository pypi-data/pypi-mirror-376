import os
import sys
from setuptools import setup, find_packages
from setuptools.dist import Distribution

# 这是一个自定义的 Distribution 类，用于标记包为平台特定的
class BinaryDistribution(Distribution):
    def is_pure(self):
        return False
    def has_ext_modules(self):
        return True

def get_data_files():
    data_files = []
    # 添加 bin 目录下的 .pyd 文件
    bin_dir = os.path.join('DDS_All', 'bin')
    for root, dirs, files in os.walk(bin_dir):
        for file in files:
            if file.endswith('.pyd'):
                # 获取相对于 DDS_All 包的路径
                rel_path = os.path.relpath(os.path.join(root, file), 'DDS_All')
                data_files.append(rel_path.replace('\\', '/'))  # 确保使用 / 分隔符
    # 添加 libs 目录下的所有文件
    libs_dir = os.path.join('DDS_All', 'libs')
    for root, dirs, files in os.walk(libs_dir):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), 'DDS_All')
            data_files.append(rel_path.replace('\\', '/'))
    return data_files

setup(
    name="DDS_All",
    version="0.3.6",  
    author="JackyJia",
    author_email="213231181@seu.edu.cn",
    description="为适应不同Python版本的用户，编译了不同版本的.pyd文件可供使用",
    packages=find_packages(),
    package_data={
        'DDS_All': get_data_files(),
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires='>=3.9, <=3.13',
    distclass=BinaryDistribution,
)


def main():
    print(get_data_files())
   
if __name__ == '__main__':
    main()
