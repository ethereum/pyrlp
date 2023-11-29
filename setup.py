#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import (
    find_packages,
    setup,
)

extras_require = {
    "dev": [
        "build>=0.9.0",
        "bumpversion>=0.5.3",
        "ipython",
        "pre-commit>=3.4.0",
        "tox>=4.0.0",
        "twine",
        "wheel",
    ],
    "docs": [
        "sphinx>=6.0.0",
        "sphinx_rtd_theme>=1.0.0",
        "towncrier>=21,<22",
    ],
    "test": [
        "pytest>=7.0.0",
        "pytest-xdist>=2.4.0",
        "hypothesis==5.19.0",
    ],
    "rust-backend": ["rusty-rlp>=0.2.1, <0.3"],
}


extras_require["dev"] = (
    extras_require["dev"] + extras_require["docs"] + extras_require["test"]
)

with open("./README.md") as readme:
    long_description = readme.read()

setup(
    name="rlp",
    # *IMPORTANT*: Don't manually change the version here. See README for more.
    version="4.0.0",
    description="""rlp: A package for Recursive Length Prefix encoding and decoding""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="jnnk",
    author_email="jnnknnj@gmail.com",
    url="https://github.com/ethereum/pyrlp",
    include_package_data=True,
    install_requires=[
        "eth-utils>=2",
    ],
    python_requires=">=3.8, <4",
    extras_require=extras_require,
    py_modules=["rlp"],
    license="MIT",
    zip_safe=False,
    keywords="rlp ethereum",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
