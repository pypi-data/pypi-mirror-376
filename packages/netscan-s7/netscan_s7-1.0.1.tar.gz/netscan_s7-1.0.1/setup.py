from setuptools import setup, find_packages

setup(
    name="netscan-s7",
    version="1.0.1",
    packages=find_packages(),
    install_requires=[
        "colorama"
    ],
    entry_points={
        "console_scripts": [
            "networkscan = networkscan.networkscan:main"
        ]
    },
    author="SABIR7718",
    description="A fast multi-threaded network port scanner",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
