#!/usr/bin/env python

import setuptools
import os

setuptools.setup(
    name='multilibgeosuitesnd',
    version='0.0.10.1',
    description='Parser for the GeoSuite<tm> SND export format forked with bugfixes',
    long_description="""Parser for the GeoSuite<tm> SND export format""",
    long_description_content_type="text/markdown",
    author='Jakob Drage Roti',
    author_email='jdr@multiconsult.no',
    url='https://github.com/Multiconsult-Group/10563014-geo-libgeosuitesnd',
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={'libgeosuitesnd': ['*/*.csv']},
    install_requires=[
        "numpy",
        "pandas",
    ],
    entry_points = {
        'libsgfdata.parsers': ['snd=libgeosuitesnd:parse'],
    }
)
