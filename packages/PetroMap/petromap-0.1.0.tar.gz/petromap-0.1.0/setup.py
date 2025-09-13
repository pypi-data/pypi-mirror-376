from setuptools import setup, find_packages

setup(
    name="PetroMap",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "matplotlib",
        "scipy",
        "plotly",
        "scikit-learn"
    ],
    author="Nashat Jumaah Omar",
    description="A Contour Mapping Utility for Oil and Gas Engineers",
    url="https://github.com/Nashat90/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
