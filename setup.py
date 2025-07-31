from setuptools import setup, find_packages

extras_require = {
    "io": [],
    "plot": [
        "matplotlib<=3.8.4",
        "pandas<=2.2.2"
    ],
    "stat": [
        "scipy<=1.13.0",
        "numpy<=1.26.4"
    ],
    "metstat": [
        "pandas<=2.2.2"
    ],
    "agg": [
        "scipy<=1.13.0",
        "pandas<=2.2.2",
        "numpy<=1.26.4"
    ],
    "preprocess": [
        "xarray<=2024.4.0",
        "netCDF4<=1.6.5",
        "zarr<=2.17.0",
        "pygrib<=2.1.5",
        "pandas<=2.2.2"
    ],
    "processing": [
        "xarray<=2024.4.0",
        "netCDF4<=1.6.5",
        "zarr<=2.17.0",
        "pygrib<=2.1.5",
        "scipy<=1.13.0"
    ],
}

# Named install groups
extras_require["lite"] = (
    extras_require["io"] +
    extras_require["plot"] +
    extras_require["metstat"] +
    extras_require["agg"]
)

# Remove duplicates while preserving order
def dedup(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]

extras_require["all"] = dedup(
    sum(extras_require.values(), [])
)

setup(
    name="vcast",
    version="1.0.0",
    packages=find_packages(include=["vcast", "vcast.*"]),
    description="VCasT: Verification and Forecast Evaluation Tool",
    author="Vanderlei Vargas Jr.",
    author_email="vanderlei.vargas@noaa.gov",
    url="https://github.com/NOAA-GSL/VCasT",
    install_requires=[
        "pyyaml<=6.0.1",
        "colorama<=0.4.6",
    ],
    extras_require=extras_require,
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "vcast=vcast.cli:main",
        ]
    },
)
