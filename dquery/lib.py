#!/usr/bin/env python

#if sys.stdout.isatty(): + turn off pipe detection
# + colors
#TODO: python doc-strings format and inline tests for relevant functions

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
import httplib2
import lxml.etree
#TODO: try catch
try:
    from cStringIO import cStringIO as StringIO
except:
    from StringIO import StringIO

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


#TODO: This should thow an exception if variable not found!!
def drupal_settings_variable_json(filename, variable):
    command = ['php', 'json_settings.php', filename, variable];
    try:
        #db_url_data = subprocess.check_output(command) # only works in python 2.7+
        php_process = subprocess.Popen(command, stdout=subprocess.PIPE) # .communicate()[0]
        data = php_process.communicate()[0]

        # Replace with constants
        if php_process.returncode == 1:
            print 'Error: variable ' + variable + ' not found in ' + filename
        elif php_process.returncode:
            print 'Error: unkown error for ' + variable + ' in ' + filename
        else:
            variable_json = json.loads(data)
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
            print 'Error: no default db'
            exit()
    if isinstance(db_url, basestring):
        match = d6_db_url_re.match(db_url)
        return match.groupdict()
    else:
        #TODO: proper error
        print 'error invalid db_url'
        exit()
    #check if db_url is string?

def drupal7_db_settings(filename):
    databases = drupal_settings_variable_json(filename, 'databases')
    if isinstance(databases, dict):
        try:
            default_db = databases['default']['default']
            # set empty strings to None
            for key, value in default_db.items():
                if isinstance(value, basestring) and not len(value):
                    default_db[key] = None
            return {
                'type' : default_db.get('driver', 'mysql'),
                'username' : default_db.get('username', None), #might use anonymous connectoin, allow empty username
                'password' : default_db['password'],
                'hostname' : default_db.get('host', None),
                'port' : default_db.get('port', None),
                'database' : default_db['database']
             }
        except KeyError:
            print 'error: no default database'
    else:
        #TODO: proper error
        print 'error invalid databases variable'
        exit()


#TODO: replace version number with constant?
def sqlalchemy_connection_url(drupal_settings_filename, drupal_version):

    if drupal_version == 6:
        drupal_settings = drupal6_db_settings(drupal_settings_filename)
    elif drupal_version == 7:
        drupal_settings = drupal7_db_settings(drupal_settings_filename)
    else:
        #TODO: proper error
        print 'error invalid version'
        exit()

    if drupal_settings is None:
        print 'Error: no settings for ' + drupal_settings_filename
        return None

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
            connection_url.append(':' + drupal_settings['password'])

        connection_url.append('@')
        connection_url.append(drupal_settings['hostname'])

        if 'port' in drupal_settings and drupal_settings['port'] is not None:
            connection_url.append(':' + drupal_settings['port'])

        connection_url.append('/' + drupal_settings['database'])

        return ''.join(connection_url)

    else:
        #TODO: proper error
        print 'error invalid db type'
        exit()


@memoize
def regex_cache(regexp, flags=0):
    return re.compile(regexp, flags)


"""
 * Detects the version number of the current Drupal installation,
 * if any. Returns FALSE if there is no current Drupal installation,
 * or it is somehow broken.
 *
 * @return
 *   A string containing the version number of the current
 *   Drupal installation, if any. Otherwise, return FALSE.
"""

#TODO: optimize needed?
def dquery_extract_php_define_const(constant_name, filename):
    with open(filename, 'r', 1) as f:
        #TODO: allow double quote
        re_string = r"define\('{0}',\s*'(.+)'\)".format(constant_name)
        php_define_re = regex_cache(re_string)
        match = None
        # Just testing, will this evaluate lazily?
        #for first_match in (for match in (drupal_version.re.match(line) for line in f) if match is not None)
        #    return first_match.groupdict()
        for line in f:
            match = php_define_re.match(line)
            if match is not None:
                return match.group(1)



