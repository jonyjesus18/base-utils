from setuptools import setup, find_packages

setup(
    name="base-utils",
    version="0.1.0",
    author="João Jesus",
    author_email="joaomj1800@example.com",
    description="Utility functions and helpers for base projects.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jonyjesus18/base-utils",
    packages=find_packages(),
    python_requires=">=3.11",
    include_package_data=True,
    package_data={
        "": ["*.csv", "*.json"],  # include csv/json files inside all packages
    },
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=open("requirements.txt", encoding="utf-8").read().splitlines(),
    entry_points={
        "console_scripts": [
        ],
    },
)
