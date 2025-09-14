from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as fh:
            return fh.read()
    return "A simple image compression tool."

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    return ["numpy", "scipy", "matplotlib", "Pillow"]

setup(
    # With PEP 621 metadata in pyproject.toml, setuptools reads the
    # name, version, author, and other metadata from there during builds.
    # Keeping setup() minimal avoids duplicating version info.
    name="smlr",
    author="Jack Douglas",
    description="A simple image compression tool.",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/smlr",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "smlr=smlr.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