#Port of the drush function
#TODO: optimize needed?
@memoize
def dquery_drupal_version(drupal_root):
    drupal_version_re = regex_cache(r"(?P<major>\d+)\.(?P<minor>\d+)")
    # D7 stores VERSION in bootstrap.inc. D8 moved that to /core/includes.
    version_constant_filenames = [os.path.join(drupal_root, path)\
            for path in ['modules/system/system.module', 'includes/bootstrap.inc', 'core/includes/bootstrap.inc']]
    for filename in version_constant_filenames:
        # Drupal version is in top of file, so line buffring is probably most efficient
        if os.path.isfile(filename):
            result = dquery_extract_php_define_const('VERSION', filename)
            if result is not None:
                version =  dict(zip(['major', 'minor'], map(int, result.split('.'))))
                print 'version'
                print version
                return version
    print 'Error: Drupal version could not be detected'
    exit()



"""
 * Returns the Drupal major version number (6, 7, 8 ...)
"""
def dquery_drupal_major_version(drupal_root):
    version = dquery_drupal_version(drupal_root)
    return version['major']

@memoize
def dquery_drupal_core_compatibility(drupal_root):
    #TODO: have not actually checked these are the correct paths
    core_compatibility_constant_filenames = [os.path.join(drupal_root, path)\
            for path in ['modules/system/system.module', 'includes/bootstrap.inc', 'core/includes/bootstrap.inc']]
    for filename in core_compatibility_constant_filenames:
        # Drupal version is in top of file, so line buffring is probably most efficient
        if os.path.isfile(filename):
            result = dquery_extract_php_define_const('DRUPAL_CORE_COMPATIBILITY', filename)
            if result is not None:
                return result
    print 'Error: Drupal core compatibility could not be detected'
    exit()

#TODO return paths, absolute or relative??
@memoize
@pickle_memoize
def dquery_discover_sites(drupal_root, cache=True):
    sites_directory = os.path.join(drupal_root, 'sites')
    sites = []
    for f in [os.path.join(sites_directory, f) for f in os.listdir(sites_directory) if f != 'all']:
        if os.path.isdir(f) and not os.path.islink(f):
            if dquery_is_site_directory(f):
                sites.append(f)
    return frozenset(sites)

def dquery_is_site_directory(dirpath):
    return os.path.isfile(os.path.join(dirpath, 'settings.php'))

@memoize
@pickle_memoize
def dquery_discover_modules(path, cache=True):
    modules = []
    for root, dirnames, filenames in os.walk(path):
        for basename in fnmatch.filter(filenames, '*.module'):
            if os.path.isfile(os.path.join(root, basename[:-6] + 'info')):
                modules.append(os.path.join(root, basename))
            else:
                #replace with logging or debug option
                print "Missing info file for" + basename
    return modules

def dquery_modules_info(path, cache=True):
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
# TODO: put this in regex cache
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


info_format_key_re = re.compile('\]?\[')

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

def dquery_directories_discover_projects(drupal_root, directories, cache=True):
    directories_projects = {}
    for directory in directories:
        #TODO: remove this kludge, and scan for missing modules separately
        projects = dquery_directory_discover_projects(drupal_root, directory, cache=True)
        for project, module_files in projects.iteritems():
            if directory not in directories_projects:
                directories_projects[directory] = {}
            if project not in directories_projects[directory]:
                directories_projects[directory][project] = {}
            directories_projects[directory][project] = module_files
    return directories_projects

def dquery_module_namespace(module_filename):
    return os.path.basename(module_filename)[:-7]

#TODO: info kanns godtyckligt har, borde bara vara projekt -> projektnamn -> modulefiler
#TODO: ah, we set info here because we get it anyway, but because of memoizing it
# should not matter
#TODO: dquery_find_projects better name? dquery_scan_projects?
# dquery_extract_projects?
@memoize
@pickle_memoize
def dquery_directory_discover_projects(drupal_root, directory, cache=True):
    projects= {}
    #TODO: perhaps dquery_module_info is contrived, not to hard to just get info
    # when we need it?
    for module_file_abspath, module_info in dquery_modules_info(directory, cache=cache).iteritems():
        module_namespace = dquery_module_namespace(module_file_abspath)
        module_file_relpath = os.path.relpath(module_file_abspath, drupal_root)

        #TODO: should this hack be removed, or considered feature?
        if module_file_relpath.find('modules/') == 0:
            module_info['project'] = 'drupal'

        if 'project' in module_info:
            project = module_info['project']

            if not project in projects:
                projects[project] = []

            # check if project/module exist and warn??
            projects[project].append(module_file_abspath)
        else:
            #This is the only place we should warn about missing project?
            #modules_project_missing.append((module_namespace, filename))
            print 'no project: ' + module_file_relpath
    return projects

