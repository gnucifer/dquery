#TODO: Try placing this in __init__
from dquery.application import dQueryCommand
from dquery.lib import *

@dQueryCommand('sites', help='list sites')
def dquery_sites_command(args):
    #TODO: we igore cache here since no real speed difference, how make this clear to the user?
    for site in dquery_discover_sites(args.drupal_root, cache=False):
        print dquery_format_site(site, args.drupal_root, args.format)

dquery_sites_command.add_argument('-f, --format', dest='format', choices=['uri', 'relpath', 'abspath', 'basename'], default='uri', help='Site output format')
#TODO: how make parseargs save as frozenset instead of list
