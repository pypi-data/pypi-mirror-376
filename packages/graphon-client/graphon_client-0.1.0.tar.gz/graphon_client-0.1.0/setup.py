from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="graphon-client",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python client library for the Graphon API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/graphon-client",
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
    install_requires=[
        "requests>=2.25.0",
    ],
    keywords="graphon api client video indexing",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/graphon-client/issues",
        "Source": "https://github.com/yourusername/graphon-client",
    },
)
