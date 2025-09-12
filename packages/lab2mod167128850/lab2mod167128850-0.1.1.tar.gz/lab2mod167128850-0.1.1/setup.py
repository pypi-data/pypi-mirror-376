from setuptools import setup, find_packages

setup(
    name="lab2mod167128850",               # Must be unique on PyPI!
    version="0.1.1",                # Follow semantic versioning
    description="A simple example package with basic calculation of fixed_point_iteration and  false_position.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Yok",
    author_email="raseljone.com@gmail.com",
      # optional
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[],
)