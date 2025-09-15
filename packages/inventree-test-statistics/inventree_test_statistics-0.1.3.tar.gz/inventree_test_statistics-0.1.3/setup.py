# -*- coding: utf-8 -*-

import setuptools

from test_statistics.version import PLUGIN_VERSION

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name="inventree-test-statistics",
    version=PLUGIN_VERSION,
    author="Oliver Walters",
    author_email="oliver.henry.walters@gmail.com",
    description="Test statistics plugin for InvenTree",
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords="inventree inventory",
    url="https://github.com/inventree/inventree-test-statistics",
    license="MIT",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'tablib',
    ],
    setup_requires=[
        "wheel",
        "twine",
    ],
    python_requires=">=3.9",
    entry_points={
        "inventree_plugins": [
            "TestStatistics = test_statistics.core:TestStatisticsPlugin",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Framework :: InvenTree",
    ],
)
