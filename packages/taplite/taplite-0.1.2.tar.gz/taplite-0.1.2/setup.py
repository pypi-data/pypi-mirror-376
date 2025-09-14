import re
from setuptools import setup


_package_name = 'taplite'


def get_long_description():
    with open('README.md', 'r') as fh:
        return fh.read()


def get_version():
    init_file = f'{_package_name}/__init__.py'
    with open(init_file, 'r') as fh:
        content = fh.read()

    version = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
    if version:
        return version.group(1)

    raise RuntimeError('unable to find version info in __init__.py')


setup(
    name=_package_name,
    version=get_version(),
    author='Dr. Xuesong Zhou, Dr. Peiheng Li',
    author_email='xzhou74@asu.edu, jdlph@hotmail.com',
    description='A lightweight traffic assignment and simulation engine for networks encoded in GMNS',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/asu-trans-ai-lab/TAPLite',
    packages=[_package_name],
    package_dir={_package_name: _package_name},
    package_data={_package_name: ['*.dll', '*.dylib', '*.so']},
    license='Apache License 2.0',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
)
