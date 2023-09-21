#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import (
    setup,
    find_packages,
)

extras_require = {
    'test': [
        "pytest>=6.2.5,<7",
        "pytest-xdist>=2.4.0",
        "hypothesis==5.19.0",
    ],
    'lint': [
        "flake8==6.0.0",  # flake8 claims semver but adds new warnings at minor releases, leave it pinned.
        "flake8-bugbear==23.3.23",  # flake8-bugbear does not follow semver, leave it pinned.
        "isort>=5.10.1",
        "mypy==0.971",  # mypy does not follow semver, leave it pinned.
        "pydocstyle>=6.0.0",
        "black>=23",
    ],
    'docs': [
        "sphinx>=6.0.0",
        "sphinx_rtd_theme>=1.0.0",
        "towncrier>=21,<22",
    ],
    'dev': [
        "bumpversion>=0.5.3",
        "pytest-watch>=4.1.0",
        "tox>=4.0.0",
        "build>=0.9.0",
        "wheel",
        "twine",
        "ipython",
    ],
    'rust-backend': [
        "rusty-rlp>=0.2.1, <0.3"
    ]
}


extras_require['dev'] = (
    extras_require['dev'] +
    extras_require['test'] +
    extras_require['lint'] +
    extras_require['docs']
)


with open("./README.md") as readme:
    long_description = readme.read()


setup(
    name='rlp',
    # *IMPORTANT*: Don't manually change the version here. See README for more.
    version='3.0.0',
    description="A package for Recursive Length Prefix encoding and decoding",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="jnnk",
    author_email='jnnknnj@gmail.com',
    url='https://github.com/ethereum/pyrlp',
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    install_requires=[
        "eth-utils>=2",
    ],
    extras_require=extras_require,
    py_modules=["<MODULE_NAME>"],
    license="MIT",
    zip_safe=False,
    keywords='rlp ethereum',
    classifiers=[
        "Development Status :: 3 - Alpha",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
