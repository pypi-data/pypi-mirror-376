from setuptools import setup, find_packages
import sys
import os

# Only run post-install during actual installation, not during setup
if 'install' in sys.argv:
    import importlib.util
    module_path = os.path.join(os.path.dirname(__file__), "amd_taichi", "_postinstall.py")
    spec = importlib.util.spec_from_file_location("amd_taichi._postinstall", module_path)
    postinstall = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(postinstall)
    postinstall.run()

setup(
    name="amd-taichi",
    version="0.1.7",
    author="David",
    description="Experimental bindings for distributed collective communication workflows.",
    long_description=""" This package provides experimental bindings for distributed collective communication workflows in Python.
    It aims to simplify the development of applications that require efficient communication between multiple processes or devices.
    """,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Software Development :: Libraries",
    ],
)
