#!/usr/bin/env python3
"""
setup.py for plananalyze - PostgreSQL EXPLAIN Plan Analyzer
"""

import os

from setuptools import find_packages, setup


# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "PostgreSQL EXPLAIN Plan Analyzer"


# Read requirements
def read_requirements(filename):
    req_path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(req_path):
        with open(req_path, "r") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return []


setup(
    name="plananalyze",
    version="0.1.0",
    author="Guja Lomsadze",
    author_email="lomsadze.guja@gmail.com",
    description="PostgreSQL EXPLAIN Plan Analyzer - Extract insights from execution plans",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/GujaLomsadze/PlanAnalyzer",
    # Package configuration
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
    ],
    # Python version requirement
    python_requires=">=3.8",
    # Dependencies
    install_requires=read_requirements("requirements.txt"),
    # Optional dependencies for development
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "docs": ["sphinx", "sphinx-rtd-theme", "myst-parser"],
        "test": ["pytest", "pytest-cov", "pytest-mock"],
    },
    # Entry points for command-line tools
    entry_points={
        "console_scripts": [
            "plananalyze=plananalyze.cli:main",
            "pa=plananalyze.cli:main",  # Short alias
        ],
    },
    # Include additional files
    include_package_data=True,
    # Keywords for PyPI
    keywords=[
        "postgresql",
        "explain",
        "query",
        "performance",
        "database",
        "analysis",
        "optimizer",
        "sql",
        "plan",
        "bottleneck",
    ],
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/GujaLomsadze/PlanAnalyzer/issues",
        "Source": "https://github.com/GujaLomsadze/PlanAnalyzer",
    },
)
