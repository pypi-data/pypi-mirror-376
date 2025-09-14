from setuptools import setup, find_packages

setup(
    name="feateng",
    version="0.3.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy",
        "pandas",
        "scikit-learn"
    ],
    author="Sanchitgg",
    author_email="sanchitgg2005@gmail.com",
    description="A feature engineering helper library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Sanchitgg/Data_Mat",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
