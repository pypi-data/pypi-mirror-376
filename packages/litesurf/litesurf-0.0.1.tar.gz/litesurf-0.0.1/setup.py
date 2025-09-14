from setuptools import setup, find_packages
from pathlib import Path

# Base directory of this file
BASE_DIR = Path(__file__).resolve().parent


# Helper function to read requirements from a file
def read_requirements(filename):
    path = BASE_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


# Read README.md for long description
long_description = (BASE_DIR / "README.md").read_text(encoding="utf-8")

# Optional test/dev requirements
default_requires = read_requirements("requirements/requirements.txt")
test_requires = read_requirements("requirements/requirements_test.txt")
dev_requires = read_requirements("requirements/requirements_dev.txt")
docs_requires = read_requirements("requirements/requirements_docs.txt")

setup(
    name="litesurf",
    version="0.0.1",
    author="Ishan Bhat",
    author_email="ishan2003bhat@gmail.com",
    description="A simple CLI-based web browser and HTML parser",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bhatishan2003/litesurf",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=default_requires,
    extras_require={"test": test_requires, "dev": dev_requires, "docs": docs_requires ,"all": test_requires + dev_requires + docs_requires},
    entry_points={
        "console_scripts": [
            "litesurf=litesurf.cli:cli",
        ],
    },
    include_package_data=True,
)
