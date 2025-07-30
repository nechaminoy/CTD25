from setuptools import setup, find_packages

setup(
    name="KFC_Py",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'numpy',
        'keyboard',
        'pytest',
        'pytest-cov'
    ],
) 