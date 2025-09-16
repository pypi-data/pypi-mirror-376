from setuptools import setup, find_packages
from setuptools.command.install import install
import os, importlib.util

def run_postinstall():
    # marker to ensure it only fires once per user
    marker = os.path.expanduser("~/.amd_taichi_postinstall_ran")
    try:
        fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    except FileExistsError:
        return  # already ran

    module_path = os.path.join(os.path.dirname(__file__), "amd_taichi", "_postinstall.py")
    spec = importlib.util.spec_from_file_location("amd_taichi._postinstall", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.run()

class PostInstall(install):
    def run(self):
        # perform the normal install steps
        super().run()
        # now run our post-install hook
        run_postinstall()

setup(
    name="amd-taichi",
    version="0.1.10",
    author="David",
    description="Experimental bindings for distributed collective communication workflows.",
    long_description="""...""",
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
