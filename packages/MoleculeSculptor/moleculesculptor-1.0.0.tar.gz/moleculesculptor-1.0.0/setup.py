from setuptools import setup, find_packages

setup(
    name='MoleculeSculptor',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pandas',
        'numpy',
        'matplotlib',
        'rdkit',
    ],
    author="Park Jinyong",
    author_email="phillip1998@korea.ac.kr",
    description="Molecule Segmentation Tool",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/ACCA-KU/MoleculeSculptor",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)