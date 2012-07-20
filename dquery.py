#!/usr/bin/env python

#if sys.stdout.isatty(): + turn off pipe detection
# + colors

import base64
import json
import re
import os
import fnmatch
import subprocess
import sqlalchemy
import argparse
import termcolor
import phpserialize
import cProfile
import sys
import cli #TODO
import yaml #TODO: would be nice with some colored keys etc

#import inspect
#TODO: rename module-usage to usage, or perhaps present tense, using?
from colorama import init
init()

try:
    import cPickle as pickle
except:
    import pickle

from sqlalchemy.exc import DatabaseError
#from phpserialize import *
#from time import clock, time

def dquery_get_project(module_namespace):
    return project_mapping[module_namespace]

def memoize(f, cache={}):
    def g(*args, **kwargs):
        key = ( f, tuple(args), frozenset(kwargs.items()) )
        if key not in cache:
            cache[key] = f(*args, **kwargs)
        return cache[key]
    return g

def pickle_memoize(f):
    def g(*args, **kwargs):
        #TODO: things will get fucked up if fuction decorated aka is g?
        key = ( f.__name__, tuple(args), frozenset(kwargs.items()) )
        script_dir = os.path.dirname(os.path.realpath(__file__))
        cache_filename = os.path.join(script_dir, 'cache', ''.join([str(key.__hash__()), '.', f.__name__]))
        #cache_filename = os.path.join('cache', str(key.__hash__()))
        #TODO: handle missing cache keyword etc
        if kwargs['cache'] and os.path.isfile(cache_filename):
            with open(cache_filename, 'r') as cache_file:
                result = pickle.load(cache_file)
        else:
            result = f(*args, **kwargs)
            with open(cache_filename, 'w') as cache_file:
                pickle.dump(result, cache_file)
        return result
    return g

def drupal_settings_variable_json(filename, variable):
    command = ['php', 'json_settings.php', filename, variable];
    try:
        #db_url_data = subprocess.check_output(command) # only works in python 2.7+
        json_data = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0]
        variable_json = json.loads(json_data)
        return variable_json;
    except subprocess.CalledProcessError as e:
        print e

d6_db_url_re = re.compile(r"^(?P<type>\w+?)://(?P<username>.+?)(?::(?P<password>.+?))?@(?P<hostname>.+?)(?::(?P<port>.+?))?/(?P<database>.+)$")

def drupal6_db_settings(filename):
    db_url = drupal_settings_variable_json(filename, 'db_url')
    if isinstance(db_url, dict):
        if 'default' in db_url:
             db_url = db_url['default']
        else:
             #TODO: proper error
            print 'error'

    #check if db_url is string?
    match = d6_db_url_re.match(db_url);
    return match.groupdict()

 
def sqlalchemy_connection_url(drupal_settings_filename, drupal_version = 6):

    if drupal_version == 6:
        drupal_settings = drupal6_db_settings(drupal_settings_filename);
    else:
        #TODO: proper error
        print 'error'

    db_type_mapping = {
        'mysqli' : 'mysql',
        'mysql' : 'mysql',
        'pgsql' : 'postgresql'
    }
    if(drupal_settings['type'] in db_type_mapping):

        connection_url = [
            db_type_mapping[drupal_settings['type']],
            '://',
            drupal_settings['username'],
        ]

        if 'password' in drupal_settings and drupal_settings['password'] is not None:
            connection_url.append(':' + drupal_settings['password']);

        connection_url.append('@');
        connection_url.append(drupal_settings['hostname'])

        if 'port' in drupal_settings and drupal_settings['port'] is not None:
            connection_url.append(':' + drupal_settings['port']);

        connection_url.append('/' + drupal_settings['database']);

        return ''.join(connection_url)

    else:
        #TODO: proper error
        print 'error'

#TODO return paths, absolute or relative??
@memoize
@pickle_memoize
def dquery_discover_sites(drupal_root, cache=True):
   
    sites = []
    sites_directory = os.path.join(drupal_root, 'sites');
    for f in os.listdir(sites_directory):
        if f != 'all':
            filename = os.path.join(sites_directory, f)
            if os.path.isdir(filename) and not os.path.islink(filename):
                for sf in os.listdir(filename):
                    if sf == 'settings.php':
                        #yield filename
                        sites.append(filename)
                        #break

    return frozenset(sites)

