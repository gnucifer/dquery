#TODO: Try placing this in __init__
from dquery.application import dQueryCommand
from dquery.lib import *
from functools import partial

@dQueryCommand('sites', help='list sites')
def dquery_sites_command(args):
    #TODO: we igore cache here since fast enough any way, how make this clear to the user?
    return map(partial(dquery_format_site, args.format, args.drupal_root), dquery_discover_sites(args.drupal_root, cache=False))

dquery_sites_command.add_argument('-f', '--format', dest='format', choices=['uri', 'relpath', 'abspath', 'basename'], default='uri', help='Site output format')
#TODO: how make parseargs save as frozenset instead of list
