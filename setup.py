#!/usr/bin/env python
"""
JiraJitsu - JIRA to JitBit Migration Tool
"""

from setuptools import setup, find_packages
import os

# Read the version from version.py
version = {}
with open("jirajitsu/version.py") as fp:
    exec(fp.read(), version)

# Read the long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="jirajitsu",
    version=version["__version__"],
    author="JiraJitsu Contributors",
    author_email="",
    description="A Python tool for migrating issue tickets from JIRA to JitBit helpdesk",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.12.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "pylint>=3.0.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "jirajitsu=jirajitsu.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "jirajitsu": ["py.typed"],
    },
    zip_safe=False,
    keywords="jira jitbit migration helpdesk issue-tracking",
)
