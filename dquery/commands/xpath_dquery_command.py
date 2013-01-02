from dquery.application import dQueryCommand
from dquery.lib import *
from dquery.xpath import *

@dQueryCommand('xpath', help='query the multisite xml directly through xpath')
def dquery_xpath_dquery_command(args):
    return dquery_multisite_xpath_query(args.drupal_root, args.xpath_query, args.use_database, cache=args.use_cache)

dquery_xpath_dquery_command.add_argument('xpath_query', metavar='XPATH_QUERY', type=str, help='xpath query')
dquery_xpath_dquery_command.add_argument('--no-db', dest='use_database', action='store_const', const=False, default=True, help='Do not attempt any database connections')
