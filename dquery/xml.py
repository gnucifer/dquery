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

    module_directories = dquery_drupal_module_directories(drupal_root, cache=cache)
    directories_projects = dquery_directories_discover_projects(drupal_root, module_directories, cache=cache)

    for directory, projects in directories_projects.iteritems():
        directory_element = dquery_directory_element(root, directory, drupal_root)

        for project, module_files in projects.iteritems():
            """
            project_directory = dquery_files_directory(module_files)
            project_directory_element = dquery_directory_element(
                directory_element,
                project_directory,
                drupal_root)
            """
            module_files_relpaths = [os.path.relpath(module_file, directory) for module_file in module_files]
            directory_tree = dquery_directory_tree(module_files_relpaths)

            dquery_build_multisite_xml_project(
                directory_element,
                project,
                module_files,
                directory,
                directory_tree,
                drupal_root)
            """
            project_element = dquery_project_element(project_directory_element,
                    project, module_files)
            dquery_directory_tree(module_files_relpaths)

            for module_file in module_files:
                dquery_module_element(project_element, module_file)
            """
    with open(cache_filename, 'w') as cache_file:
        multisite_etree = lxml.etree.ElementTree(root)
        multisite_etree.write(cache_file)

    return root

def dquery_build_multisite_xml_project(parent, name, module_files, directory_root, directory_tree, drupal_root):
    #module_files_relpaths = [os.path.relpath(module_file, directory_root) for module_file in module_files]
    #directory_tree = dquery_directory_tree(module_files_relpaths)
    directory_module_files, directories = directory_tree
    if directory_module_files:
        #module files???
        project_element = dquery_project_element(parent, name, module_files)
        #or is this just silly, could build this structure though os.walk?
        dquery_build_multisite_xml_project_modules(project_element, directory_root, directory_tree, drupal_root)
    else:
        for directory_name, directory_tree in directories.items():
            directory_abspath = os.path.join(directory_root, directory_name)
            directory_element = dquery_directory_element(
                    parent,
                    directory_abspath,
                    drupal_root)
            dquery_build_multisite_xml_project(
                    directory_element,
                    name,
                    module_files,
                    directory_abspath,
                    directory_tree,
                    drupal_root)
    #print module_file
    #print directories
    #exit()
    #print directory_root
    #project_element = dquery_project_element(parent, name, module_files)
    #or is this just silly, could build this structure though os.walk?
    #dquery_build_multisite_xml_project_modules(project_element, directory_root, directory_tree, drupal_root)

#TODO: Rename directory_root to current_directory?
def dquery_build_multisite_xml_project_modules(parent, directory_root, directory_tree, drupal_root):
    module_files, directories = directory_tree

    for module_file in module_files:
        module_file_abspath = os.path.join(directory_root, module_file)
        dquery_module_element(parent, module_file_abspath)

    for directory_name, directory_tree in directories.iteritems():
        directory_abspath = os.path.join(directory_root, directory_name)
        directory_element = dquery_directory_element(
                parent,
                directory_abspath,
                drupal_root)
        dquery_build_multisite_xml_project_modules(
                directory_element,
                directory_abspath,
                directory_tree,
                drupal_root)

#is relative shit
#what kind of perverted semi recursion is this
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
            #if not 'files' in directory_tree:
                #directory_tree['files'] = []
            #directory_tree['files'].append(head)
            files.append(head)
        else:
            #if not 'dirs' in directory_tree:
                #directory_tree['dirs'] = {}
            #if not head in directories['dirs']:
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

def dquery_project_element(parent, name, module_files):
    #Loop though module files and grap the first version info that makes senes
    #Seems there is no other sane way of extracting project info?
    attributes = {}
    for module_file_abspath in module_files:
        attributes = dquery_module_element_version_info(module_file_abspath)
        if(len(attributes)):
            break
    attributes['name'] = name
    return lxml.etree.SubElement(parent, 'project', **attributes)


