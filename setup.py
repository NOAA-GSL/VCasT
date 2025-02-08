from setuptools import setup, find_packages

setup(
    name="vcast",  
    version="1.0.0",    
    package_dir={"": "vcast"},
    packages=find_packages(where="vcast"),
    description="A tool for calculating forecast statistics like RMSE and bias.",
    author="Vanderlei Vargas Jr.",
    author_email="vanderlei.vargas@noaa.gov",
    url="https://github.com/VanderleiVargas-NOAA/VCast",
    install_requires=[
        "numpy",
        "pygrib",
        "netCDF4",
        "pyyaml",
        "scipy",
        "argparse",
        "pandas",
        "matplotlib",
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

