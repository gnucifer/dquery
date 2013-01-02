from dquery.application import dQueryCommand
from dquery.lib import *
from dquery.xml import *

@dQueryCommand('multisite-xml', help='generate multisite xml for making xpath queries against')
def dquery_multisite_xml_dquery_command(args):
    return dquery_build_multisite_xml(args.drupal_root, args.use_database, cache=args.use_cache)

#TODO: replace with some bootstrap abstraction?
dquery_multisite_xml_dquery_command.add_argument('--no-db', dest='use_database', action='store_const', const=False, default=True, help='Do not attempt any database connections')
