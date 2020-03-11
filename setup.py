# -*- coding: utf-8 -*-
from setuptools import setup, find_packages, Extension

setup(
    name='uvicorn-rest-framework',
    version="1.0.9",
    keywords=("uvicorn", "asyncio", "rest api", "python3"),
    description='Uvicorn Rest Framework',
    long_description="Uvicorn Rest Framework",
    author='caowenbin',
    author_email='cwb201314@qq.com',
    url='https://github.com/caowenbin/uvicorn-rest-framework',
    download_url='https://github.com/caowenbin/uvicorn-rest-framework',
    license='BSD',
    packages=["rest_framework"],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
       'Programming Language :: Python :: 3.6',
    ],
    scripts=['rest_framework/bin/uvicorn-admin.py'],
    entry_points={'console_scripts': [
        'uvicorn-admin = rest_framework.core.script:execute_from_command_line',
    ]},
    ext_modules=[
        Extension(
            "rest_framework.lib.orm.speedups",
            ["rest_framework/lib/orm/speedups.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.']
        ),
    ],
    install_requires=[
        "pytz>=2017.3",
        "blinker>=1.4",
        "Babel>=2.5.1",
        "uvicorn>=0.3.2"
    ]
)
