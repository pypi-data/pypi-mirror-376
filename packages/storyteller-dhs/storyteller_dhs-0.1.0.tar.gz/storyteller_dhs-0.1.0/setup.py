from setuptools import setup, find_packages
from _version import __version__

setup(
    name="storyteller-dhs",
    version=__version__,
    author="kofiyatech",
    author_email="kofiya.technologies@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "storyteller": [
            "metadata.yaml",
            "assets/*",
            "templates/*",
        ],
    },
    install_requires=[
        "click",
        "datasette",
        "sqlite-utils",
        "Jinja2",
        "pandas",
    ],  # TODO - Update for new dependencies
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "storyteller=storyteller.cli:storyteller",
            "enable_fts=storyteller.cli:enable_fts",
        ],  # TODO - Update for new CLI commands
    },
)