#TODO remove build from function name?
def dquery_project_mapping(drupal_root, cache=True):
    project_mapping = {}
    #TODO: remove drupal from function name?
    module_directories = dquery_drupal_module_directories(drupal_root, cache=cache)
    for module_dir in module_directories:
        projects = dquery_directory_discover_projects(drupal_root, directory, cache=cache)
        for project, module_files in projects.iteritems():
            for module_file in module_files:
                module_namespace = dquery_module_namespace(module_file)
                project_mapping[module_namespace] = project
    return project_mapping

#TODO: rename, according to what this does, do we even whant to do it?
#TODO: module_dir, inconsistent naming, directory?

#TODO: better name
def dquery_files_directory(files):
    directory = os.path.commonprefix(files)
    if not os.path.isdir(directory):
        directory = os.path.dirname(directory)
    #TODO: wrong to normalize here?
    return os.path.normpath(directory)

#TODO: if package all function in class, drupal_root can be provided as class property etc
#TODO: arg just one site?
@pickle_memoize
def dquery_build_module_usage_graph(drupal_root, site_directories = [], cache=True):

    module_directories = dquery_drupal_module_directories(drupal_root, include_sites=False, cache=cache)

    for site_dir in site_directories:
        module_directories.append(os.path.join(site_dir, 'modules'))
 
    directories_projects = dquery_directories_discover_projects(drupal_root, module_directories, cache=cache)

    project_mapping = dquery_project_mapping(drupal_root, cache=cache)

    usage_graph = {}

    for project in directories_projects:
        usage_graph[project] = {
            'sites' : set(),
            'modules' : {} # project_info #TODO really need this? Should just build usage
        }
        for module_directory, project_info in directories_projects[project].iteritems():
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

    drupal_major_version = dquery_drupal_major_version(drupal_root)
    for site in dquery_discover_sites(drupal_root, cache=cache):
        #TODO: throw exception instead of checking for none 
        connection_url = sqlalchemy_connection_url(os.path.join(site, 'settings.php'), drupal_major_version)
        if connection_url is None:
            continue 
        engine = sqlalchemy.create_engine(connection_url + '?charset=utf8&use_unicode=0', encoding='utf-8')

        try:
            connection = engine.connect()
            #TODO: new try
            result = connection.execute('SELECT name, filename, status, info FROM system WHERE status <> 0 AND type = "module"')
            for row in result:
                #TODO: replace with try catch indextjohejsan since 2xfaster
                info = {}

                #try:
                    #This is slow as fuck
                    #info = phpserialize.loads(row['info'], decode_strings=True)
                    #if row['name'] == 'uc_auriga':
                     #   print info
                      #  exit()
                #except ValueError as e:
                    #print 'value error'
                    #print row['filename']
                    #print row['info']
                    #print type(row['info'])
                    #exit()

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

#TODO: rename subdirectory
"""
def is_subdir_of(subdirectory, directory):
    #TODO: is there a less hackish way?
    return os.path.commonprefix([directory, subdirectory]) == directory and subdirectory.endswith(os.path.relpath(subdirectory, directory))
def is_subdir_of(subdirectory, directory):
    #directory = os.path.realpath(directory)
    #dirname = os.path.dirname(os.path.realpath(subdirectory))
    dirname = os.path.dirname(subdirectory)
    while dirname and len(dirname) >= len(directory):
        if dirname == directory:
            return True
        dirname = os.path.dirname(dirname)
    else:
        return False
"""
# recursive variant
def is_subdir_of(subdirectory, directory):
    subdirdir = os.path.dirname(subdirectory)
    #subdirdir != subdirectory checks if root , does not work on windows shares though (\\share\path)
    return subdirdir != subdirectory and\
        len(subdirdir) >= len(directory) and\
        (subdirdir == directory or is_subdir_of(subdirdir, directory))

