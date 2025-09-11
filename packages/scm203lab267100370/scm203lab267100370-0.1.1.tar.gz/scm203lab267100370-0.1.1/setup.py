from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="scm203lab267100370",
    version="0.1.1",
    description="This my package. Can use to Roots of Equation in One Variable and Initial Value Problems for a frist-order differential equation ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="THITIRAT",
    author_email="thitirat98242@gmail.com",
    url="https://github.com/Cartoonmee/scm203lab267100370",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[],
)
