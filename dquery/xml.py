from dquery.lib import *
import lxml.etree
from cli.profiler import Profiler

def dquery_build_multisite_xml(drupal_root, pretty_print=True, cache=True):
    xml_etree = dquery_build_multisite_xml_etree(drupal_root, cache)
    return lxml.etree.tostring(xml_etree, pretty_print=pretty_print)

#TODO: how handle cache here?
#_Element can't be pickled or some reason, we cache as xml instead
#profiler = Profiler(stdout=sys.stdout)
#@profiler.deterministic
def dquery_build_multisite_xml_etree(drupal_root, cache=True):
    #TODO: get function name etc
    script_dir = os.path.dirname(os.path.realpath(__file__))
    cache_filename = os.path.join(
        script_dir,
        'cache',
        ''.join([str(drupal_root.__hash__()), '.dquery_build_multisite_xml_etree.xml']))

    #TODO: error handling
    if cache and os.path.isfile(cache_filename):
        with open(cache_filename, 'r') as cache_file:
            etree_from_file = lxml.etree.parse(cache_file)
            return etree_from_file.getroot()

    root = lxml.etree.Element('drupal-multisite', version="fluid")

    dquery_build_multisite_xml_module_projects(root, drupal_root, cache=cache)
    dquery_build_multisite_xml_theme_projects(root, drupal_root, cache=cache)

    with open(cache_filename, 'w') as cache_file:
        multisite_etree = lxml.etree.ElementTree(root)
        multisite_etree.write(cache_file)

    return root


def dquery_build_multisite_xml_theme_projects(etree_root, drupal_root, cache=True):

    theme_directories = dquery_drupal_system_directories(
            drupal_root,
            'themes',
            cache=cache)

    theme_files = []

    for directory in theme_directories:
        etree_context = etree_root

        directory_relpath = os.path.relpath(directory, drupal_root)
        etree_context = dquery_build_multisite_xml_directories(
            etree_context, directory_relpath, drupal_root, drupal_root)

        theme_files = dquery_scan_directory_themes(
            directory, cache=cache)

        projects_theme_files = dquery_partition_by_project(
            theme_files, 'theme')

        for project, theme_files in projects_theme_files.items():

            project_etree_context = etree_context

            project_directory = dquery_files_directory(theme_files)
            if project_directory != directory:
                directory_relpath = os.path.relpath(project_directory, directory)
                project_etree_context = dquery_build_multisite_xml_directories(
                    project_etree_context, directory_relpath, directory, drupal_root)

            theme_files_relpaths = [os.path.relpath(theme_file, project_directory) for theme_file in theme_files]

            themes_dir_tree = dquery_directory_tree(theme_files_relpaths)

            dquery_build_multisite_xml_etree_theme_project(
                    theme_files[0], project_etree_context, themes_dir_tree, project_directory, drupal_root)


def dquery_build_multisite_xml_etree_theme_project(
    theme_file_abspath, etree_context, directory_tree, current_dir, drupal_root):

    etree_context = dquery_theme_project_element(
        etree_context, theme_file_abspath)
    dquery_build_multisite_xml_etree_theme_project_themes(
        etree_context, directory_tree, current_dir, drupal_root)

def dquery_theme_project_element(parent, theme_file_abspath):
    attributes = {}
    attributes = dquery_theme_element_version_info(theme_file_abspath)
    return lxml.etree.SubElement(parent, 'project', **attributes)

def dquery_build_multisite_xml_module_projects(etree_root, drupal_root, cache=True):

    module_directories = dquery_drupal_system_directories(
            drupal_root,
            'modules',
            cache=cache)

    module_files = []

    for directory in module_directories:

        etree_context = etree_root

        directory_relpath = os.path.relpath(directory, drupal_root)
        etree_context = dquery_build_multisite_xml_directories(
            etree_context, directory_relpath, drupal_root, drupal_root)

        module_files = dquery_scan_directory_modules(
            directory, cache=cache)

        projects_module_files = dquery_partition_by_project(
            module_files, 'module')

        for project, module_files in projects_module_files.items():

            project_etree_context = etree_context

            project_directory = dquery_files_directory(module_files)
            if project_directory != directory:
                directory_relpath = os.path.relpath(project_directory, directory)
                project_etree_context = dquery_build_multisite_xml_directories(
                    project_etree_context, directory_relpath, directory, drupal_root)

            module_files_relpaths = [os.path.relpath(module_file, project_directory) for module_file in module_files]
            modules_dir_tree = dquery_directory_tree(module_files_relpaths)

            dquery_build_multisite_xml_etree_module_project(
                    module_files[0], project_etree_context, modules_dir_tree, project_directory, drupal_root)

def dquery_build_multisite_xml_directories(
        etree_context, directory_relpath, base_abspath, drupal_root):
    #TODO: or perform relpath check here?
    #directory_relpath = os.path.relpath(directory_abspath, drupal_root)
    directory_components = directory_relpath.split(os.sep)

    for i in range(1, len(directory_components) + 1):
        dir_abspath = os.path.join(
            base_abspath,
            os.sep.join(directory_components[0:i]))
        etree_context = dquery_build_multisite_xml_directory(
            etree_context,
            dir_abspath,
            drupal_root)
    return etree_context


