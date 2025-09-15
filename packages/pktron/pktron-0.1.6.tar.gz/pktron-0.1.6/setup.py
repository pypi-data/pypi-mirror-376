
from setuptools import setup, find_packages

setup(
    name="pktron",
    version="0.1.6",
    packages=find_packages(),
    install_requires=[
        'numpy>=1.21.0',
        'pennylane>=0.38.0',
        'matplotlib>=3.4.0',
        'quimb>=1.4.0',
        'networkx>=2.8.0',
        'plotly>=5.0.0',
        'seaborn>=0.11.0',
        'qutip>=4.6.0',
        'imageio>=2.9.0'
    ],
    author="PKTron Developer Canada",
    author_email="info@thecetqap.com",
    description="PKTron Pakistan's 1st Quantum Simulator with 100 Qubits Version 0.1.6",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/pktron/pktron",
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
