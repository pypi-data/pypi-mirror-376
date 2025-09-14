# setup.py
from setuptools import setup, find_packages
import codecs
import os

# 读取版本号
here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(here, "方圆", "__init__.py"), encoding='utf-8') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip('"\'')
            break

# 读取README
with codecs.open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="fangyuan-gui",
    version="1.1.0",
    packages=find_packages(),  # 这会自动找到「方圆」文件夹
    # 或者显式指定：
    # packages=['方圆'],
    # package_dir={'方圆': '方圆'},
    install_requires=["PySide6>=6.0.0"],
    author="方圆开发团队",
    description="使用自然语言创建GUI的Python库",
)