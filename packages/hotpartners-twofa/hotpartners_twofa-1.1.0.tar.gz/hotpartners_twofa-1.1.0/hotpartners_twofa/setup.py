#!/usr/bin/env python3
"""
HotPartners 2FA Package Setup
"""

import os

from setuptools import find_packages, setup


# README 파일 읽기
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "HotPartners 2FA Package"

# requirements.txt 읽기
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="hotpartners-twofa",
    version="1.0.0",
    author="HotPartners Team",
    author_email="dev@hotpartners.com",
    description="Two-Factor Authentication (2FA) package for HotPartners",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/hotpartners/hotpartners-twofa",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security",
        "Topic :: System :: Systems Administration :: Authentication",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    include_package_data=True,
    package_data={
        "hotpartners_twofa": [
            "sql/*.sql",
            "migrations/*.sql",
            "*.md",
        ],
    },
    entry_points={
        "console_scripts": [
            "hotpartners-twofa-setup=hotpartners_twofa.cli:setup_schema",
        ],
    },
    keywords="2fa two-factor authentication otp totp qr-code security",
    project_urls={
        "Bug Reports": "https://github.com/hotpartners/hotpartners-twofa/issues",
        "Source": "https://github.com/hotpartners/hotpartners-twofa",
        "Documentation": "https://hotpartners-twofa.readthedocs.io/",
    },
)
