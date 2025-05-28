from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="OMI_functions",
    version="0.1",
    packages=find_packages(),
    install_requires=requirements,  # Dependências (adicione aqui se precisar)
    author="Fernando Fernandes",
    author_email="fernando.allysson@usp.br",
    description="This is packpage with utils functions for make extract temporal series from hdf_files from OMI product",
    url="https://github.com/fernandoACF28/OMI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
