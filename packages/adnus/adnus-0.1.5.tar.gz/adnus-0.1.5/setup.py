# -*- coding: utf-8 -*-
import io
import re
from setuptools import setup, find_packages
import sys


setup(
    name="adnus",
    version="0.1.5",
    description="adnus",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Mehmet Keçeci",
    maintainer="Mehmet Keçeci",
    author_email="mkececi@yaani.com",
    maintainer_email="mkececi@yaani.com",
    url="https://github.com/WhiteSymmetry/adnus",
    packages=find_packages(),  # 'adnus' klasörünü otomatik bulur
    package_data={
        "adnus": ["__init__.py", "_version.py"]  # Gerekli dosyaları dahil et
    },
    install_requires=[
        "hypercomplex",

    ],
    extras_require={
        'test': [
            "pytest",
            "pytest-cov",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.10',
    license="MIT",
)
