from setuptools import setup, find_packages

setup(
    name="scm203lab267112755",               # Must be unique on PyPI!
    version="0.1.2",                # Follow semantic versioning
    description="Numerical methods: root finding and ODE solvers (Secant, False Position, Runge-Kutta).",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Lewan",
    author_email="natthapong.nn@mail.wu.ac.th",
    url="https://github.com/yourusername/mypackage",  # optional
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[],
)