def dquery_build_multisite_xml_directory(etree_context, directory_abspath, drupal_root):
    """
    for directory_elem in lxml.etree.ElementDepthFirstIterator(
            etree_context, tag='directory'):
    """

    for directory_elem in etree_context.iterchildren(tag='directory'):
        if directory_elem.get('abspath') == directory_abspath:
            etree_context = directory_elem
            break
    else:
        etree_context = dquery_directory_element(
            etree_context, directory_abspath, drupal_root)

    return etree_context

def dquery_build_multisite_xml_etree_module_project(
        module_file_abspath, etree_context, directory_tree, current_dir, drupal_root):
    etree_context = dquery_module_project_element(
        etree_context, module_file_abspath)
    dquery_build_multisite_xml_etree_module_project_modules(
        etree_context, directory_tree, current_dir, drupal_root)


def dquery_build_multisite_xml_etree_module_project_modules(
        etree_context, directory_tree, current_dir, drupal_root):

    directory_module_files, directories = directory_tree

    if directory_module_files:
        for module_file in directory_module_files:
            module_file_abspath = os.path.join(current_dir, module_file)
            dquery_module_element(etree_context, module_file_abspath)
    for directory_name, directory_tree in directories.items():
        directory_abspath = os.path.join(drupal_root, current_dir, directory_name)
        modules_etree_context = dquery_build_multisite_xml_directory(
                etree_context,
                directory_abspath,
                drupal_root)
        dquery_build_multisite_xml_etree_module_project_modules(
                modules_etree_context,
                directory_tree,
                directory_abspath,
                drupal_root)

def dquery_build_multisite_xml_etree_theme_project_themes(
        etree_context, directory_tree, current_dir, drupal_root):

    directory_theme_files, directories = directory_tree

    if directory_theme_files:
        for theme_file in directory_theme_files:
            theme_file_abspath = os.path.join(current_dir, theme_file)
            dquery_theme_element(etree_context, theme_file_abspath)
    for directory_name, directory_tree in directories.items():
        directory_abspath = os.path.join(drupal_root, current_dir, directory_name)
        themes_etree_context = dquery_build_multisite_xml_directory(
                etree_context,
                directory_abspath,
                drupal_root)
        dquery_build_multisite_xml_etree_theme_project_themes(
                themes_etree_context,
                directory_tree,
                directory_abspath,
                drupal_root)


#what kind of perverted semi recursion is this
#filepaths MUST be filepahts, no empty dirs allowed!
def dquery_directory_tree(filepaths):
    directory_tree = ([], {})
    for filepath in filepaths:
        _dquery_directory_tree(filepath.split(os.sep), directory_tree)
    return directory_tree

#here filepaths are split by filepath separator
def _dquery_directory_tree(split_filepath, directory_tree):
    #for split_filepath in split_filepaths:
        head, tail = split_filepath[0], split_filepath[1:]
        files, directories = directory_tree
        if not tail:
            #head is filename
            files.append(head)
        else:
            if not head in directories:
                directories[head] = ([], {})
            #_dquery_directory_tree(tail, directory_tree['dirs'][head])
            _dquery_directory_tree(tail, directories[head])

def dquery_directory_element(parent, abspath, drupal_root):
    return lxml.etree.SubElement(
        parent,
        'directory',
        name=os.path.basename(abspath),
        abspath=abspath,
        relpath=os.path.relpath(abspath, drupal_root))

#rename?
def dquery_module_element_version_info(module_file_abspath):
    info = dquery_project_info(module_file_abspath, 'module')
    module_element_info = {}
    module_element_info['name'] = info['project']
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

#TODO: implement properly, what kind of info, all?
def dquery_theme_element_version_info(theme_file_abspath):
    info = dquery_project_info(theme_file_abspath, 'theme')
    theme_element_info = {}
    theme_element_info['name'] = info['project']
    if 'core' in info:
        theme_element_info['core'] = info['core']
    if 'version' in info:
        theme_element_info['version'] = info['version']
        version_info = dquery_parse_project_version(info['version'])
        # oh shit, this should be on project
        if version_info is not None:
            # Add "stable" as status if version-status not set?
            if not version_info['status'] is None:
                theme_element_info['status'] = version_info['status']
            if not version_info['major'] is None:
                theme_element_info['version-major'] = version_info['major']
            if not version_info['patch'] is None:
                theme_element_info['version-patch'] = version_info['patch']
            #Good idea to set core if not set?
    return theme_element_info


def dquery_module_element(parent, module_file_abspath):
    attributes = dquery_module_element_version_info(module_file_abspath)
    attributes['name'] = dquery_module_namespace(module_file_abspath)
    return lxml.etree.SubElement(
            parent,
            'module',
            **attributes)

def dquery_theme_element(parent, theme_file_abspath):
    attributes = dquery_theme_element_version_info(theme_file_abspath)
    attributes['name'] = dquery_theme_namespace(theme_file_abspath)
    return lxml.etree.SubElement(
            parent,
            'theme',
            **attributes)

def dquery_module_project_element(parent, module_file_abspath):
    attributes = {}
    attributes = dquery_module_element_version_info(module_file_abspath)
    return lxml.etree.SubElement(parent, 'project', **attributes)