@memoize
@pickle_memoize
def dquery_discover_modules(path, cache=True):
    #TODO: yield shit?
    #TODO: decorator for this?
    modules = []
    for root, dirnames, filenames in os.walk(path):
        for basename in fnmatch.filter(filenames, '*.module'):
            #check for existing info-file? # yes
            if os.path.isfile(os.path.join(root, basename[:-6] + 'info')):
                modules.append(os.path.join(root, basename));
            #else warning?
    return modules

#TODO: not to much cache
# Actually need this memoized for module info action
# @pickle_memoize
def dquery_get_modules(path, cache=True):
    modules = {}
    for module_filename in dquery_discover_modules(path, cache=cache):
        modules[module_filename] = dquery_module_info(module_filename)
    return modules


def dquery_module_info(module_filename):
    info_filename = ''.join([module_filename[:-6], 'info'])
    with open(info_filename) as f:
        data = f.read()
        info_data = drupal_parse_info_format(data)
        return info_data

def dquery_valid_drupal_root(directory):
    fingerprint_files = set(['index.php', 'modules', 'sites']) # probably enough
    fingerprint_files.difference_update(os.listdir(directory))
    return not len(fingerprint_files)

# TODO: check if multislashes needed
info_format_re = re.compile(r"""
    ^\s*                                # Start at the beginning of a line, ignoring leading whitespace
    ((?:
        [^=;\[\]]|                      # Key names cannot contain equal signs, semi-colons or square brackets,
        \[[^\[\]]*\]                    # unless they are balanced and not nested
    )+?)
    \s*=\s*                             # Key/value pairs are separated by equal signs  (ignoring white-space)
    (?:
        ("(?:[^"]|(?<=\\\\)")*")|       # Double-quoted string, which may contain slash-escaped quotes/slashes
        (\'(?:[^\']|(?<=\\\\)\')*\')|   # Single-quoted string, which may contain slash-escaped quotes/slashes
        ([^\r\n]*?)                     # Non-quoted string
    )\s*$                               # Stop at the next end of a line, ignoring trailing whitespace
    """, re.M | re.S | re.X)


info_format_key_re = re.compile('\]?\[');

# port of drupal_parse_info_format (php)
def drupal_parse_info_format(data):
    def populate_info(keys, parent, value):
        if len(keys):
            key = keys.pop()
            if key == '':
                if parent is None:
                    parent = []
                parent.append(populate_info(keys, None, value))
            else:
                if parent is None:
                    parent = {}
                if not key in parent:
                    parent[key] = None
                parent[key] = populate_info(keys, parent[key], value)
            return parent
        else:
            return value

    info = {};
    matches = info_format_re.findall(data)

    for key, value1, value2, value3 in matches:
        keys = info_format_key_re.split(key.rstrip(']'))
        value = ''.join([\
            value1.strip('"').decode('string_escape'),\
            value2.strip("'").decode('string_escape'),\
            value3\
        ])
        keys.reverse()
        populate_info(keys, info, value)

    return info

#TODO: rename to build_something
#TODO: option for project assignment hack?
def dquery_modules_list(drupal_root, module_directories, cache=True):

    #TODO: check if exists, filter with list comprehension?
 
    #print json.dumps(modules, sort_keys=True, indent=4)
    # dquery_get_modules? dquery_modules()?
    #TODO: loop instead and have build_modules take only one path
    module_map = {}
    modules_project_missing = []

    for module_dir in module_directories:
        #TODO: remove this kludge, and scan for missing modules separately
        _module_map, _modules_project_missing = dquery_build_modules(drupal_root, module_dir, cache=True)
        modules_project_missing = modules_project_missing + _modules_project_missing
        
        for project, info in _module_map.iteritems():
            if project not in module_map:
                module_map[project] = {}
            module_map[project][module_dir] = info

        #for project in _module_map:
        #    for module_namespace in _module_map[project]:


    # seems to be dangerous to place here, isolate!
    """
    project_mapping = dquery_build_project_mapping(modules)

    #Second pass to fix modules with missing project, this feels hackish, provide option?
    for module_namespace, filename in modules_project_missing:
        try:
            project = project_mapping[module_namespace]
            modules[project]['modules'][module_namespace][filename] = []
        except KeyError:
            pass
    """

    return module_map

def dquery_module_namespace(module_filename):
    return os.path.basename(module_filename)[:-7]

