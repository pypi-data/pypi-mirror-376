"""
Setup script for the Trasor.io Python SDK
"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="trasor-sdk",
    version="2.1.0",
    author="Trasor.io",
    author_email="support@trasor.io",
    description="Official Python SDK for Trasor.io trust infrastructure platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/trasor-io/trasor-python",
    project_urls={
        "Documentation": "https://docs.trasor.io/sdk/python",
        "API Reference": "https://docs.trasor.io/api",
        "Bug Tracker": "https://github.com/trasor-io/trasor-python/issues",
        "Homepage": "https://trasor.io",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",

        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8.1",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.812",
        ],
        "async": [
            "aiohttp>=3.8.0",
        ],
        "crewai": [
            "crewai>=0.1.0",
        ],
        "langchain": [
            "langchain>=0.0.200",
        ],
        "all": [
            "aiohttp>=3.8.0",
            "crewai>=0.1.0",
            "langchain>=0.0.200",
        ],
    },
    keywords="audit logging security ai agents blockchain verification trust infrastructure",
    license="MIT",
    zip_safe=False,
)