# Created by A. MATHIEU at 26/02/2025
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='irr_uncertainty',
    version='1.5',
    packages=find_packages(),
    description='Irradiance uncertainty package',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Alexandre MATHIEU',
    author_email='mathalex@gmail.com',
    url='https://github.com/AlexandreHugoMathieu/irr_uncertainty',
    python_requires='>=3.9',
    install_requires=required,
    include_package_data=True
)
