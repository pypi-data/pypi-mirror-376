from setuptools import setup, find_packages

setup(
    name="scm203lab267101691",               # Must be unique on PyPI!
    version="0.1.0",                # Follow semantic versioning
    description="This is my first project.To find root of function using bisection method and newton method.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="khing",
    author_email="anchitha2005@gmail.com",
    url="https://github.com/khing2005/scm203lab267101691",  # optional
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[],
)