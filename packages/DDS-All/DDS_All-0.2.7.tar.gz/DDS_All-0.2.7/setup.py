import os
from setuptools import setup, find_packages
from setuptools.dist import Distribution

class BinaryDistribution(Distribution):
    def is_pure(self):
        return False
    def has_ext_modules(self):
        return True

setup(
    name="DDS_All",
    version="0.2.7",  # 确保版本号正确
    description="添加不同版本Python编译出的.pyd文件",
    author="JackyJia",
    packages=find_packages(),
    package_data={
        'DDS_All': [
            'bin/cp39-win_amd64/*.pyd',
            'bin/cp310-win_amd64/*.pyd',
            'bin/cp311-win_amd64/*.pyd',
            'bin/cp312-win_amd64/*.pyd',
            'bin/cp313-win_amd64/*.pyd',
            'libs/*.dll',
            'libs/*.lib',
        ],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.9, <=3.13",
    distclass=BinaryDistribution,
    options={
        'bdist_wheel': {
            'plat_name': 'win_amd64',
        }
    },
)