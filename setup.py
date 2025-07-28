from setuptools import setup, find_packages

setup(
    name="sage-learning",
    version="0.1.0",
    description="Scholar's Adaptive Growth Engine - An adaptive learning assistant system",
    author="SAGE Team",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "sage=sage.cli.main:cli",
        ],
    },
    python_requires=">=3.8",
)