from setuptools import setup, find_packages

setup(
    name='kaqing',
    version='1.98.122',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'qing = adam.cli:cli'
        ]
    }
)
