from setuptools import setup, find_packages

setup(
    name="kinematicsolver",
    version="1.5.0",
    description="An algebra-based kinematic variables solver for UAM",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Mahir Masudur Rahman",
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics"
    ],
    include_package_data=True,
    license="MIT",
)
