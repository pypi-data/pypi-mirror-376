from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='quantum-scoring-sdk',
    version='0.3.3',
    author='Jaime Alexander Jimenez Lozano',
    author_email='jaimeajl@hotmail.com',
    description='Quantum-native framework with IBM Quantum hardware support and enterprise license control',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'scikit-learn',
        'qiskit>=0.45.0',
        'qiskit-aer>=0.13.0',
        'requests'
    ],
    extras_require={
        'ibm': ['qiskit-ibm-runtime>=0.15.0']
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    python_requires='>=3.8',
)
