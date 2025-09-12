"""
Setup configuration for shrutiAI SDK
"""

from setuptools import setup, find_packages

# Read the README file for long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "A Python SDK for interacting with shrutiAI API"

setup(
    name="shrutiAI-sdk",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python SDK for interacting with shrutiAI API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/shrutiAI-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
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
    keywords="api sdk client rest",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/shrutiAI-sdk/issues",
        "Source": "https://github.com/yourusername/shrutiAI-sdk",
        "Documentation": "https://shrutiAI-sdk.readthedocs.io/",
    },
)
