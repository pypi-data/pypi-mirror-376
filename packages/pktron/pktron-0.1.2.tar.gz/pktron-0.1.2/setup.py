
from setuptools import setup, find_packages
import os

setup(
    name="pktron",
    version="0.1.2",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "matplotlib>=3.4.0",
        "quimb>=1.4.0",
    ],
    author="CETQAP",
    author_email="info@thecetqap.com",
    description="Pakistan's 1st Quantum 100 Qubit Simulator A quantum circuit simulator with statevector, stabilizer, and MPS backends",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/cetqap/pktron",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
