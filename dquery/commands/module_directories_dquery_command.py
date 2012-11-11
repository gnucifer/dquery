from dquery.application import dQueryCommand
from dquery.lib import *

@dQueryCommand('module-directories', help='list module directories')
def dquery_module_directories_dquery_command(args):
    return dquery_drupal_system_directories(
        args.drupal_root,
        'modules',
        include_sites=True,
        cache=args.use_cache)
"""
dquery_xpath_dquery_command.add_argument(
    'project',
    metavar='PROJECT_NAME',
    type=str,
    help='list module directories for PROJECT_NAME')
"""
#TODO: include_sites argument?
