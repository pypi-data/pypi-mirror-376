"""
Setup configuration for the log generator tool.
"""

from setuptools import setup, find_packages
import os
import re

# Read version from __init__.py
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'log_generator', '__init__.py')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            content = f.read()
            version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
            if version_match:
                return version_match.group(1)
    return "1.0.0"

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Log Generator Tool - Automatic log generation for testing and development"

# Read requirements from requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove version comments and extra spaces
                    requirement = line.split('#')[0].strip()
                    if requirement:
                        requirements.append(requirement)
    return requirements

setup(
    name="log-generator-tool",
    version=get_version(),
    author="Log Generator Team",
    author_email="team@loggenerator.dev",
    description="Automatic log generation tool for log analyzer development and testing",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/log-generator/log-generator-tool",
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
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
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        "Topic :: Utilities",
        "Environment :: Console",
        "Natural Language :: English",
        "Natural Language :: Korean",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
            "pytest-asyncio>=0.21.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "isort>=5.12.0",
            "pre-commit>=3.3.0",
            "bandit>=1.7.5",
            "safety>=2.3.0",
        ],
        "network": [
            "requests>=2.31.0",
            "aiohttp>=3.8.0",
        ],
        "monitoring": [
            "psutil>=5.9.0",
            "prometheus-client>=0.17.0",
        ],
        "performance": [
            "uvloop>=0.17.0; sys_platform != 'win32'",
            "orjson>=3.9.0",
        ],
        "all": [
            "requests>=2.31.0",
            "aiohttp>=3.8.0",
            "psutil>=5.9.0",
            "prometheus-client>=0.17.0",
            "uvloop>=0.17.0; sys_platform != 'win32'",
            "orjson>=3.9.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "log-generator=log_generator.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "log_generator": [
            "patterns/*.yaml",
            "patterns/*.json",
            "config/*.yaml",
        ],
    },
    keywords="log generator testing development analysis nginx apache syslog",
    project_urls={
        "Bug Reports": "https://github.com/log-generator/log-generator-tool/issues",
        "Source": "https://github.com/log-generator/log-generator-tool",
        "Documentation": "https://log-generator-tool.readthedocs.io/",
    },
)