#TODO: rename
@memoize
@pickle_memoize
def dquery_build_modules(drupal_root, module_dir, cache=True):

    modules = {}

    modules_project_missing = []

    for module_filename, info_data in dquery_get_modules(module_dir).iteritems():
        module_namespace = dquery_module_namespace(module_filename)
        filename = os.path.relpath(module_filename, drupal_root)
        
        #temporary workaround
        if os.path.relpath(module_filename, drupal_root).find('modules/') == 0:
            info_data['project'] = 'drupal'

        if 'project' in info_data:
            project = info_data['project']

            #if not module_namespace in project_mapping:
                #project_mapping[module_namespace] = project

            if not project in modules:
                modules[project] = {}

            if not module_namespace in modules[project]:
                modules[project][module_namespace] = {
                    'filename' : filename,
                    'info' : info_data
                }
            else:
                print 'error, duplicate module ' + module_namespace + ' in module directory ' + module_dir

        else:
            modules_project_missing.append((module_namespace, filename))
            #print 'no project: ' + info_data['name']

    module_map = {}
    
    for project in modules:
        project_files = []
        for module_namespace in modules[project]:
            project_files.append(modules[project][module_namespace]['filename'])
            
        project_directory = os.path.commonprefix(project_files)

        if not os.path.isdir(project_directory):
            project_directory = os.path.dirname(project_directory)
             
        module_map[project] = {
            'directory' : os.path.normpath(project_directory),
            'modules' : modules[project]
        }

    return (module_map, modules_project_missing)

@pickle_memoize
def dquery_build_project_mapping(drupal_root, cache=True):
    project_mapping = {}
    module_directories = dquery_drupal_module_directories(drupal_root)

    for module_dir in module_directories:
        for module_filename, info in dquery_get_modules(module_dir, cache=cache).iteritems():
            #temporary workaround
            if os.path.relpath(module_filename, drupal_root).find('modules/') == 0:
                info['project'] = 'drupal'

            if 'project' in info:
                module_namespace = dquery_module_namespace(module_filename)
                project_mapping[module_namespace] = info['project']
                project_mapping[module_filename] = info['project']

    return project_mapping


#TODO: if package all function in class, drupal_root can be provided as class property etc
#TODO: arg just one site?
@pickle_memoize
def dquery_build_module_usage_graph(drupal_root, site_directories = [], cache=True):

    module_directories = dquery_drupal_module_directories(drupal_root, include_sites=False, cache=cache)

    #TODO: list comprehension?
    #TODO: set default all dirs here instead?
    for site_dir in site_directories:
        module_directories.append(os.path.join(site_dir, 'modules'))
 
    #TODO: rename variable, project_tree, module_tree??
    module_map = dquery_modules_list(drupal_root, module_directories)

    project_mapping = dquery_build_project_mapping(drupal_root, cache=cache)

    usage_graph = {}

    for project in module_map:
        usage_graph[project] = {
            'sites' : set(),
            'modules' : {} # project_info #TODO really need this? Should just build usage
        }
        for module_directory, project_info in module_map[project].iteritems():
            for module_namespace, module_info in project_info['modules'].iteritems():
                filename = module_info['filename']
                if module_namespace not in usage_graph[project]['modules']:
                    usage_graph[project]['modules'][module_namespace] = {
                        'sites' : set(),
                        'filenames' : {}
                    }
                if filename\
                    not in usage_graph[project]['modules'][module_namespace]['filenames']:
                    usage_graph[project]['modules'][module_namespace]['filenames'][filename] = {
                        'sites' : set(),
                        'module_namespace' : module_namespace
                    }

    for site in dquery_discover_sites(drupal_root, cache=cache):
        connection_url = sqlalchemy_connection_url(os.path.join(site, 'settings.php'))
        engine = sqlalchemy.create_engine(connection_url + '?charset=utf8&use_unicode=0', encoding='utf-8')
        try:
            connection = engine.connect()
            #TODO: new try
            result = connection.execute('SELECT name, filename, status, info FROM system WHERE status <> 0 AND type = "module"')
            for row in result:
                #TODO: replace with try catch indextjohejsan since 2xfaster
                info = {}
                """
                try:
                    #This is slow as fuck
                    info = phpserialize.loads(row['info'], decode_strings=True)
                    if row['name'] == 'uc_auriga':
                        print info
                        exit()
                except ValueError as e:
                    print 'value error'
                    print row['filename']
                    print row['info']
                    print type(row['info'])
                    exit()
                """

                module_namespace = row['name']
                filename = row['filename']
                project = None

                try:
                    project = project_mapping[module_namespace]
                except KeyError:
                    try:
                        project = project_mapping[filename]
                    except KeyError:
                        pass
                    #print 'not found: ' + row['name']

                if project is not None:
                    try:
                        usage_graph[project]['sites'].add(site)
                        try:
                            usage_graph[project]['modules'][module_namespace]['sites'].add(site) # + status?
                            usage_graph[project]['modules'][module_namespace]['filenames'][filename]['sites'].add(site) # + status?
                        except KeyError:
                            print 'warning: ' + filename + ' not found for project ' + project
                    except KeyError:
                        pass
                        #print 'Index error: ' + filename
                        #print modules[project]['modules'][module_namespace]

                #else:
                    #print 'not found: ' + row['name']
            
            
            connection.close()

        except DatabaseError as e:
            #Fix proper error-output/logging
            print ''.join(['Error: failed connecting to ', site, ':', repr(e)])

    return usage_graph


