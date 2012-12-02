#!/usr/bin/env python

#if sys.stdout.isatty(): + turn off pipe detection
# + colors
#TODO: python doc-strings format and inline tests for relevant functions
#TODO: split into lib and util and possibly more
import warnings
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
from dquery import settings as dquery_settings

#Exceptions

class DQueryException(Exception):
    pass

class DQueryMissingInfoFileError(DQueryException):
    pass

#Warnings

class DQueryWarning(UserWarning):
    pass

def dquery_get_project(module_namespace):
    return project_mapping[module_namespace]

def memoize(f, cache={}):
    def g(*args, **kwargs):
        key = ( f, tuple(args), frozenset(kwargs.items()) )
        if key not in cache:
            cache[key] = f(*args, **kwargs)
        return cache[key]
    return g
#TODO: We have one unresolved "problem" if cache=True in default arguemnt list,
#it will not be present in **kwargs (if not supplied in function call), find out
#how to handle this, right now only explicit use of cache=True works in function
#calls
def pickle_memoize(f):
    def g(*args, **kwargs):
        if not ('cache' in kwargs and kwargs['cache']):
            return f(*args, **kwargs)
        #TODO: things will get fucked up if fuction decorated aka is g?
        key = ( f.__name__, tuple(args), frozenset(kwargs.items()) )
        #script_dir = os.path.dirname(os.path.realpath(__file__))
        cache_file_abspath = os.path.join(dquery_settings.cache_dir_abspath, ''.join([str(key.__hash__()), '.', f.__name__]))
        if os.path.isfile(cache_file_abspath):
            with open(cache_file_abspath, 'r') as cache_file:
                result = pickle.load(cache_file)
        else:
            result = f(*args, **kwargs)
            try:
                with open(cache_file_abspath, 'w') as cache_file:
                    pickle.dump(result, cache_file)
            except IOError as e:
                if not os.path.isdir(
                        dquery_settings.cache_dir_abspath):
                    raise DQueryException(('You need to manually create DQuery\'s '
                        'cache directory {0!r} and ensure it has the appropriate '
                        'permissions. Run command with --no-cache to bypass '
                        'this error.').format(dquery_settings.cache_dir_abspath))
                else:
                    raise e
        return result
    return g

def dquery_clear_cache(pattern=None):
    fs = os.listdir(dquery_settings.cache_dir_abspath)

    if not pattern is None:
        file_regex = regex_cache(pattern)
        #fs = [f for f in fs if regex.match(f)]
        fs = filter(file_regex.match, fs)

    for f in fs:
        abspath = os.path.join(dquery_settings.cache_dir_abspath, f)
        try:
            if os.path.isfile(abspath):
                os.unlink(abspath)
        except Exception as e:
            print e

#TODO: This should thow an exception if variable not found!!
def drupal_settings_variable_json(filename, variable):
    command = ['dquery_php_var_json', filename, variable];
    try:
        #db_url_data = subprocess.check_output(command) # only works in python 2.7+
        php_process = subprocess.Popen(command, stdout=subprocess.PIPE) # .communicate()[0]
        data = php_process.communicate()[0]

        # Replace with constants
        if php_process.returncode == 1:
            message = 'variable {0!r} not found in {1!r}'
            raise DQueryException(
                message.format(variable, filename))
        elif php_process.returncode:
            message = 'unknown error extracting variable {0!r} from {1!r}'
            raise DQueryException(
                message.format(variable, filename))
        else:
            variable_json = json.loads(data, encoding='ascii')
            return variable_json;
    except subprocess.CalledProcessError as e:
        #TODO: do something
        raise e

d6_db_url_re = re.compile(r"^(?P<type>\w+?)://(?P<username>.+?)(?::(?P<password>.+?))?@(?P<hostname>.+?)(?::(?P<port>.+?))?/(?P<database>.+)$")

