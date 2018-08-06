#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import (
    setup,
    find_packages,
)


extras_require = {
    'test': [
        "pytest==3.3.2",
        "tox>=2.9.1,<3",
        "hypothesis==3.56.5",
    ],
    'lint': [
        "flake8==3.4.1",
    ],
    'doc': [
        "Sphinx>=1.6.5,<2",
        "sphinx_rtd_theme>=0.1.9",
    ],
    'dev': [
        "bumpversion>=0.5.3,<1",
        "pytest-xdist",
        "pytest-watch>=4.1.0,<5",
        "wheel",
        "ipython",
        "twine",
    ],
}


extras_require['dev'] = (
    extras_require['dev'] +
    extras_require['test'] +
    extras_require['lint'] +
    extras_require['doc']
)


setup(
    name='rlp',
    # *IMPORTANT*: Don't manually change the version here. See README for more.
    version='1.0.2',
    description="A package for Recursive Length Prefix encoding and decoding",
    long_description_markdown_filename='README.md',
    author="jnnk",
    author_email='jnnknnj@gmail.com',
    url='https://github.com/ethereum/pyrlp',
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    setup_requires=['setuptools-markdown'],
    install_requires=[
        "eth-utils>=1.0.2,<2",
    ],
    extras_require=extras_require,
    license="MIT",
    zip_safe=False,
    keywords='rlp ethereum',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
