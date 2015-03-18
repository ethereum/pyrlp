#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.md') as readme_file:
    readme = readme_file.read()

test_requirements = [
        'pytest'
]

setup(
    name='rlp',
    version='0.3.1',
    description="A package for encoding and decoding data in and from Recursive Length Prefix notation",
    long_description=readme,
    author="jnnk",
    author_email='jnnknnj@gmail.com',
    url='https://github.com/ethereum/pyrlp',
    packages=[
        'rlp', 'rlp.sedes'
    ],
    include_package_data=True,
    install_requires=[],
    license="MIT",
    zip_safe=False,
    keywords='rlp ethereum',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
