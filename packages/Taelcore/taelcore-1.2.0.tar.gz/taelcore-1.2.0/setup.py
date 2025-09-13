from setuptools import setup, find_packages

setup(
    name='Taelcore',  
    version='1.2.0',
    description="Dimension reduction with best linear combination for optimal reduction of embeddings (Taelcore)",
    url="https://github.com/MorillaLab/Taelcore",
    packages=find_packages(),
    install_requires=[
        # List your dependencies here
    ],
    author='Ian MORILLA',  
    author_email='ian.morilla@math.univ-paris13.fr',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # License type
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',

)