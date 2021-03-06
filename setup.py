from setuptools import setup, find_packages

setup(
    name='DQuery',
    version='0.1.0-rc4',
    author='David Gustafsson',
    author_email='david.gustafsson@xelera.se',
    packages=find_packages(),
    include_package_data=True,
    scripts=['bin/dquery', 'bin/dquery_php_var_json'],
    url='http://pypi.python.org/pypi/DQuery/',
    download_url='https://github.com/david-xelera/dquery/tarball/master',
    license='GPL',
    description='Drupal multisite query-tool.',
    long_description=open('README.rst').read(),
    keywords=["drupal"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: POSIX',
        'Programming Language :: PHP',
        'Programming Language :: Python',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
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

