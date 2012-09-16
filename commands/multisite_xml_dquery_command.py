from dquery.application import dQueryCommand
from dquery.lib import *

@dQueryCommand('multisite-xml', help='generate multisite xml for making xpath queries against')
def dquery_multisite_xml_dquery_command(args):
    dquery_build_multisite_xml(args.drupal_root, cache=args.use_cache)
