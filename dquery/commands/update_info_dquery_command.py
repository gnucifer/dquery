from dquery.application import dQueryCommand
from dquery.lib import dquery_drupal_update_info_projects_data, dquery_drupal_core_compatibility
@dQueryCommand('update-info', help='Fetch project(s) update info from update.drupal.org')
def dquery_update_info_dquery_command(args):
    compatibility = dquery_drupal_core_compatibility(args.drupal_root)
    return dquery_drupal_update_info_projects_data(compatibility, frozenset(args.projects))

dquery_update_info_dquery_command.add_argument('--connections', type=int, help='number of concurrent connections')
dquery_update_info_dquery_command.add_argument('--timeout', type=int, help='timeout')
dquery_update_info_dquery_command.add_argument('projects', metavar='PROJECT', nargs='+', type=str, help='project(s) to list update info for')
