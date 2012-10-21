#temporary hack
from dquery.application import dQueryCommand

@dQueryCommand('usage')
def dquery_usage_command(args):
    #This gets called when command executed
    site_directories = []

    if not args.site_directories:
        site_directories = dquery_discover_sites(args.drupal_root, cache=args.use_cache)

    #TODO: fix cache
    usage_graph = dquery_build_module_usage_graph(args.drupal_root, site_directories, cache=args.use_cache)

    #unused = []
    #TODO: implement as subcommand?
    if args.list_unused:
        for project, info in usage_graph.iteritems():
            if not len(info['sites']):
                #unused.append(project)
                print project

    if args.type == 'module':
        project_mapping = dquery_build_project_mapping(args.drupal_root, cache=args.use_cache) 
        for target in args.targets:
            if target in project_mapping:
                project = project_mapping[target]
                for site in usage_graph[project]['modules'][target]['sites']:
                    print dquery_format_site(site, args.drupal_root, args.format)
            else:
                #TODO print error
                print 'invalid module ' + target
                exit(2)
    elif args.type == 'project':
        for target in args.targets:
            if target in usage_graph:
                for site in usage_graph[target]['sites']:
                    print dquery_format_site(site, args.drupal_root, args.format)
            else:
                print 'invalid project ' + target
                exit(2)

dquery_usage_command.add_argument(
    '--type, -t',
    dest='type',
    default='project',
    choices=['module', 'project'],
    help='Type to check usage for')

dquery_usage_command.add_argument(
    '--list-unused',
    dest='list_unused',
    action='store_true',
    help='List unused modules')

dquery_usage_command.add_argument(
    '--sites',
    dest='site_directories',
    metavar='SITE_DIRECTORIES',
    type=str,
    nargs='*',
    help='Site directories')

dquery_usage_command.add_argument(
    '-f, --format',
    dest='format',
    choices=['uri', 'relpath', 'abspath', 'basename'],
    default='abspath',
    help='Site output format')

#dquery_usage_command.add_argument('--module', dest='module_namespace', type=str, help='List usage for this module only')
    #dquery_usage_command.add_argument('--project', dest='project', type=str, help='List usage for this project only')
dquery_usage_command.add_argument(
    'targets',
    type=str,
    nargs='+',
    help='List usage for these targets')

#parser_usage.set_defaults(func=dquery_usage)

#@dQueryCommand('usage')
#def dquery_usage_command(args):
    #TODO: add site args

    #module_directories = dquery_drupal_module_directories(args.drupal_root)
    #modules = dquery_modules_list(args.drupal_root, module_directories)


"""
usage_dquery_command.add_argument(
        '--type, -t',
        dest='type',
        default='project',
        choices=['module', 'project'],
        help='Type to check usage for'
    )

usage_dquery_command.add_argument(
        '--list-unused',
        dest='list_unused',
        action='store_true',
        help='List unused modules'
    )

usage_dquery_command.add_argument('--sites',
        dest='site_directories',
        metavar='SITE_DIRECTORIES',
        type=str,
        nargs='*',
        help='Site directories'
    )

usage_dquery_command.add_argument(
        '-f, --format',
        dest='format',
        choices=['uri', 'relpath', 'abspath', 'basename'],
        default='abspath',
        help='Site output format'
    )

#usage_dquery_command.add_argument('--module', dest='module_namespace', type=str, help='List usage for this module only')
#usage_dquery_command.add_argument('--project', dest='project', type=str, help='List usage for this project only')
usage_dquery_command.add_argument(
        'targets',
        type=str,
        nargs='+',
        help='List usage for these targets'
    )
"""
