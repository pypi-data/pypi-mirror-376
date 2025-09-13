from setuptools import setup, find_packages
from Cython.Build import cythonize
import os

ext_modules = cythonize(
    [os.path.join("Virec_publish", "*.py")],
    compiler_directives={"language_level": "3"},
)

setup(
    name="VirecFremwork",
    version="0.2.2",
    author="Sumit Zala",
    author_email="sumit.zala@xbyte.io",
    description="Validate our data",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    ext_modules=ext_modules,
    package_data={
        "Virec_publish": ["*.pyd"],
    },
    zip_safe=False,
    include_package_data=True,  # 👈 ensures MANIFEST.in is respected
    install_requires=[
        # add dependencies if any
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
