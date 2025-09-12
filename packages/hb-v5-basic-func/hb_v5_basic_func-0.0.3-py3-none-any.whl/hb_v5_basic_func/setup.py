#!/usr/bin/env python3
"""
Setup script for hb_v5_basic_func package
"""

from setuptools import setup, find_packages
import os

# Get the directory containing this setup.py
here = os.path.abspath(os.path.dirname(__file__))

setup(
    name="hb_v5_basic_func",
    version="0.0.3",
    author="Unknown",
    author_email="unknown@example.com",
    description="Basic function package with Pyarmor protection (v5)",
    long_description="Enhanced basic function package with Pyarmor protection and runtime support",
    long_description_content_type="text/plain",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.6",
    include_package_data=True,
    package_data={
        "hb_v5_basic_func": [
            "*.py",
            "*.so",
        ],
        "hb_v5_basic_func.pyarmor_runtime_000000": [
            "*.py",
            "*.so",
        ],
    },
    zip_safe=False,  # Pyarmor protection requires files to be extracted
)
