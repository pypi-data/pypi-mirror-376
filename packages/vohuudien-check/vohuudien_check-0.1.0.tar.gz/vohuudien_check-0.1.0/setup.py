from setuptools import setup, find_packages

setup(
    name="vohuudien-check",
    version="0.1.0",
    packages=find_packages(),
    description="Kiểm tra và chuẩn hóa tên người dùng (username) theo quy tắc PyPI",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Võ Hữu Điền",
    url="https://github.com/<username>/vohuudien-check",
    license="MIT",
)
