from setuptools import setup
import sys
import os


setup(
    name="amd-taichi",
    version="1.0.0",
    author="David",
    description="Experimental bindings for distributed collective communication workflows.",
    long_description=""" This package provides experimental bindings for distributed collective communication workflows in Python.
    It aims to simplify the development of applications that require efficient communication between multiple processes or devices.
    """,
    long_description_content_type="text/markdown",
    include_package_data=True,
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Software Development :: Libraries",
    ],
)
