from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="x6c1",
    version="3.0.0",
    author="celestine1729",
    author_email="celestine1729@proton.me",
    description="A comprehensive tool for converting between hexadecimal representations and their corresponding text or numeric values",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/celestine1729/x6c1",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "x6c1=x6c1.cli:main",
        ],
    },
    keywords="hex, converter, translator, text, number, file",
)
