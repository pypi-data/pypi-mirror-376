"""
Setup script for pipeline-connector package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pipeline-connector",
    version="0.1.0",
    author="Krix Developer",
    author_email="developer@example.com",
    description="A powerful Python package for connecting and orchestrating multiple data pipelines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pipeline-connector",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typing-extensions>=4.0.0",
    ],
    keywords="pipeline data processing connector orchestration",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/pipeline-connector/issues",
        "Source": "https://github.com/yourusername/pipeline-connector",
    },
)