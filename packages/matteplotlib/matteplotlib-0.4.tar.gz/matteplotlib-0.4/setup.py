from setuptools import setup, find_packages

setup(
    name='matteplotlib',
    version='0.4',
    packages=find_packages(),
    install_requires=[
        # Add dependencies here.
        # e.g. 'numpy>=1.11.1'
    ],
    entry_points={
        "console_scripts": [
            "test-hello = matplotib:hello",
            "ml-index = matplotib:ml_index",
        ],
    },
)