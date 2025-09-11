#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# 读取 README 文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取 requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="emutrader",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python library for quantitative trading simulation and backtesting",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/EmuTrader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
        "docs": [
            "sphinx",
            "sphinx-rtd-theme",
        ],
    },
    keywords="quantitative trading, backtesting, simulation, finance, algorithmic trading",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/EmuTrader/issues",
        "Source": "https://github.com/yourusername/EmuTrader",
        "Documentation": "https://emutrader.readthedocs.io/",
    },
)
