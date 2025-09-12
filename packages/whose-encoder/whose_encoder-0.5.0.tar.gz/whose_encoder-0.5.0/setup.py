from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="whose_encoder",                  # 你要发布的包名，pip install fruit_encoder
    version="0.5.0",                       # 版本号，每次更新要改版本！！
    author="Ruo1.-_1",
    author_email="213243435@sey.edu.cn",
    description="一个将文件编码为'苹果'/'安卓'文本，以及解码还原的工具",
    long_description=long_description,     # 来自 README.md
    long_description_content_type="text/markdown",
    packages=find_packages(),              # 自动发现所有包，比如 fruit_encoder/
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # 或其他协议
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',               # 支持的 Python 版本
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'encoder=whose_encoder.encoder:encoder',   # 格式：命令名=包名.模块名:函数名
            'decoder=whose_encoder.decoder:decoder',
        ],
    },
)