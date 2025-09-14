from setuptools import setup, find_packages
import codecs
import os

# 读取README.md文件内容作为长描述
here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# 读取requirements.txt文件获取依赖
with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="xml2gui",
    version="1.0.0",
    author="huang1057",
    author_email="your.email@example.com",  # 请替换为您的邮箱
    description="A powerful framework for creating GUI applications using XML files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitee.com/ghhuang1057/xml2-gui",  # 项目主页
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: Software Development :: Code Generators",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "xml2gui=xml2gui_build:main",  # 将xml2gui_build.py作为命令行工具
        ],
    },
    include_package_data=True,
    package_data={
        "xml2gui": ["*.xml"],  # 包含示例XML文件
    },
    keywords="xml gui pyqt pyqt5 qt python ui designer",
    project_urls={
        "Documentation": "https://gitee.com/ghhuang1057/xml2-gui/blob/master/USER_GUIDE.md",
        "Source": "https://gitee.com/ghhuang1057/xml2-gui",
        "Bug Reports": "https://gitee.com/ghhuang1057/xml2-gui/issues",
    },
)