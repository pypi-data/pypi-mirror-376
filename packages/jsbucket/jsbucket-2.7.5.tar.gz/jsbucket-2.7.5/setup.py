#!/usr/bin/env python3
"""
Setup script for JSBucket.
Modern configuration is in pyproject.toml, but this provides compatibility.
"""

from setuptools import setup, find_packages

# Read the version from __init__.py
def get_version():
    with open("jsbucket/__init__.py", "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split('"')[1]
    return "2.0.0"

# Read the README for long description
def get_long_description():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

setup(
    name="jsbucket",
    version=get_version(),
    author="Mortaza Behesti Al Saeed",
    author_email="saeed.ctf@gmail.com",
    description="A tool to discover S3 buckets from subdomains by analyzing JavaScript files.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/saeed0xf/jsbucket",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "tqdm>=4.60.0", 
        "rich>=10.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "jsbucket=jsbucket.core:main",
        ],
    },
    keywords=["security", "s3", "bucket", "discovery", "javascript", "subdomain", "bugbounty", "pentest"],
)