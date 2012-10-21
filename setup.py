from setuptools import setup, find_packages

setup(
    name='DQuery',
    version='0.0.9',
    author='David Gustafsson',
    author_email='david.gustafsson@xelera.se',
    packages=find_packages(),
    include_package_data=True,
    scripts=['bin/dquery'],
    url='http://pypi.python.org/pypi/DQuery/',
    download_url='https://github.com/david-xelera/dquery/tarball/master',
    license='GPL',
    description='Drupal multisite query-tool.',
    long_description=open('README.txt').read(),
    keywords=["drupal"],
    install_requires=[
        "PyYAML",
        "SQLAlchemy",
        "colorama",
        "httplib2",
        "lxml",
        "phpserialize",
        "pyCLI",
        "termcolor",
    ],
)