def drupal6_db_settings(filename):
    db_url = drupal_settings_variable_json(filename, 'db_url')
    if isinstance(db_url, dict):
        if 'default' in db_url:
            db_url = db_url['default']
        else:
            DQueryException('no default database in {0!r}'.format(filename))
    if isinstance(db_url, basestring):
        match = d6_db_url_re.match(db_url)
        return match.groupdict()
    else:
        #or just warn?
        raise DQueryException('invalid db_url in {0!r}'.format(filename))

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
            raise DQueryException('no default database in {0!r}'.format(filename))
    else:
        raise DQueryException('invalid databases variable in {0!r}'.format(filename))


#TODO: replace version number with constant?
def sqlalchemy_connection_url(drupal_settings_filename, drupal_version):
    if drupal_version == 6:
        drupal_settings = drupal6_db_settings(drupal_settings_filename)
    elif drupal_version == 7:
        drupal_settings = drupal7_db_settings(drupal_settings_filename)
    else:
        raise DQueryException(
            'invalid drupal version: {0!r}'.format(drupal_version))

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
        raise DQueryException(
            'invalid db type: {0!r} in {1!r}'.format(
                drupal_settings['type'], drupal_settings_filename))

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
                return version
    raise DQueryExcepetion('Drupal version could not be detected')

# Returns the Drupal major version number (6, 7, 8 ...)
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
    raise DQueryException('Drupal core compatibility could not be detected')

#TODO return paths, absolute or relative??
@memoize
@pickle_memoize
def dquery_sites_scan(drupal_root, cache=True):
    sites_directory = os.path.join(drupal_root, 'sites')
    sites = []
    for f in [os.path.join(sites_directory, f) for f in os.listdir(sites_directory) if f != 'all']:
        if os.path.isdir(f) and not os.path.islink(f):
            if dquery_is_site_directory(f):
                sites.append(f)
    return frozenset(sites)

def dquery_is_site_directory(dirpath):
    return os.path.isfile(os.path.join(dirpath, 'settings.php'))

#TODO: order of argument of other functions that takes extension_type should be
# consistent, extension_type first so easier to map with partial
def dquery_scan_directory_extensions(extension_type, abspath, **kwargs):
    if extension_type == 'module':
        return dquery_scan_directory_modules(abspath, **kwargs)
    elif extension_type == 'theme':
        return dquery_scan_directory_themes(abspath, **kwargs)
    else:
        raise DQueryException(
            'invalid extension type: {0!r}'.format(extension_type))

def dquery_scan_directory_modules(abspath, **kwargs):
    #We are a little bit less permissive module-name wise than drupal since I don't
    #know how to do unicode ranges in fnmatch.filter
    return dquery_scan_directory(
        abspath, '[a-zA-z_][a-zA-Z0-9_]*.module', **kwargs)

def dquery_scan_directory_themes(abspath, **kwargs):
    return dquery_scan_directory(
        abspath, '[a-zA-z_][a-zA-Z0-9_]*.info', **kwargs)


#'/^' . DRUPAL_PHP_FUNCTION_PATTERN . '\.module$/'
#TODO: implement min_depth!
#TODO: verify cache works as expected
def dquery_scan_directory(abspath, mask, min_depth=1, cache=True):
    files = []
    for root, dirnames, filenames in os.walk(abspath):
        for basename in fnmatch.filter(filenames, mask):
            files.append(os.path.join(root, basename))
    return files

#TODO!!
"""
def dquery_paths_reldepth(basepath, path):
    relpath = os.path.relpath(path, basepath)
    depth = 0
    while os.path.split(relpath)
"""

def dquery_modules_info(path, cache=True):
    modules = {}
    for module_filename in dquery_discover_modules(path, cache=cache):
        modules[module_filename] = dquery_module_info(module_filename)
    return modules


