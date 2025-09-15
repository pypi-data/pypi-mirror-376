from setuptools import setup, find_packages

setup(
    name='arycodes',
    version='0.2',
    packages=find_packages(),
    install_requires=[
        'requests',
        'tabulate',
        'colorama'
        ],
    entry_points={
        'console_scripts': [
            'arycodes = arycodes.arycodes_cli:main'
        ]
    }
)
