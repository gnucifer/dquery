from dquery.application import dQueryCommand
from dquery.lib import *
from dquery.xpath import *
from dquery.drush import dquery_drush_command, dquery_drush_commands
import warnings

# Options, target-directory, source-directories?, overwrite (prompt,yes,no/skip), backup dir?
# Or split into smaller commands, project directories? Project info?

@dQueryCommand('projects-git', help='Attempt to detect versions of drupal projects and check them out from git.drupal.org')
def dquery_projects_git_dquery_command(args):
    xpath_query = '//project'
    if args.source_directories:
        # make directories arg hashable
        directories = frozenset(args.source_directories)
        projects = dquery_multisite_xml_directories_xpath(args.drupal_root, xpath_query, False, directories, cache=args.use_cache)
    else: 
        projects = dquery_multisite_xml_xpath(args.drupal_root, xpath_query, False, cache=args.use_cache)
    
    """
    unique_projects = set()
    for project in projects:
        project_name = project.attrib['name']
        unique_projects.add(project_name)

    compatibility = dquery_drupal_core_compatibility(args.drupal_root)
    
    projects_data = dquery_drupal_update_info_projects_data(compatibility, frozenset(unique_projects), cache=args.use_cache)
    """
    target_dir = args.target_directory
    backup_dir = args.backup_directory

    for project in projects:
        #TODO: sort this mess out
        #project_abspath = project.getparent().attrib['abspath']

        #Check if is dirty??

        #Check if git dir

        #Get current branch

        project_relpath = project.getparent().attrib['relpath']
        target_abspath = os.path.join(target_dir, project_relpath)
        
        if not os.path.isdir(target_abspath):
            os.makedirs(target_abspath)
        elif dquery_is_git_dir(target_abspath):
            # Alreasy exists and is a git repo, issue warning and continue
            warnings.warn(
                "target directory {0!r} already exists and is a git directory, skipping.".format(target_abspath),
                DQueryWarning)
            continue

        repo_url = dquery_drupal_org_git_url(project.attrib['name'])
        branch = project.attrib['git_branch'] if 'git_branch' in project.attrib else None
        dquery_git_install_project(repo_url, project.attrib['version'], target_abspath, branch=branch)  
            
    #TODO: collect drupal updatexml version data, use gevent??? Separate cache bin for this?? yes, no

    # First collect project names and save in list

    # Then prepare gevent thread-pool for sending version info requests to updates.drupal.org


    # //TODO: for a possible future pm-update-command
    # Compare preferred version (with respect to configuratins in .dquery.py) against currently installed
    # If a higher preferred version is found update to new version (probably using the excellent pm in drush)
    # This command could take arguments to forward to drush?


    #TODO: In place warning?
    #xml_tree = dquery_build_multisite_xml_etree(args.drupal_root, False, cache=args.use_cache)

dquery_projects_git_dquery_command.add_argument('source_directories', metavar='SOURCE_DIRECTORY', nargs='*', type=str, help='project directories relative to drupal root')
#TODO: allow for target and backup dires to be relative?
dquery_projects_git_dquery_command.add_argument('--target-dir', metavar='TARGET_DIRECTORY', dest='target_directory', type=str, help='target root directory, if not supplied projects will be replaced in place')
dquery_projects_git_dquery_command.add_argument('--backup-dir', metavar='BACKUP_DIRECTORY', dest='backup_directory', type=str, help='backup directory')
