from setuptools import setup, find_packages

setup(
    name="hello-world-test-pkg",
    version="0.1.0",
    author="Ryan Vaughan",
    author_email="ryan.vaughan@wnco.com",
    description="A simple hello world package for testing PyPI uploads",
    packages=find_packages(),
    python_requires=">=3.6",
    license="BSD-3-Clause",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
)