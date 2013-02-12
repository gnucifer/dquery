from dquery.application import dQueryCommand
from dquery.lib import *
from dquery.xpath import *

#Projects
@dQueryCommand('projects', help='Extract and present projects metadata')
def dquery_projects_dquery_command(args):
    #backup_directory = None
    #target_directory = None
    #source_directories = [args.drupal_root]
    # In place warning?
    # Get project directories and add them to projects
    xpath_query = '//project'
    projects = None

    if args.directories:
        # make directories arg hashable
        directories = frozenset(args.directories)
        projects = dquery_multisite_xml_directories_xpath(args.drupal_root, xpath_query, False, directories, cache=args.use_cache)
    else: 
        projects = dquery_multisite_xml_xpath(args.drupal_root, xpath_query, False, cache=args.use_cache)
    # Bit of a hack, how get rid of this?
    for project in projects:
        #try?
        project_abspath = project.getparent().attrib['abspath']
        project_relpath = project.getparent().attrib['relpath']
        project.attrib['abspath'] = project_abspath
        project.attrib['relpath'] = project_relpath
        for child in project.getchildren():
            project.remove(child)
    
    return dquery_xpath_result_to_python(projects)

dquery_projects_dquery_command.add_argument('directories', metavar='DIRECTORY', nargs='*', type=str, help='project directories relative to drupal root')
