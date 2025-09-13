# -*- coding: utf-8 -*-
import io
import re
from setuptools import setup, find_packages
import os
import sys

def get_version():
    """_version.py dosyasından versiyon numarasını al"""
    version_file = os.path.join(os.path.dirname(__file__), 'src', 'adnus', '_version.py')
    
    try:
        with open(version_file, 'r') as f:
            version_content = f.read()
            version_match = re.search(r"^__version__\s*=\s*['\"]([^'\"]*)['\"]", 
                                    version_content, re.M)
            if version_match:
                return version_match.group(1)
    except FileNotFoundError:
        pass
    
    # Fallback: __init__.py'den versiyon almayı dene
    init_file = os.path.join(os.path.dirname(__file__), 'src', 'adnus', '__init__.py')
    try:
        with open(init_file, 'r') as f:
            init_content = f.read()
            version_match = re.search(r"^__version__\s*=\s*['\"]([^'\"]*)['\"]", 
                                    init_content, re.M)
            if version_match:
                return version_match.group(1)
    except FileNotFoundError:
        pass
    
    # Hiçbiri yoksa varsayılan versiyon
    return "0.1.0"

setup(
    name="adnus",
    version=get_version(),
    description="adnus",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Mehmet Keçeci",
    maintainer="Mehmet Keçeci",
    author_email="mkececi@yaani.com",
    maintainer_email="mkececi@yaani.com",
    url="https://github.com/WhiteSymmetry/adnus",
    packages=find_packages(where='src'),  # src klasöründeki paketleri bul
    package_dir={'': 'src'},  # Paketlerin src altında olduğunu belirt
    package_data={
        "adnus": ["*.py", "*.pyi"],  # Tüm Python dosyalarını dahil et
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
