from os import name
import pathlib
from setuptools import setup

# The Directory containing this file
HERE = pathlib.Path(__file__).parent

# The readme file
README = (HERE / "README.md").read_text()

# setup()
setup(
    name="impgraph",
    version="1.0.0",
    description="A package for creating import graphs",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Utkarsh-Patel-13/import-grapher",
    author="Utkarsh Patel",
    author_email="utkarshhpatel13@gmail.com",
    license="MIT",
    packages=["impgraph"],
    include_package_data=True,
    install_requires=["pygraphviz", "stdlib-list", "toml"],
    entry_points={"console_scripts": ["impgraph=impgraph.__main__:main"]},
)
