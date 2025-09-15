from setuptools import setup, find_packages

setup(
    name="Flet Textfield Extras",              # package name on PyPI
    version="0.1.1",                # initial version
    author="Meezaan Ryklief",
    author_email="mryklicky@gmail.com",
    description="A brief description",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Progressing-Llama/Flet-Textfield-Extras/tree/main",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "flet"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