def dquery_drupal_module_directories(drupal_root, include_sites=True, cache=True):
    module_directories = [] 
    module_directories.append(os.path.join(drupal_root, 'modules'))
    module_directories.append(os.path.join(drupal_root, 'sites/all/modules'))
    #TODO: profiles, more?
    if include_sites:
        for site in dquery_discover_sites(drupal_root, cache=cache):
            module_directories.append(os.path.join(site, 'modules'))
    return module_directories


def dquery_depends(args):
    print 'depends'
    print args

def dquery_belongs(args):
    print 'belongs'
    print args

#rename dquery_action_site, or dquery_module_sites, dquery_subcommand_site etc?
def dquery_sites(args):
    #TODO: we igore cache here since no real speed difference, how make this clear to the user?
    for site in dquery_discover_sites(args.drupal_root, cache=False):
        print dquery_format_site(site, args.drupal_root, args.format)

def dquery_projects(args):
    module_directories = dquery_drupal_module_directories(args.drupal_root, cache=args.use_cache)
    module_map = dquery_modules_list(args.drupal_root, module_directories, cache=args.use_cache)
    projects = args.projects if len(args.projects) else module_map.keys
    for project in projects:
        for projects_dir in module_map[project]:
            version = ''
            project_dir = module_map[project][projects_dir]['directory']
            for module_namespace, module_info in module_map[project][projects_dir]['modules'].iteritems():
                if 'version' in module_info['info']:
                    version = module_info['info']['version']
                    break
            print ', '.join(['project:' + project, 'version:' + version, 'directory:' + project_dir])
            
def dquery_modules(args):
    module_directories = dquery_drupal_module_directories(args.drupal_root, cache=args.use_cache)
    module_map = dquery_modules_list(args.drupal_root, module_directories, cache=args.use_cache)
    for project in module_map:
        for projects_dir in module_map[project]:
            project_dir = module_map[project][projects_dir]['directory']
            for module_namespace, module_info in module_map[project][projects_dir]['modules'].iteritems():
                info = module_info['info']
                version = info['version'] if 'version' in info else ''
                print ', '.join(['module:' + module_namespace, 'version:' + version, 'filename:' + module_info['filename']])


def dquery_module_info_action(args):
    #TODO: more path mangling
    module_abspath = None
    if os.path.isabs(args.module_path):
        module_abspath = os.path.realpath(args.module_path) 
    else:
        module_abspath = os.path.join(args.drupal_root, args.module_path)
    info = dquery_module_info(module_abspath)
    print yaml.dump(info, default_flow_style=False)

    """
    module_directories = dquery_drupal_module_directories(args.drupal_root, cache=args.use_cache)
    #here yield would actually perhaps be useful
    for module_dir in module_directories:
        modules = dquery_get_modules(module_dir, cache=args.use_cache)
        if module_abspath in modules:
            print modules[module_abspath]
            return
    """

    #print not found?


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

def dquery_usage(args):
    #TODO: add site args

    #module_directories = dquery_drupal_module_directories(args.drupal_root)
    #modules = dquery_modules_list(args.drupal_root, module_directories)

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


def dquery_format_site(site_abspath, drupal_root, format):
    if format == 'basename':
        return os.path.basename(site_abspath)
    if format == 'uri':
        return ''.join(['http://', os.path.basename(site_abspath)])
    elif format == 'relpath':
        return os.path.relpath(site_abspath, drupal_root)
    elif format == 'abspath':
        return site_abspath
    else:
        #print error/warning
        return site_abspath

