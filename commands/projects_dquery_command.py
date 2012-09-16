from dquery.application import dQueryCommand
from dquery.lib import *

@dQueryCommand('projects', help='list projects')
def dquery_projects_command(args):
    module_directories = args.module_directories if\
            args.module_directories is not None else\
            module_directories_from_context(args.drupal_root, args.use_cache)
    module_map = dquery_modules_list(args.drupal_root, module_directories, cache=args.use_cache)

    if args.update_status is not None:
        compatibility = dquery_drupal_core_compatibility(args.drupal_root)

    projects = args.projects if len(args.projects) else module_map.keys()
    for project in projects:
        for projects_dir in module_map[project]:
            version = ''
            project_dir = module_map[project][projects_dir]['directory']
            for module_namespace, module_info in module_map[project][projects_dir]['modules'].iteritems():
                if 'version' in module_info['info']:
                    version = module_info['info']['version']
                    break
            #TODO: fix, for now just testing
            if args.update_status is not None:
                update_info = dquery_drupal_update_recommended_release(project, compatibility, cache=True)
                if update_info is not None and update_info['version'] != version:
                    print ', '.join(['project:' + project, 'version:' + version, 'directory:' + project_dir, 'status: latest version is ' + update_info['version']])
                else:
                    print ', '.join(['project:' + project, 'version:' + version, 'directory:' + project_dir, 'status: no updates available'])
            elif args.format is not None:
                replacements = {
                    'project' : project,
                    'version' : version,
                    'directory' : project_dir
                }
                #Just testing
                #Just try except here and we should be safe
                print args.format.format(**replacements)
            else:
                print ', '.join(['project:' + project, 'version:' + version, 'directory:' + project_dir])


dquery_projects_command.add_argument('--module-directories', dest='module_directories', metavar='MODULE_DIRECTORIES', type=str, nargs='*', help='Module directories')
dquery_projects_command.add_argument('--format', dest='format', metavar='PYTHON_FORMAT {blabla}', type=str, help='Format')
#TODO: some sort of action api/formalization? 'list'/'update_status' so forth, subsubcommands? dquery projects list, dquery projects update-status etc? Probably good idea
dquery_projects_command.add_argument('--update-status', dest='update_status', action='store_true', help='Show update status')
dquery_projects_command.add_argument('projects', metavar='PROJECT', type=str, nargs='*', help='Limit results')
