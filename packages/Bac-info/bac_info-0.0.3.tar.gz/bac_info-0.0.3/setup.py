from setuptools import setup, find_packages
setup(
    name="Bac_info", 
    version="0.0.3",
    author="Aziz boudriga",
    author_email="",
    description="A collection of utility functions for common programming tasks including input validation, array/matrix operations, string processing, and mathematical calculations.",
    long_description=open("README.md", encoding="utf-8").read()+"\n\n"+open("changelog.txt", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license="MIT",
    url="",
    packages=find_packages(),  # Automatically finds all packages in your project
    install_requires=[
        # List your dependencies here, e.g.:
        # "requests>=2.25.1",
    ],
    python_requires='>=3.6',
)
