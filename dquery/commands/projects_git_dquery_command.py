from dquery.application import dQueryCommand
from dquery.lib import *
from dquery.xpath import *

# Options, target-directory, source-directories?, overwrite (prompt,yes,no/skip), backup dir?
# Or split into smaller commands, project directories? Project info?

@dQueryCommand('projects-git', help='Attempt to detect versions of drupal projects and check them out from git.drupal.org')
def dquery_projects_git_dquery_command(args):
    xpath_query = '//projects'
    if args.source_directories:
        # make directories arg hashable
        directories = frozenset(args.source_directories)
        projects = dquery_multisite_xml_directories_xpath(args.drupal_root, xpath_query, False, directories, cache=args.use_cache)
    else: 
        projects = dquery_multisite_xml_xpath(args.drupal_root, xpath_query, False, cache=args.use_cache)
    
    #TODO: collect drupal updatexml version data, use gevent??? Separate cache bin for this?? yes, no

    # First collect project names and save in list

    # Then prepare genvent thread-pool for sending version info requests to updates.drupal.org


    # //TODO: for a possible future pm-update-command
    # Compare preferred version (with respect to configuratins in .dquery.py) against currently installed
    # If a higher preferred version is found update to new version (probably using the excellent pm in drush)
    # This command could take arguments to forward to drush?


    #TODO: In place warning?
    #xml_tree = dquery_build_multisite_xml_etree(args.drupal_root, False, cache=args.use_cache)
    return 'test'

dquery_projects_git_dquery_command.add_argument('source_directories', metavar='SOURCE_DIRECTORY', nargs='*', type=str, help='project directories relative to drupal root')
dquery_projects_git_dquery_command.add_argument('--target-dir', metavar='TARGET_DIRECTORY', dest='target_directory', type=str, help='target root directory, if not supplied projects will be replaced in place')
dquery_projects_git_dquery_command.add_argument('--backup-dir', metavar='BACKUP_DIRECTORY', dest='backup_directory', type=str, help='backup directory')
