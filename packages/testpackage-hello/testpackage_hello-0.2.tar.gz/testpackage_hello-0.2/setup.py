from setuptools import setup, find_packages

setup(
    name='testpackage_hello',
    version='0.2',
    packages=find_packages(),
    install_requires=[
    ],
    entry_points={
        "console_scripts": [
            "testpackage-hello = testpackage_hello:hello",
        ],
    },
)
