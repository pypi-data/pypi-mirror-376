from setuptools import setup

setup(
    name='mol-adme',
    version='1.0.0',
    py_modules=['mol_adme'],  # your main script renamed mol_adme.py
    install_requires=[
        'rdkit-pypi==2023.3.1b1',  # stable RDKit version for Windows/Linux
        'pandas>=2.0.3',
        'matplotlib>=3.7.1'
    ],
    entry_points={
        'console_scripts': [
            'mol-adme=mol_adme:main',  # CLI command
        ],
    },
    author="Sai Eswar M",
    author_email="msaieswar2002@gmail.com",
    description="Offline ADME & BOILED-Egg batch tool for molecules",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url="https://pypi.org/project/mol-adme/",  # optional
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
