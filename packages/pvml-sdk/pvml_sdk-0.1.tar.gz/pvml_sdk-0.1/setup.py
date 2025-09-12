from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required_packages = f.readlines()

setup(
    name='pvml-sdk',
    version='0.1',
    packages=find_packages(),
    python_requires=">=3.11",
    setup_requires=["setuptools"],
    install_requires=[pkg.strip() for pkg in required_packages],
)