def _dquery_main(args=None):

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description='Drupal module query tool')

    parser.add_argument('-r', '--root', dest='drupal_root', type=str, default='.', help='Drupal root directory to use')
    parser.add_argument('--relative', dest='relative_paths', action='store_true', help='Output paths relative to drupal root directory')
    parser.add_argument('-v', dest='verbose', action='store_true')
    parser.add_argument('-p', '--pipe', dest='pipe', action='store_true') # this can be auto-detected?

    #TODO: mutually exlusive with sub-commands?
    parser.add_argument('--no-cache', dest='use_cache', action='store_false', help='Do not use the internal dquery cache')
    parser.add_argument('--clear-cache', dest='clear_cache', action='store_true', help='Clear the interal dquery cache')

    #parser.add_argument('module_directories', metavar='MODULE_DIRECTORY',  type=str, nargs='*', help='Module directories')

    subparsers = parser.add_subparsers(help='sub-command help', title='commands')#, description='valid subcommands')
    
    """
    parser_list = subparsers.add_parser('list', help='list help')
    parser_list.add_argument('--baz', choices='XYZ', help='baz help')
    #TODO: how make parseargs save as frozenset instead of list
    parser_list.add_argument('module_directories', metavar='MODULE_DIRECTORY',  type=str, nargs='*', help='Module directories')
    parser_list.set_defaults(func=dquery_list)
    """
    
    parser_sites = subparsers.add_parser('sites', help='list sites')
    parser_sites.add_argument('-f, --format', dest='format', choices=['uri', 'relpath', 'abspath', 'basename'], default='uri', help='Site output format')
    #TODO: how make parseargs save as frozenset instead of list
    parser_sites.set_defaults(func=dquery_sites)
   
    parser_projects = subparsers.add_parser('projects', help='list projects')
    parser_projects.add_argument('projects', metavar='PROJECT', type=str, nargs='*', help='Limit results')
    parser_projects.set_defaults(func=dquery_projects)
    
    parser_modules = subparsers.add_parser('modules', help='list modules')
    parser_modules.add_argument('module_namespaces', metavar='MODULE', type=str, nargs='*', help='Limit results')
    parser_modules.set_defaults(func=dquery_modules)

    parser_module_info = subparsers.add_parser('module-info', help='display module info')
    parser_module_info.add_argument('module_path', type=str, help='Path to module to display info for')
    #TODO: how make parseargs save as frozenset instead of list
    parser_module_info.set_defaults(func=dquery_module_info_action)

    parser_usage = subparsers.add_parser('usage', help='usage help')
    #TODO: mutually exclusive sheid  
    parser_usage.add_argument('--type, -t', dest='type', default='project', choices=['module', 'project'], help='Type to check usage for')
    parser_usage.add_argument('--list-unused', dest='list_unused', action='store_true', help='List unused modules')
    parser_usage.add_argument('--sites', dest='site_directories', metavar='SITE_DIRECTORIES', type=str, nargs='*', help='Site directories')
    parser_usage.add_argument('-f, --format', dest='format', choices=['uri', 'relpath', 'abspath', 'basename'], default='abspath', help='Site output format')
    #parser_usage.add_argument('--module', dest='module_namespace', type=str, help='List usage for this module only')
    #parser_usage.add_argument('--project', dest='project', type=str, help='List usage for this project only')
    parser_usage.add_argument('targets', type=str, nargs='+', help='List usage for these targets')

    parser_usage.set_defaults(func=dquery_usage)

    parser_depends = subparsers.add_parser('depends', help='depends help')
    parser_depends.add_argument('--baz', choices='XYZ', help='baz help')
    parser_depends.set_defaults(func=dquery_depends)

    parser_belongs = subparsers.add_parser('belongs', help='belongs help')
    parser_belongs.add_argument('bar', type=int, help='baz help')
    parser_belongs.set_defaults(func=dquery_belongs)

    args = parser.parse_args(args)

    drupal_root = os.path.abspath(args.drupal_root)

    #process args, TODO: nice way of doing this
    try:
        if dquery_valid_drupal_root(drupal_root):
            args.drupal_root = drupal_root
        else:
            #TODO: python string formatting, gah
            parser.error(drupal_root + ' does not appear to be a valid drupal root directory')

    except Exception as e:
        parser.error(str(e))

    if args.clear_cache:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        cache_dir = os.path.join(script_dir, 'cache')
        for basename in os.listdir(cache_dir):
            filename = os.path.join(cache_dir, basename)
            try:
                if os.path.isfile(filename):
                    os.unlink(filename)
            except Exception as e:
                print e

    args.func(args)


if __name__ == '__main__':
    _dquery_main()
    #cProfile.runctx('_dquery_main()', globals(), locals())
    #cProfile.run('_dquery_main()')
