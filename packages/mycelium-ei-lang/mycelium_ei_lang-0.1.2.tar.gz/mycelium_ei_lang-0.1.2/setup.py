#!/usr/bin/env python3
"""
Setup script for Mycelium-EI-Lang
Copyright (c) 2024 Michael Benjamin Crowe. All Rights Reserved.
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mycelium-ei-lang",
    version="0.1.2",
    author="Michael Benjamin Crowe",
    author_email="michael.benjamin.crowe@gmail.com",
    description="World's first bio-inspired programming language with quantum computing and ecological intelligence",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MichaelCrowe11/mycelium-ei-lang",
    project_urls={
        "Bug Tracker": "https://github.com/MichaelCrowe11/mycelium-ei-lang/issues",
        "Documentation": "https://mycelium-ei-lang.readthedocs.io",
        "Source Code": "https://github.com/MichaelCrowe11/mycelium-ei-lang",
    },
    packages=find_packages(exclude=["tests*", "examples*", "docs*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Interpreters",
        "Topic :: Software Development :: Debuggers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "numba>=0.54.0",
        "lz4>=3.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "mypy>=0.950",
            "pylint>=2.14.0",
        ],
        "gpu": [
            "cupy-cuda11x>=10.0.0",  # For CUDA 11.x
        ],
        "docs": [
            "sphinx>=4.5.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mycelium=mycelium_dev_tools:main",
            "myc=mycelium_dev_tools:main",
            "mycelium-repl=tools.repl.mycelium_repl:main",
            "mycelium-lint=tools.linter.mycelium_linter:main",
            "mycelium-debug=tools.debugger.mycelium_debugger:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mycelium_ei": ["*.md", "examples/*.myc"],
    },
    keywords=[
        "bio-inspired",
        "quantum-computing", 
        "ecological-intelligence",
        "mycelium-networks",
        "genetic-algorithms",
        "swarm-intelligence",
        "cultivation-monitoring",
        "sensor-networks",
        "adaptive-systems",
        "distributed-computing",
        "environmental-modeling",
        "biological-simulation",
        "quantum-hybrid",
        "compiler",
        "interpreter",
        "repl",
        "debugger",
        "linter"
    ],
    zip_safe=False,
)