from setuptools import find_packages, setup

with open("README.md", "r") as f:
    page_description = f.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="gustavo-pacote-processamento-imagens",
    version="0.0.1",
    author="Gustavo_lima",
    author_email="gustavofifa580@gmail.com",
    description="My short description",
    long_description=page_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Gustavo-Lima17/pacote-processamento-imagens",  
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.8',
)