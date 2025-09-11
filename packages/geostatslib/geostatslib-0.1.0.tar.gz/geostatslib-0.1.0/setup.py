from setuptools import setup, find_packages

setup(
    name="geostatslib",  # 包名，和 PyPI 上一致
    version="0.1.0",     # 版本号，确保每次发布都递增
    author="MZ Han",  # 作者
    author_email="hanmz1106@gmail.com",  # 作者邮箱
    description="A lightweight geostatistics library",  # 简短描述
    long_description=open('README.md').read(),  # 长描述，通常从 README.md 中读取
    long_description_content_type="text/markdown",  # 文件类型
    url="https://github.com/han1399013493/Geostatslib",  # 项目地址
    packages=find_packages(),  # 自动发现包
    install_requires=[  # 依赖的第三方库
        "pandas",
        "numpy",
    ]
)