#TODO: some command don't need drupal root, just scanning module directories for example, solve this
def module_directories_from_context(drupal_root, cache=True):
    cwd = os.getcwd()
    #cwd = os.path.realpath(cwd) #seems like realpath by default
    #Do we reside in the current drupal_root?
    module_directories = dquery_drupal_module_directories(drupal_root, cache=cache)
    if os.path.commonprefix([cwd, drupal_root]) == drupal_root:
        relpath = os.path.relpath(cwd, drupal_root)
        #Get all valid module subdirecties of cwd
        #TODO: benchmark
        module_directories = [directory for directory in module_directories if directory == cwd or is_subdir_of(directory, cwd)]
        if not len(module_directories):
            #Non standard module directory, still inside of drupal context, return cwd
            return [cwd]
        return module_directories
    else:
        #otherwise, default to all known module directories
        return module_directories

def dquery_drupal_update_info_data(project, compatibility):
    update_url = 'http://updates.drupal.org/release-history'
    url = '/'.join([update_url, project, compatibility])
    h = httplib2.Http('.cache')
    resp, content = h.request(url, 'GET')
    return content
    #TODO

# Compatibility feels a bit redundant, part of project?
# project_version to be replaced with general project entity?
# TODO: remove cache, just use for faster testing
@memoize
@pickle_memoize
def dquery_drupal_update_recommended_release(project, compatibility, cache=True):
    data = dquery_drupal_update_info_data(project, compatibility)
    f = StringIO(data)
    tree = lxml.etree.parse(f)
    error = tree.xpath('/error/text()')
    #Trow exceptins instead so we can finally .close
    if len(error):
        print 'Error: ' + error[0]
        f.close()
        return None

    project_status = tree.xpath('/project/project_status/text()')[0]
    #just hacking this together for now
    if project_status == 'unsupported':
        print 'Warning: project ' + project + ' is unsupported'
        f.close()
        return None

    #Check drupal logic for this
    recommended_major = tree.xpath('/project/recommended_major/text()')
    if len(recommended_major):
        major = recommended_major[0]
    else:
        default_major = tree.xpath('/project/default_major/text()')
        major = default_major[0]

    recommended_release = tree.xpath('/project/releases/release[version_major = $major][1]', major = major)[0]
    version = recommended_release.xpath('version/text()')[0]
    tag = recommended_release.xpath('tag/text()')[0]
    f.close()
    return {'version' : str(version), 'tag' : str(tag)}


#rename?
def dquery_module_element_version_info(module_file_abspath):
    info = dquery_module_info(module_file_abspath)
    module_element_info = {}
    if 'core' in info:
        module_element_info['core'] = info['core']
    if 'version' in info:
        module_element_info['version'] = info['version']
        version_info = dquery_parse_project_version(info['version'])
        # oh shit, this should be on project
        if version_info is not None:
            # Add "stable" as status if version-status not set?
            if not version_info['status'] is None:
                module_element_info['status'] = version_info['status']
            if not version_info['major'] is None:
                module_element_info['version-major'] = version_info['major']
            if not version_info['patch'] is None:
                module_element_info['version-patch'] = version_info['patch']
            #Good idea to set core if not set?
    return module_element_info

#TODO: module info etc
def dquery_module_element(parent, module_file_abspath):
    attributes = dquery_module_element_version_info(module_file_abspath)
    attributes['name'] = dquery_module_namespace(module_file_abspath)
    return lxml.etree.SubElement(
            parent,
            'module',
            **attributes)

# returns Core compabillity (or None), major and patch and development status
def dquery_parse_project_version(version):
    project_version_re = regex_cache(r"""
        (?:(?P<core>\d+\.\w+)-)?                #Core compability, this is sometimes part of version string
        (?P<major>\d+)\.(?P<patch>\w+)          #Major and patch version (patch version may be "x" for dev releases)
        (?:-(?P<status>.+))?                    #Development status, may be "dev","alpha" "rc-1" etc
    """, re.X)
    match = project_version_re.match(version)
    if match is None:
        print "Invalid project version string: " + version
    else:
        return match.groupdict()

#TODO: split into util.py and lib.py, util is the one beeing used, lib
# dependency for utils

# <project name="user" version="6.22" version-major="6" version-patch="22" mdhash="234234234234">
def dquery_multisite_xml_project(parent, **kwargs):
    #validation.. fuck it
    pass

def dquery_build_projects_xml(drupal_root, cache=True):
    pass


def dquery_format_site(format, drupal_root, site_abspath):
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

