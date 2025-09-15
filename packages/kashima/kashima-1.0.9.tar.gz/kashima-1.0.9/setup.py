from setuptools import setup, find_packages
from pathlib import Path

README = Path("README.md").read_text(encoding="utf-8")

setup(
    name="kashima",
    version="1.0.9",
    author="Alejandro Verri Kozlowski",
    author_email="averri@fi.uba.ar",
    description="Machine Learning Tools for Geotechnical Earthquake Engineering, plus the tito scientific pipeline.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/averriK/kashima",
    packages=find_packages(
        include=["kashima*"],
        exclude=("dist*", "build*", "tests*", "test*", "legacy*", "archive*"),
    ),
    include_package_data=True,  # necesario si incluyes prompts dentro del paquete
    install_requires=[
        "pandas",
        "numpy",
        "folium",
        "geopandas",
        "pyproj",
        "requests",
        "branca",
        "geopy",
        "matplotlib",
        "obspy",
        'dataclasses; python_version < "3.7"',
        # Dependencias de tito:
        "openai>=1.40.0",
    ],
    entry_points={
        "console_scripts": [
            # CLI para el pipeline tito
            "tito = kashima.tito.cli:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",  # openai>=1.40 requiere >=3.8
    package_data={
        # Si guardas los prompts dentro del paquete en kashima/tito/prompts/*.md descomenta:
        # "kashima.tito": ["prompts/*.md"]
    },
)
