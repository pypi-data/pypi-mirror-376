from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="allinonetoolbyMineMish",
    version="0.0.5",
    author="MineMish",
    author_email="your.email@example.com",
    description="A collection of useful mini functions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MineMish/all-in-one-tools",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "Pillow>=8.0.0",
        "requests>=2.25.0",
    ],
)