from setuptools import setup, find_packages

setup(
    name="scm203lab267101691",               # Must be unique on PyPI!
    version="0.1.1",                # Follow semantic versioning
    description="Roots of equation and Differential equation",   
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="khing",
    author_email="anchitha2005@gmail.com",
    url="https://github.com/khing2005/scm203lab267101691",  # optional
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[],
)