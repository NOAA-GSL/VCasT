from setuptools import setup, find_packages

setup(
    name="vcast",  
    version="1.0.0", 
    packages=find_packages(include=["vcast", "vcast.*"]),
    description="A tool for calculating forecast statistics like RMSE and bias.",
    author="Vanderlei Vargas Jr.",
    author_email="vanderlei.vargas@noaa.gov",
    url="https://github.com/VanderleiVargas-NOAA/VCast",
    install_requires=[
        "numpy",
        "netCDF4",
        "pyyaml",
        "scipy",
        "argparse",
        "pandas",
        "matplotlib",
        "colorama",
        "xarray",
        "zarr",
        "pygrib"
    ],
    python_requires=">=3.6",  
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "vcast=vcast.main:main",
        ]
    },
)

