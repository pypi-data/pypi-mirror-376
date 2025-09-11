from setuptools import setup, find_packages

setup(
    name="scm20367104703",               # Must be unique on PyPI!
    version="0.1.1",                # Follow semantic versioning
    description="This is package . A example package to find Roots of eqaution and solves an ordinary differential equation (ODE).",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="N. Amarittabut",
    author_email="nabeel65010@email.com",
    url="https://github.com/Amarit1008/ammaritproj",  # optional
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
)