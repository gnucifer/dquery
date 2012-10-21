#TODO: Try placing this in __init__
from dquery.application import dQueryCommand
from dquery.lib import *

@dQueryCommand('modules', help='list modules')
def dquery_modules_command(args):
    module_directories = dquery_drupal_module_directories(args.drupal_root, cache=args.use_cache)
    module_map = dquery_modules_list(args.drupal_root, module_directories, cache=args.use_cache)
    for project in module_map:
        for projects_dir in module_map[project]:
            project_dir = module_map[project][projects_dir]['directory']
            for module_namespace, module_info in module_map[project][projects_dir]['modules'].iteritems():
                info = module_info['info']
                version = info['version'] if 'version' in info else ''
                print ', '.join(['module:' + module_namespace, 'version:' + version, 'filename:' + module_info['filename']])

dquery_modules_command.add_argument('module_namespaces', metavar='MODULE', type=str, nargs='*', help='Limit results')

# Differance??? Old version?
"""
def dquery_list(args):
    #TODO: callback default value in parseargs module?
    #TODO: do not need to be frozen set anymore
    module_directories = frozenset(args.module_directories)
    #TODO: append option?
    if not len(module_directories):
        module_directories = dquery_drupal_module_directories(args.drupal_root)

    modules = dquery_modules_list(args.drupal_root, module_directories)
    for project in modules:
        for module in modules[project]['modules']:
            print ': '.join([project, module])
"""




