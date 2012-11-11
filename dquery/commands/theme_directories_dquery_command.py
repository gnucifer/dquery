from dquery.application import dQueryCommand
from dquery.lib import *

@dQueryCommand('theme-directories', help='list theme directories')
def dquery_theme_directories_dquery_command(args):
    return dquery_drupal_system_directories(
        args.drupal_root,
        'themes',
        include_sites=True,
        cache=args.use_cache)

