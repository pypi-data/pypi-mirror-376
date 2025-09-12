from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="electricalsystemcalculator",
    version="0.1.1",
    description="A Python library for three-phase electrical system calculations.",
    author="Bharti Mishra, Madhuri Shriniwar",
    author_email="bhartimishra7941@gmail.com, madhurishriniwar24@gmail.com",
    url="https://github.com/Modular-Minds/ElectricalSystemCalculator",
    packages=find_packages(include=["electricalsystemcalculator", "electricalsystemcalculator.*"]),
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.6",
    install_requires=[],
    include_package_data=True,
    keywords=["three-phase", "electrical", "power system", "engineering", "calculations"],

    project_urls={
        "Documentation": "https://github.com/Modular-Minds/ElectricalSystemCalculator#readme",
        "Source": "https://github.com/Modular-Minds/ElectricalSystemCalculator",
        "Tracker": "https://github.com/Modular-Minds/ElectricalSystemCalculator/issues",
    },
)

