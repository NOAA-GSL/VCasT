from setuptools import setup, find_packages

setup(
    name="mvt",  # Name of your project/package
    version="1.0.0",        # Version of your package
    package_dir={"": "mvt"},  # Specify src as the root for packages
    packages=find_packages(where="mvt"),  # Automatically discover packages in src/
    description="A tool for calculating forecast statistics like RMSE and bias.",
    author="Vanderlei Vargas Jr.",
    author_email="vanderlei.vargas@noaa.gov",
    url="https://github.com/VanderleiVargas-NOAA/ModelVerificationTool",  # Repository URL (optional)
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
    python_requires=">=3.6",  # Specify compatible Python versions
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "mvt_stat=mvt.main:main",  # Allows running `mvt` from the CLI
            "mvt_plot=mvt.main_plot:main_plot",
            "mvt_check=mvt.main_check:main_check",
            "mvt_conv=mvt.main_conv:main_conv"
        ]
    },
)