#TODO: correct inconsistent naming, filename, filepaths, path, abs_filepaths etc
def dquery_partition_by_project(files_abspaths, extension_type):
    projects_files = {}
    for file_abspath in files_abspaths:
        info = None
        try:
            info = dquery_project_info(file_abspath, extension_type)
            if 'project' in info and 'version' in info:
                project = info['project'] + '-' + info['version']
                if not project in projects_files:
                    projects_files[project] = []
                projects_files[project].append(file_abspath)
            else:
                message = '{0!r} has no project information and will ignored'
                warnings.warn(message.format(file_abspath), DQueryWarning)
        except DQueryException as e:
            warnings.warn(e.message, DQueryWarning)
    return projects_files

#TODO: good idea?
#TODO: utilize in xml.py?
def dquery_extension_directory(extension_type):
    if extension_type == 'module':
        return 'modules'
    elif extension_type == 'theme':
        return 'themes'
    else:
        raise DQueryException(
            'invalid extension type: {0!r}'.format(extension_type))

#TODO: fix order of argument, extension_type first
def dquery_project_info(filename, extension_type):
    if extension_type == 'module':
        return dquery_module_info(filename)
    elif extension_type == 'theme':
        return dquery_open_info_file(filename)
    else:
        raise DQueryException(
            'invalid extension type: {0!r}'.format(extension_type))

def dquery_module_info(module_filename):
    info_filename = ''.join([module_filename[:-6], 'info'])
    return dquery_open_info_file(info_filename)

def dquery_open_info_file(info_filename):
    try:
        with open(info_filename) as f:
            data = f.read()
            info_data = drupal_parse_info_format(data)
            return info_data
    except IOError:
        raise DQueryMissingInfoFileError(
            "Missing info file: {0!r}".\
            format(info_filename))

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

def dquery_module_namespace(module_filename):
    return os.path.basename(module_filename)[:-7]

def dquery_theme_namespace(theme_info_filename):
    return os.path.basename(theme_info_filename)[:-5]

#TODO: rename, according to what this does, do we even whant to do it?
#TODO: module_dir, inconsistent naming, directory?
#TODO: better name
def dquery_files_directory(files):
    directory = os.path.commonprefix(files)
    if not os.path.isdir(directory):
        directory = os.path.dirname(directory)
    #TODO: wrong to normalize here?
    return os.path.normpath(directory)

def dquery_drupal_system_directories(drupal_root, directory, include_sites=True, cache=True):
    module_directories = [] 
    module_directories.append(os.path.join(drupal_root, directory))
    module_directories.append(os.path.join(drupal_root, 'sites/all', directory))
    #TODO: profiles
    if include_sites:
        for site in dquery_sites_scan(drupal_root, cache=cache):
            module_directories.append(os.path.join(site, directory))

    #TODO: filter file exists?
    return filter(os.path.isdir, module_directories)

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
    module_directories = dquery_drupal_system_directories(
            drupal_root,
            'modules',
            cache=cache)
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
    h = httplib2.Http(dquery_settings.cache_dir_abspath)
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
    version_data = None
    #with context manager possible for f?
    try:
        if len(error):
            message = 'error requesting update information for {0!r}: {1!r}'
            raise DQueryException(message.format(project, error[0]))
        project_status = tree.xpath('/project/project_status/text()')[0]
        #just hacking this together for now
        if project_status == 'unsupported':
            message = 'project {0!r} is unsupported'
            raise DQueryException(message.format(project))
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
        version_data = {'version' : str(version), 'tag' : str(tag)}
    except DQueryException as e:
        warnings.warn(e.message, DQueryWarning)
    finally:
        f.close()
    return version_data

# returns Core compabillity (or None), major and patch and development status
def dquery_parse_project_version(version):
    project_version_re = regex_cache(r"""
        (?:(?P<core>\d+\.\w+)-)?                #Core compability, this is sometimes part of version string
        (?P<major>\d+)\.(?P<patch>\w+)          #Major and patch version (patch version may be "x" for dev releases)
        (?:-(?P<status>.+))?                    #Development status, may be "dev","alpha" "rc-1" etc
    """, re.X)
    match = project_version_re.match(version)
    if match is None:
        warnings.warn(
            "invalid project version string: {0!r}".format(version),
            DQueryWarning)
    else:
        return match.groupdict()

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

