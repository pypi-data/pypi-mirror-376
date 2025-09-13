#!/usr/bin/env python3
"""
TOXO - World's First No-Code LLM Training Platform
Public Python Package for .toxo file support

This package allows users to seamlessly use .toxo files created on the TOXO platform.
Simply install with: pip install toxo
Then use: from toxo import ToxoLayer; layer = ToxoLayer.load('your_model.toxo')
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "TOXO - No-Code LLM Training Platform"

# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="toxo",
    version="1.0.9",
    author="ToxoTune",
    author_email="support@toxotune.com",
    description="TOXO Python Library - Smart Layer Platform that converts ANY black-box LLM (GPT, Gemini, Claude) into Context Augmented Language Models (CALM). No LLM retraining needed - just attach .toxo layers for instant domain expertise. Revolutionary AI enhancement technology.",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://toxotune.github.io/toxo-docs",
    project_urls={
        "Homepage": "https://toxotune.github.io/toxo-docs",
        "Documentation": "https://toxotune.github.io/toxo-docs",
        "Source": "https://github.com/toxotune/toxo-docs",
        "Bug Reports": "https://github.com/toxotune/toxo-docs/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Education",
        "Topic :: Office/Business",
    ],
    python_requires=">=3.8",
    install_requires=[
        "google-generativeai>=0.1.0rc1",
        "numpy",
        "requests>=2.25.0",
        "tqdm>=4.60.0",
        "pydantic>=1.8.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.900",
        ],
        "openai": [
            "openai>=1.0.0",
        ],
        "claude": [
            "anthropic>=0.7.0",
        ],
        "full": [
            "openai>=1.0.0",
            "anthropic>=0.7.0",
            "chromadb>=0.4.0",
            "sentence-transformers>=2.2.0",
            "scikit-learn>=1.0.0",
            "pandas>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "toxo=toxo.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="toxo, toxo python library, smart layer, calm, context augmented language models, black-box llm enhancement, llm conversion, domain expert ai, toxo layer, python library, ai augmentation, llm enhancement, no llm retraining, toxo python package, ai layer training, toxo ai, toxo library, ai smart layers, llm memory, ai enhancement",
)
