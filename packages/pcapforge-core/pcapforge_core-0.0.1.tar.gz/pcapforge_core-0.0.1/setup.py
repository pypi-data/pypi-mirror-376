from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pcapforge-core",
    version="0.0.1",
    author="Colin Knizek",
    author_email="pcapforge@users.noreply.github.com",
    description="Fast packet capture processor and feature extractor - Core library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pcapforge/pcapforge",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[],
    keywords="pcap packet network analysis capture pcapng",
)