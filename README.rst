DQuery
======

DQuery is a general tool used to extract metadata from a drupal multisite
installation, and query this metadata using xpath. It also provides some other
commands complementing drush. Inspired by drush and Gentoo linux equery.

Planned features are an alternative package manager (to drush) and more
complete integration against the Drupal version data API.

.. contents::

Installation
------------

The easiest way is to install is using pip::

    pip install DQuery

To install directly from github::

    pip install git+git://github.com/david-xelera/dquery.git

If you are running Python <= 2.7 you will need to make sure the argparse Python package is installed since it's not included standard library::

    pip install argparse

When first run without the ``--no-cache`` option DQuery will complain about a missing cache directory. You will need to create this directory manually and ensure the appropriate permissions are set.

Usage
-----

In all examples it is assumed that you are standing in a valid Drupal multisite installation. To explicitly set the drupal root use the ``-r`` argument.


Commands:
~~~~~~~~~

multisite-xml
^^^^^^^^^^^^^

Generate and print a structured xml-representation of a drupal installation::

    dquery multisite-xml

Right now this is the only way finding out the multisite-xml format queried against in the ``xpath`` command.


xpath
^^^^^

List the relative paths (to the Drupal root directory) of all enabled modules::

    dquery xpath "//module[descendant::usage[@status='enabled']]/@relpath"

List directories of all projects with enabled modules::

    dquery xpath "//project[descendant::usage[@status='enabled']]/parent::directory/@abspath"

List directories of all unused projects::

    dquery xpath "//project[not(descendant::usage)]/parent::directory/@abspath"

List locations of all views 3 installations::

    dquery xpath "//project[@name='views' and @version-major='3']/parent::directory/@abspath"


Formatters
~~~~~~~~~~

The ``sites`` command are used in the following examples:


pipe
^^^^

Attempt to format output as simple text, easily parsed by standards unix commands like grep, cut etc::

    dquery --pipe sites
    http://site.com
    http://anothersite.com
    http://yetanothersite.com

pipe is the standard output format so ``dquery sites`` will produce the same result.


json
^^^^

Format output as json::

    dquery --json sites
    [
        "http://site.com", 
        "http://anothersite.com", 
        "http://yetanothersite.com"
    ]


yaml
^^^^

Format output as yaml::

    dquery --yaml sites
    - http://site.com
    - http://anothersite.com
    - http://yetanothersite.com


Writing your own commands
-------------------------

More information to come.


Writing your own formatters
---------------------------

More information to come.
