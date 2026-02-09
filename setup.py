#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script for IEC60870-5-101/104 Test Tool
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="iec60870-test",
    version="0.1.0",
    author="zhanggy",
    description="Test tool for IEC60870-5-101/104 protocols",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zhanggy/IEC60870-5Test",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Networking",
    ],
    python_requires='>=3.6',
    install_requires=[
        'pyserial>=3.5',
    ],
    entry_points={
        'console_scripts': [
            'iec60870-test=iec60870.cli:main',
        ],
    },
)
