from setuptools import setup, find_packages

setup(
    name='DQuery',
    version='0.1.0-beta',
    author='David Gustafsson',
    author_email='david.gustafsson@xelera.se',
    packages=find_packages(),
    include_package_data=True,
    scripts=['bin/dquery', 'bin/dquery_php_var_json'],
    url='http://pypi.python.org/pypi/DQuery/',
    download_url='https://github.com/david-xelera/dquery/tarball/master',
    license='GPL',
    description='Drupal multisite query-tool.',
    long_description=open('README.txt').read(),
    keywords=["drupal"],
    install_requires=[
        "PyYAML",
        "SQLAlchemy",
        "MySQL-python",
        "colorama",
        "httplib2",
        "lxml",
        "phpserialize",
        "pyCLI",
        "termcolor",
    ],
)

