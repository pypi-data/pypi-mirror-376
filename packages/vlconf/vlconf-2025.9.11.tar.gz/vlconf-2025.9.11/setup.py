# Setup file

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


def get_requirements():
    """Get the requirement libraries"""
    with open("requirements.txt") as freq:
        rlines = freq.readlines()
        # print(rlines)
        mreq = rlines[2:]

    with open("optional-requirements.txt") as foreq:
        rlines = foreq.readlines()

        oreq = rlines[2:]

    return mreq, oreq



setuptools.setup(
    name="vlconf",
 	version="2025.09.11",
    author="Vaishak Prasad",
    author_email="vaishakprasad@gmail.com",
    description="Global python configuration and verbosity levels",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/vaishakp/config",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3",
)
