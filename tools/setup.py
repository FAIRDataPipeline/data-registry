#!/usr/bin/env python

from setuptools import setup

setup(
    name="component-checker",
    version="0.1.0",
    description="Data Registry Component Checker",
    author="Jonathan Hollocombe",
    author_email="Jonathan.Hollocombe@ukaea.uk",
    url="https://github.com/FAIRDataPipeline/data-registry",
    py_modules=["check_components"],
    install_requires=[
        "h5py (>=2.10.0)",
        "toml (>=0.10.1)",
        "requests (>=2.23.0)",
    ],
    entry_points="""
        [console_scripts]
        check_components=check_components:main
    """,
)
