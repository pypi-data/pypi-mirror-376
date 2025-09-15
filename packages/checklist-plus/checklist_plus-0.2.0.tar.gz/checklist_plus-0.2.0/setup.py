import os
import re
import sys

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install


# Handle the notebook extension installation
def enable_visual_interface():
    try:
        import notebook
        notebook.nbextensions.install_nbextension_python(
            "checklist_plus.viewer", user=True, overwrite=True)
        notebook.nbextensions.enable_nbextension_python(
            "checklist_plus.viewer")
    except ImportError:
        print("Warning: notebook not installed, skipping visual interface setup")

def enable_visual_interface_shell_cmd(direction):
    sys.path.append(direction)
    enable_visual_interface()

class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        self.execute(enable_visual_interface_shell_cmd, (self.install_lib,), msg="Setting up visual interface")

class PostInstallCommand(install):
    """Post-installation for install mode."""
    def run(self):
        install.run(self)
        self.execute(enable_visual_interface_shell_cmd, (self.install_lib,), msg="Setting up visual interface")

# Get package name from environment or default
pkg_name = os.getenv("PKG_NAME", "checklist_plus")

# Read version from pyproject.toml
def get_version():
    try:
        with open("pyproject.toml") as f:
            content = f.read()
            version_match = re.search(r'^version\s*=\s*"(.*?)"', content, re.M)
            if version_match:
                return version_match.group(1)
    except FileNotFoundError:
        raise RuntimeError("pyproject.toml not found")
    except Exception as e:
        raise RuntimeError(f"Error reading pyproject.toml: {e}")

setup(
    name=pkg_name,
    version=get_version(),
    packages=find_packages(exclude=['js', 'node_modules', 'tests']),
    url=f"https://github.com/cowana-ai/checklist-plus",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Chingis Owana",
    author_email="your.email@example.com",
    python_requires=">=3.9",
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    # All other metadata now comes from pyproject.toml
)
