from setuptools import setup, find_packages

setup(
    name='Exversion Layer',
    version='0.001',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask', 'psycopg2', 'psycopg2.extras']
)