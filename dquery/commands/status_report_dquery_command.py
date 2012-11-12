#TODO: Try placing this in __init__
from dquery.application import dQueryCommand
from dquery.lib import *
import warnings

@dQueryCommand(
    'status-report',
    help='list potential problems with a drupal installation and attempt to suggest solutions')
def dquery_status_report_command(args):
    # Scan for info-files with missing project information
    report = {}
    report['missing info files'] = {}

    module_files = extensions_missing_project_info(args.drupal_root, 'module', cache=args.use_cache)
    report['missing info files']['modules'] = module_files

    theme_files = extensions_missing_project_info(args.drupal_root, 'theme', cache=args.use_cache)
    report['missing info files']['themes'] = theme_files

    return report

    # Scan for sites with broken database connections (or other problems like
    # invalid db-strings)

    #TODO: more to come

def extensions_missing_project_info(drupal_root, extension_type, cache=True):
    directory = dquery_extension_directory(extension_type)
    extension_directories = dquery_drupal_system_directories(
            drupal_root,
            directory,
            cache=cache)
    extension_files = []
    missing_project_info = []
    #Could instead map with partial to save some indents?
    for directory in extension_directories:
        extension_files = dquery_scan_directory_extensions(
            extension_type, directory, cache=cache)
        for file_abspath in extension_files:
            try:
                info = dquery_project_info(file_abspath, extension_type)
                if not 'project' in info:
                    missing_project_info.append(file_abspath)
            except DQueryException as e:
                #TODO: hmm?
                warnings.warn(e.message, DQueryWarning)
    return missing_project_info
