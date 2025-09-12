from setuptools import setup, find_packages
from Cython.Build import cythonize

setup(
    name="omga-cli",
    version="0.1.0",
    description="A CLI tool for code checking, explanation, and AI assistance",
    author="Pouria Hosseini",
    author_email="PouriaHosseini@outlook.com",
    packages=find_packages(),  # core package رو پیدا می‌کنه
    ext_modules=cythonize(
        "core/*.py",  # همه فایل‌های core کامپایل میشن
        compiler_directives={"language_level": "3"}
    ),
    include_package_data=True,  # README و LICENSE روی PyPI بمونن
    install_requires=[
        "click>=8.0.0",
        "prompt_toolkit>=3.0.0",
        "requests>=2.28.0",
        "rich>=13.0.0"
    ],
    entry_points={
        "console_scripts": [
            "omga-cli=core.cli:main"  # دستور CLI
        ]
    },
)
